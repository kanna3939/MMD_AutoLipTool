# MS27-B2 Implementation Plan

## 1. 文書情報

- 対象: MS27-B2 `1.0.0`版数更新・表示整合・Windows version resource反映
- 作成日: 2026-09-13
- リポジトリ: `D:\Kanna_Works\MMD_AppWork\MMD_AutoLipTool-dev\MMD_AutoLipTool_Antigravity`
- 計画作成時ブランチ: `feature/MS27-implementation`
- 計画作成時HEAD: `9e9cc64 Record MS27-B1 baseline and OS gate`
- 開始時working tree: clean。現在ブランチのupstreamは未設定。remoteの再照会・同期操作は実施していない。
- 前提: MS26 CloseOut Aを継承。MS27-B1は最新実施記録でPass。
- B2実装開始時HEAD: `153b213 Document MS27-B2 implementation plan`
- B2実装開始時working tree: clean。実装後の変更は本書の§15.4へ記録する。
- 本書の状態: **B2実装済み・直接検証Pass。最終EXE、onefile、ZIP、GUI、実MMD、licenseは後続Blockの未確認事項として継承。**
- 今回の作成担当: 指定された計画作成担当サブエージェント。メインエージェントが成果物の採否・最終検証を担当する。
- 計画作成時の変更許可: 本書1ファイルのみ。B2実装時の変更は§7.1の範囲に限定した。

正本文書は[MS27 Block Breakdown](MS27_Block_Breakdown.md) §7.1 / §8.1 G-VERSION / §9 B2 / §10〜§12と、[MS27-B1 Implementation Plan](MS27-B1_Implementation_Plan.md) §8.1 / §15.4 / §16 / §17.1である。Block Breakdown先頭の「B1〜B6未実施」は作成時の状態であり、B1の最新Passを上書きしない。Indexに残る旧ブランチ表記や過去のMS26 Pendingも、現在のGitと最終受入記録より優先しない。

## 2. 背景

### 2.1 現行資料・実装との対応

| 確認対象 | 計画作成時の事実 | B2で扱う差分・境界 |
| --- | --- | --- |
| [現行Index](../MS20_and_Beyond_Index.md) §2、[Roadmap](../MS20_and_Beyond_Roadmap.md) §14 | MS26の最終受入はCloseOut A。MS27はbuild・配布・readiness工程 | 機能受入と配布検証を分離する。全体routing同期はB6へ渡す |
| B1 §15.4 / §16 / §17.1 | Windows 11 Pro、Version `10.0.26200`、Build `26200`、64bitを確認しB1 Pass | B2でOS確認を再実行する必須条件を追加しない |
| `pyproject.toml` `[project]` | nameは`mmd-autolip-tool`、versionは`0.4.0.0` | versionのみ`1.0.0`へ更新 |
| `src/app_version.py` | installed metadataを先に採用し、不在時にTOMLへfallback。既定TOML探索はmoduleの親階層3候補 | アプリ自身のTOMLとの不一致を解消し、選択対象を実行中アプリのresourceへ限定 |
| 現行venvのproject metadata | メインからの実照会結果として`mmd-autolip-tool==0.4.0.0`を引き継ぐ | B2実装開始時の実値も記録。TOML更新だけではsource解決値の一致を保証できない |
| `src/resource_utils.py` | `get_resource_path()`は通常時に同moduleのrepo root、PyInstaller時に`sys._MEIPASS`を基準とする | 既存のresource配置契約を利用し、別の汎用探索器を追加しない |
| `src/gui_wx/app.py` `OnInit()` | スプラッシュは`format_app_version_display(resolve_app_version())`を描画 | この呼出しと`Ver. <version>`形式を静的照合。GUI変更は予定しない |
| `tests/test_app_version.py` | 6つの既存test。project値の期待値は`0.4.0.0`。独立mock・表示例は`0.3.8.0` | project期待値と、意図的に変更する優先関係のtest前提を限定更新 |
| `README.md` | 冒頭は`Ver. 0.4.0.0`とMS17 closeout注記 | 現行版と到達状態を同期。過去のMS17記録は保持 |
| `readme_mmdautolip.txt` | 冒頭に正確な現行版数がなく、§12に`v0.4.x` / `v0.3.x 以前`の履歴 | 現行`1.0.0`と今回の変更を追記。旧履歴を置換しない |
| `docs/Release_Package_Manifest.md` §3 / §6 | 実行用ZIP例は2箇所とも`MMD_AutoLipTool_v0.4.x_Windows_onefile.zip` | 今回の正確な候補名へ同期。公開実績やlicense適合を追記しない |
| `MMD_AutoLipTool.spec` | `pyproject.toml -> .`をdatasへ収集。`EXE(name="MMD_AutoLipTool")`。version指定なし | 既存TOML収集を保持し、Windows version resourceを`EXE(version=...)`へ接続 |
| `build.ps1` | specを入力にPyInstallerを実行。Cleanはcwd相対のbuild / dist / exeを削除する | B2では変更・実行しない。隔離build実行はB4 |
| `tests/conftest.py` | `src`と`tests`をimport pathへ追加するだけ | GUIをimportしない直接testを選択可能 |

B1が取得したPython `3.14.3` / PyInstaller `6.19.0` / hooks `2026.3`は引継ぎ証拠として扱う。今回、依存を再インストールしたり全依存を再調査したりしていない。Python 3.11 / 3.12互換性と最終onefileは未検証のままである。

### 2.2 Windows resource方式の根拠

PyInstaller 6.19.0の[Windows version data説明](https://pyinstaller.org/en/v6.19.0/usage.html#capturing-windows-version-data)では、UTF-8のversion textからresourceを埋め込み、固定数値は4要素tupleで表す。Microsoftの[VERSIONINFO仕様](https://learn.microsoft.com/en-us/windows/win32/menurc/versioninfo-resource)は、固定数値と`StringFileInfo`の文字列項目を区別している。正式版数の3要素表記を維持するため、本書では文字列を`1.0.0`、内部数値を`(1, 0, 0, 0)`へ対応付ける。

現行venvのPyInstallerソースもread-onlyで確認した。

- `PyInstaller/building/api.py`: `EXE`のversion入力がpathの場合、`load_version_info_from_text_file()`で読み、build時にEXEへ反映する。
- `PyInstaller/utils/win32/versioninfo.py`: UTF-8等をdecodeし、`VSVersionInfo`表現を読み込むloaderと、`toRaw()` / `fromRaw()`がある。
- loaderはPython式を評価するため、入力をレビュー済みの固定リポジトリファイルに限定する。ユーザー素材・外部EXEからの抽出や任意入力の評価を導入しない。

これは方式の静的根拠であり、resource入力の作成・loader実行・build成功の証拠ではない。

## 3. 目的

1. ユーザー決定の`1.0.0`を、project宣言、source解決値、表示文字列、利用者文書、ZIP命名へ一致させる。
2. 現行venvの旧installed metadataが新しいsource版数を隠す問題を、版数解決の限定変更と直接testで解消する。
3. Windows FileVersion / ProductVersionの入力resourceとspec接続を実装可能な形で固定し、B4へ最終EXE検証を渡す。
4. B2の実装・直接検証と、未実施のGUI / onefile / ZIP確認を区別して記録する。

## 4. In Scope

以下はB2実装時の範囲である。

- `pyproject.toml`のproject versionを厳密に`1.0.0`へ変更する。
- `src/app_version.py`のアプリ自身のresource選択、installed metadataとの不一致処理、欠落時のfallbackを限定変更する。
- `tests/test_app_version.py`の現在値期待と優先関係のtestを更新し、旧metadata・source / frozen配置・失敗時挙動を直接検証する。
- Windows version入力`MMD_AutoLipTool.version.txt`を新規作成し、specの`EXE(version=...)`へ接続する。
- resourceの値とシリアライズを検証する直接testを追加する。PyInstaller本体のbuildは呼び出さない。
- README、配布readme、package manifestの現行版表記とZIP命名を同期し、履歴・fixture・別versionを分類する。
- 実装内容、直接test、source解決値、resource入力、対象差分、Hold・未確認事項を本書の実施欄へ記録する。

## 5. Out of Scope

- onefile build、SmokeLaunch、最終EXEのresource取得、EXE書換え、ZIP作成・展開、GUI / 実MMD操作
- repo rootまたは隔離先でのbuild / dist / 既存EXEの削除・clean
- dependency / toolchain更新、project再インストール、venv metadataの直接編集、wheel / sdist作成
- `requirements.txt`、依存値、`requires-python`、setuptoolsのpackage発見・namespace全体の修復
- runtime JSON / INI、schema、fingerprint、Whisper manifest version、モデル・音声・VMD契約の変更
- `presets.json`、`profiles.json`、`MMD_AutoLipTool.ini`の直接読込・編集・コピー・fixture化・stage
- FFmpeg / DLL差し替え、license原本作成・採否、Qt / PySide6復活、無関係なGUI / pipeline改修
- MS26再受入、B2-R05の原因確定・無害化宣言、PMX hash取得の新しい必須化
- full pytest、compileall、GUI起動testの一律実行。本書の直接検証で不足が見つかった場合は影響と追加範囲を先に特定する
- stage、commit、ブランチ変更、push、merge、tag、release、公開、追加サブエージェント起動

今回の計画作成では、In Scopeに列挙した実装・testも実施しない。

## 6. 前提条件

### 6.1 固定されたversion表

| 対象 | B2で反映する値 | 判定担当 |
| --- | --- | --- |
| `project.version` | `1.0.0` | B2 |
| アプリ自身のsource / 模擬frozenでの解決値 | `1.0.0` | B2。実frozenはB4 / B5 |
| 表示文字列 | `Ver. 1.0.0` | B2の関数出力。実画面はB5 |
| README / 配布readmeの現行版 | `1.0.0` | B2 |
| EXE名 / resourceのOriginalFilename | `MMD_AutoLipTool.exe` | B2入力、B4実物 |
| ZIP候補名 | `MMD_AutoLipTool_v1.0.0_Windows_onefile.zip` | B2命名、B5実物 |
| Windows StringFileInfo.FileVersion | `1.0.0` | B2入力、B4最終EXE |
| Windows StringFileInfo.ProductVersion | `1.0.0` | B2入力、B4最終EXE |
| Windows FixedFileInfo.filevers / prodvers | 両方`(1, 0, 0, 0)` | B2入力、B4最終EXE |

4番目の`0`はWindowsの固定数値表現に必要な補完であり、正式版数を`1.0.0.0`へ変更する意味ではない。表示・文書・文字列resourceに4要素表記、`rc`、日付、commit suffixを付けない。Windowsの表示手段がどのfieldを採用するかは最終EXEでB4が確認し、3要素文字列の不一致を数値の一致だけで合格にしない。

### 6.2 B2実装開始条件

- 別途B2実装依頼があり、live branch / HEAD / working treeを1コマンドずつ確認して対象差分を固定する。
- B1 §17.1のPassと§16のhandoffを参照する。B1未確認表の古い中間記述だけでPassを取り消さない。
- 既存の未コミット変更があれば所有範囲を分類し、無関係な変更を保護する。本計画のcommitを開始条件にはしない。
- `1.0.0`とFileVersion / ProductVersionは決定済みとして扱い、再質問しない。
- current metadata、resource配置、呼出し元に今回の調査以降の変更があれば、§8の判断ゲートで対処範囲を再評価する。

## 7. 対象ファイル

### 7.1 B2実装時の変更対象

| 区分 | ファイル | 変更内容 |
| --- | --- | --- |
| 主変更 | `pyproject.toml` | `[project].version`だけを更新 |
| 主変更 | `src/app_version.py` | resource候補、project identity確認、不一致時の版数選択 |
| 主変更・新規候補 | `MMD_AutoLipTool.version.txt` | UTF-8のWindows version入力。計画時点では未作成 |
| 配布定義 | `MMD_AutoLipTool.spec` | `EXE(version=...)`へ上記入力のpathを追加 |
| 直接test | `tests/test_app_version.py` | 既存6観点を保持・再配置し、不一致・配置・失敗の回帰を追加 |
| 直接test・新規候補 | `tests/test_ms27_b2_windows_version_resource.py` | 実loaderによる入力値とメモリ上のround-trip、projectとの対応。計画時点では未作成 |
| 利用者文書 | `README.md` | 冒頭版数・現在状態、version入力の役割を最小限同期 |
| 利用者文書 | `readme_mmdautolip.txt` | 現行版数と`v1.0.0`項目を追加し旧履歴を保持 |
| 配布文書 | `docs/Release_Package_Manifest.md` | §3 / §6の正確なZIP候補名、version入力の配布境界 |
| 実施記録 | 本書 | 根拠、変更対象、test / source出力、入力hash、判定、handoff |

### 7.2 関連確認のみ・変更対象外

- `src/gui_wx/app.py`: スプラッシュの呼出し元確認のみ。wx.Appをimport・起動して確認しない。
- `src/resource_utils.py`: source / frozenの既存path契約を利用する。共通resource helper自体を変更しない。
- `build.ps1`: 既存のspec呼出しと固定EXE名を確認する。versionの別入力や生成処理を加えない。
- `tests/conftest.py`、既存startup test: importと影響範囲の確認のみ。runtime生成を伴うsuiteへ自動拡大しない。
- `LICENSE`、`NOTICE`、`THIRD_PARTY_LICENSES.md`、`FFmpeg/bin/`、`requirements.txt`: B1 / B3 / B4の責務を維持し、B2では変更しない。
- MS27 Block Breakdown、B1 plan、Index / Roadmap、`docs/Version_Control.md`、`docs/repo_milestone.md`: 参照・handoff対象。全体状態同期はB6へ渡す。履歴の一括改版を行わない。
- `.venv` / `*.dist-info` / `*.egg-info`: 実値の確認対象に限る。直接編集・再生成を採用しない。

今回の変更は本書のみであり、上表の新規resource・testは存在確認済みファイルとして扱わない。

## 8. 実装方針

### 8.1 版数解決: アプリ自身のresourceとinstalled metadataを照合する

採用方針は、**既存のinstalled metadata照会を維持し、実行中のsource / bundleに対応する有効なproject宣言がある場合、その宣言を版数の正本とする**ことである。旧metadataとの不一致時にだけ値の選択結果が変わる。現在のsourceを表示するためにvenvを更新する必要をなくす。

現在の関数へ次の限定変更を行う。

1. `_candidate_pyproject_paths(explicit_path)`の明示path優先・単独候補契約を保持する。
2. 既定pathは既存`get_resource_path("pyproject.toml")`が返す1箇所へ限定する。sourceはrepo root、frozenは`_MEIPASS`直下である。既存specの`pyproject.toml -> .`と対応する。CWD、EXE隣接の外部TOML、任意の祖先TOMLを追加探索しない。
3. `resolve_pyproject_version()`の暗黙pathでは`[project].name == "mmd-autolip-tool"`を確認し、非空文字列versionだけを採用する。明示pathを渡した既存の汎用読取契約は保持し、project.nameを必須としない。
4. `resolve_app_version()`ではinstalled metadataを照会した後、上記のアプリ自身のproject versionを確認する。両者が一致すればその値、不一致で有効なproject値があればproject値、project値が得られなければinstalled値、どちらもなければ`None`を返す。
5. `format_app_version_display()`と引数・戻り値型を維持する。runtimeに`1.0.0`を固定returnする処理、版数文字列の切り詰め・suffix除去を加えない。

resource基準の採用は、本repoが既に使う`src/resource_utils.py`と、PyInstallerの[run-time resource配置](https://pyinstaller.org/en/v6.19.0/runtime-information.html)に基づく。実frozenでの配置・import成立はB4 / B5へ残す。

| installed値 | 有効なアプリ自身のproject値 | 期待する解決値 | 意味 |
| --- | --- | --- | --- |
| `0.4.0.0` | `1.0.0` | `1.0.0` | 現在の旧metadata問題を解消 |
| `1.0.0` | `1.0.0` | `1.0.0` | 一致時の通常解決 |
| 不在 | `1.0.0` | `1.0.0` | metadataなしsource / bundleを維持 |
| `0.3.8.0` | 不在・読取不能・無効 | `0.3.8.0` | metadataのみの解決を維持 |
| 不在 | 不在・読取不能・無効 | `None`、表示`Ver. ?` | 値を捏造せず既存fallback表示 |
| 任意 | 別projectのTOMLだけ | installed値、なければ`None` | 外部project値を採用しない |

ここで「有効なアプリ自身のproject値」は暗黙pathとidentity確認を通ったものに限定する。明示path用の読取関数を`resolve_app_version()`から任意の外部pathで呼ばない。

**B2-G-RESOLVE判断ゲート:** sourceで実際に読み込んだmodule / resource path、旧installed値、project値、解決値の対応を直接testと独立probeで示せること。解決順変更は上表に限定して記録し、既存testを新しい値へ一括置換しない。installedのみの挙動やfrozen resource対応がこの範囲で成立しない場合はB2 Holdとし、namespace修復・再インストールを無断で代替策にしない。

### 8.2 Windows resource: 固定UTF-8入力をspecへ接続する

採用方式は、repo rootに`MMD_AutoLipTool.version.txt`を新規作成し、PyInstallerのversion text形式で管理する方式とする。B2実装時にレビュー可能なテキストとして作成・更新し、build時の生成ファイルを増やさない。正式値の正本は`pyproject.toml`、resourceは検証対象となる反映先である。

resourceの構成を次に固定する。

| 構造 / field | 計画値 |
| --- | --- |
| ルート | `VSVersionInfo` |
| FixedFileInfo.filevers / prodvers | 各`(1, 0, 0, 0)` |
| FixedFileInfo | mask `0x3f`、flags `0`、OS `0x40004`、fileType `0x1`、subtype `0`、date `(0, 0)` |
| StringFileInfo.StringTable | `040904B0`（英語 / Unicode）、1表のみ |
| FileVersion / ProductVersion | 各`1.0.0`。前置詞・末尾`.0`・suffixを付けない |
| ProductName / FileDescription | `MMD_AutoLipTool` |
| InternalName | `MMD_AutoLipTool` |
| OriginalFilename | `MMD_AutoLipTool.exe` |
| CompanyName | 配布readme §14の既存作者表記`kanna3939@Virtual JC`を再利用。法人の新規設定ではない |
| VarFileInfo.Translation | `[0x0409, 1200]`。StringTableの言語・codepageと一致 |

必要のない商標・新しいcopyright・署名情報は加えない。言語IDはresource検索用の識別子であり、アプリGUIの日本語表示を変更するものではない。

接続と管理は次のとおりとする。

- specの既存`project_root`から入力pathを解決し、`EXE`へ`version=str(project_root / "MMD_AutoLipTool.version.txt")`を渡す。`version_file=`という未確認のEXE引数を使わない。
- 既存の`name="MMD_AutoLipTool"`、`console=False`、icon、datas / binaries / hiddenimportsの収集方針を維持する。
- `build.ps1`は既存specを呼ぶため変更不要。CLI側だけへ`--version-file`を追加して反映済みと扱わない。
- 入力resourceはbuild専用であり、datasへ追加しない。最終ZIPにも独立ファイルとして入れない。B4隔離sourceの入力許可一覧には追加が必要である。
- 将来の版数変更時もpyprojectとの値対応を直接testで確認する。自動生成器・新規依存・versionの複数独立決定元を追加しない。
- B2ではloaderによる読込とメモリ上のシリアライズまで検証する。spec全体の実行、PyInstaller Analysis、EXE生成、`pyi-set_version`による後書きは行わない。

**B2-G-RESOURCE判断ゲート:** 現行PyInstallerで入力resourceを読め、文字列・固定数値・Translationが一致し、spec接続と隔離sourceへの引継ぎが明確であること。方式・入力path・解析が成立しない場合はB2 Holdとする。最終EXE上の値はB4で未確認として残し、B2 Passのためにbuildへ進まない。

### 8.3 旧版表記の分類と文書更新

| 分類 | 対象 | 処置 |
| --- | --- | --- |
| 現行版 | pyproject `0.4.0.0`、README冒頭、現在のproject値test | `1.0.0`へ更新 |
| 現行版を追加 | 配布readme冒頭、§12の今回の項目 | `1.0.0`を明記し、実装済みの版数整合に対応する説明を追加 |
| 現行ZIPの例 | Manifest §3 / §6の`v0.4.x` | 正確な`MMD_AutoLipTool_v1.0.0_Windows_onefile.zip`へ更新 |
| 保持する履歴 | 配布readmeの`v0.4.x` / `v0.3.x 以前`、旧MS記録、過去HEADでの値 | 日付・履歴として保持 |
| 独立fixture | `test_app_version.py`の`0.3.8.0` | 値を保持。必要なmock条件だけを新しい選択契約に合わせる |
| 別version | `pyopenjtalk==0.4.1`、Python / PyInstaller / FFmpeg、JSON schema、Whisper manifest等 | 更新しない |

README冒頭のMS17注記は現行版の状態説明として使わず、「MS26 CloseOut Aの機能基準、MS27配布検証は進行中」の到達状態へ最小同期する。`1.0.0`という正式値を採用したことから、公開済み・build済みとは記載しない。配布readmeの今回の項目にも公開日や未検証の配布成功を作らない。

Manifestへversion入力がbuild専用であることを記録する場合も、必須5ファイル、license条件、weights / sample等の除外方針を変更しない。ZIPの配置先・大文字小文字・suffixはB1 / Block BreakdownからB5へ引き継ぐ。

READMEの既存build例はB2検証commandとして使用しない。B2の追記でroot Clean手順を新たに推奨しない。MS27検証はB1の隔離source・絶対Python path契約に従う旨を開発者向けに最小注記し、具体的なbuild実行・結果と最終手順照合はB4 / B6に残す。

## 9. 詳細ステップ

### B2-01: baselineと変更対象の固定

1. live Git、B1最新Pass、§6のversion表を照合する。
2. 既存のproject metadataを読取専用で確認し、取得不能ならその理由を記録する。現行`0.4.0.0`という引継ぎ値と実値が異なれば両方を区別する。
3. `src/app_version.py`、resource helper、呼出し元、直接test、spec / build、版数文書を確認し、対象一覧を固定する。
4. `0.4.0.0` / `v0.4.x`の残存を§8.3へ分類する。検索hitをすべて変更対象にしない。

### B2-02: project宣言と版数解決の限定変更

1. project.versionを`1.0.0`へ変更する。
2. §8.1のresource選択とproject identity確認、不一致時選択を実装する。
3. runtimeのhardcode、metadata直接編集、project再インストールを導入していないことを差分確認する。
4. 既存のdisplay関数とGUI呼出しを維持する。必要ならtest名を新契約へ変更し、旧観点との対応を実施記録へ残す。

### B2-03: version resourceとspec接続

1. §8.2の固定入力をUTF-8で作成する。
2. specの`EXE(version=...)`へ接続する。相対入力がB4の隔離source内で解決されることを静的照合する。
3. sourceへのresource入力追加と最終ZIP非同梱をhandoffへ記録する。build.ps1やEXE名を変更しない。

### B2-04: 文書同期

1. README、配布readme、Manifestの現行版とZIP名を同期する。
2. 旧履歴・fixture・第三者versionの保持を確認する。
3. 未実施のGUI / package検証、license確認、公開を成功と記載していないか確認する。

### B2-05: 直接test実装と検証前の自己監査

1. §11のtestを対象2ファイルへ実装する。新規resource testにはGUI / build起動を含めない。
2. pyproject、resolver、resource、spec、文書の対応と対象外差分を照合する。
3. 問題があればB2対象内を最小修正し、testを削除・弱体化せず検証へ進む。

### B2-06: 必須検証と終了判定

1. 版数の直接test、resourceの直接testを別commandとして順次実行し、runnerの最終終了コードを取得する。
2. 実sourceの独立probeを行い、installed値・project値・実module path・resource path・解決値・表示文字列を記録する。wx / app起動を経由しない。
3. 残存旧版の分類、specの非実行静的照合、whitespace・変更範囲を確認する。
4. §12のB2受入条件を判定し、evidence / findings / unresolved / B3〜B5 handoffを記録する。B4の最終artifact欄は未確認のまま残す。

## 10. 状態遷移 / データ契約

### 10.1 状態

`Planned → 実装中 → 直接検証待ち → B2 Pass または B2 Hold`

B1のG-VERSION Passは「値と所有Blockの要件固定」である。B2 Passは「source反映と直接検証完了」であり、MS27-AC02全体の完了にはB4 / B5の実物証拠も必要となる。後続へ移る操作権限を本書から推定しない。

### 10.2 エラー・例外・副作用

- TOMLの不在、読取不能、不正構文、不正encoding、`project`の型不正、versionの型不正・空白だけ、暗黙pathのproject identity不一致は、そのproject値を採用しない。通常のデータ読取失敗をGUI起動停止へ変えず、metadata / `None`へ戻す。
- `OSError` / `tomllib.TOMLDecodeError`という既存の回復契約を保持し、不正UTF-8は必要な限定例外として扱う。包括的な`except Exception`で無関係なプログラム不良を隠さない。
- installed metadataの`PackageNotFoundError`は既存どおり不在として扱う。他の未確認例外まで無条件に握りつぶさない。
- 版数不一致は値の採用を変更するだけであり、metadata、pyproject、INIへのruntime書込みやダイアログ・通信を発生させない。
- 通常のfallbackとして旧metadataを表示できることと、今回のcandidate受入は別である。B2の実sourceでresource欠落の結果`0.4.0.0` / `Ver. ?`となった場合はB2 Hold。
- Windows resourceの欠落・不正構文・文字列 / 数値不一致はresource gate不合格。version指定を削除してbuildを通す計画に変更しない。
- テスト用TOMLや模擬bundleはtemporary pathへ人工データとして作成する。実runtimeファイルをfixtureに流用しない。テスト終了による所有temporary領域のcleanup以外、既存成果物を削除しない。

### 10.3 版数変更の影響範囲と証拠失効

`project.version`、resolver、spec、version入力を変更した場合、その後に取得した同一入力でB4 / B5を検証する。後続のEXEが既にある場合は該当B4証拠とそのEXEを使うB5証拠をstaleにする。resource入力をbuild input hash一覧へ追加する。

配布readmeのみの変更でもZIP bytesが変わるためB5証拠は更新が必要となる。非配布の本書だけの修正は、candidate bytes不変と影響なしを確認して証拠を再利用できる。古いtest結果を変更後の同じ欄へ上書きしない。

版数解決は文字列表示用に限定する。JSON schema、Whisper gate / model identity、fingerprint、VMD / WAV保存契約、GUI Busy / cancel / rollbackを変えない。

## 11. テスト方針

### 11.1 app versionの直接test

`tests/test_app_version.py`で次を検証する。計画作成時点ではnot runであり、実装後の結果は§15.4へ記録する。

| 観点 | 期待 / 維持する証拠 |
| --- | --- |
| 実projectの値 | 明示pathで実`pyproject.toml`を読み`1.0.0`。この期待値だけを旧現行版から更新 |
| 旧installed metadataとの競合 | installedを`0.4.0.0`とmockし、実repoのprojectを使って`resolve_app_version()`が`1.0.0`。project解決自体をmockして問題を隠さない |
| 一致・metadata不在 | 一致時もmetadata不在時もprojectの`1.0.0`を返す |
| metadataのみ | アプリ自身のproject値が得られない前提を明示し、従来のmock`0.3.8.0`とmetadata照会を検証 |
| project側からの取得 | 既存の`0.3.8.0`を使うproject fallback観点を保持。呼出し順変更を隠さず、metadataなしでproject値を得るtestとして明記 |
| すべて不在 | `None`と`Ver. ?`。既存のcustom fallback契約も維持 |
| 表示 | `0.3.8.0`の既存表示例を保持。現在値をformatした結果は`Ver. 1.0.0` |
| 明示path | `_candidate_pyproject_paths(explicit)`は明示pathだけ。最優先という既存契約を維持 |
| sourceのpath独立性 | temporaryなsource配置と別CWDを使い、resource基準が動かないことを検証 |
| 模擬frozen | temporary `_MEIPASS`に正しいprojectを置き、旧metadataがあっても`1.0.0`。実resource helper経路を通す。実onefile成功とは記録しない |
| 誤採用防止 | CWD / bundle外祖先に別versionのTOMLがあっても採用しない。暗黙pathの別project名は拒否 |
| データ読取失敗 | 欠落、OSError、不正TOML・UTF-8、型不正、空version、name不一致をtemporary data / mockで検証し、metadata / Noneへ回復 |

旧testの名前・mock条件を変更する場合、「従来何を証明したか」「新しくどの観点が同じ役割を証明するか」を実施欄へ記録する。`0.3.8.0`の全置換や、単に新しい実装と同じ分岐を書いたtestへの置換は行わない。

### 11.2 Windows version入力の直接testと静的確認

新規候補`tests/test_ms27_b2_windows_version_resource.py`で、既存PyInstallerのloaderを使って固定resource入力を読み、以下を検証する。

- `FileVersion` / `ProductVersion`がともに文字列`1.0.0`で、実pyprojectのversionとも一致する。
- fixedのfile / product数値がともに`(1, 0, 0, 0)`へ復元でき、文字列との対応が一致する。
- `OriginalFilename`、`InternalName`、Translation / StringTable対応が§8.2と一致する。
- `toRaw()`でメモリ上にserializeし、新しい`VSVersionInfo`の`fromRaw()`で読み戻して上記fieldが維持される。EXEやbinary fileへ保存しない。

Windows / PyInstallerはB1の環境を使用する。必要なloaderが利用不能なら原因を記録しHoldとし、dependencyを追加したり必須観点をskipして合格扱いしたりしない。

spec接続は、実行を伴わないAST解析または目視で`EXE(version=固定入力path)`、EXE名、`pyproject.toml -> .`保持を確認する。specを`exec` / `runpy`で読み込んで検査しない。resource testのためにPyInstaller Analysis / EXE生成を呼ばない。B4の最終resource照合をこのtestで代替しない。

### 11.3 将来の実装時に使う最小command

以下は**未実行の計画command**である。各行は独立して実行し、前のprocess終了と結果を確認してから次へ進む。

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_app_version.py
.\.venv\Scripts\python.exe -m pytest tests/test_ms27_b2_windows_version_resource.py
```

source独立probeでは上記Pythonで`app_version`だけをimportし、実module path、project / installed / resolved値、display文字列を採取する。`src/main.py`や`gui_wx.app`を起動入口に使わない。commandを実施時に固定し、台帳へ全文を残す。

```powershell
git diff --check
git diff --name-status
git status --short --branch
```

未追跡resource・test・本書がある場合は対象ごとに`git diff --no-index --check -- NUL <対象path>`を単独実行する。tracked diffだけでは新規ファイルのwhitespaceを検証できない。

直接testが成功し、spec変更がversion入力の接続だけで、GUI / shared resource helper / 依存への追加変更がなければ全suite・compileallを広げず終了する。追加の実行時影響が見つかれば具体的な不足を記録し、B2範囲で不足を解消できる最小testを選ぶ。GUI / onefile / 広範な補修を必要とするものは後続ownerまたは範囲判断へ渡す。

### 11.4 証拠と終了コード

- runnerが返した最終process exit codeを記録する。pass表示でも非ゼロなら両方を記録し、その必須gateはHold。
- pass / failure / error / skip件数、skip理由、終了未確認を区別する。未実行欄に`0`を入れない。
- 再実行は新しいCxxを発行し、失敗と再試行元IDを残す。timeoutだけで成功・失敗を推定せず、実process終了を追跡する。
- `rg`の該当なしや`git diff --no-index --check`の終了値はtestと区別する。後者の`1`は新規差分由来かつwhitespace診断なしの場合に限り正常な検査結果として扱う。
- GUIの未実施は`not run / B2外`、文書上の判断は`N/A（静的照合）`と記す。どちらもprocess code `0`で代用しない。

## 12. 受け入れ条件

| ID | B2で満たす条件 | 必要な証拠 |
| --- | --- | --- |
| MS27-B2-AC01 | B1 Pass、live baseline、正式版数・Windows値・固定EXE / ZIP名と対象差分が固定 | baseline、§6、旧版分類 |
| MS27-B2-AC02 | project宣言と実source解決値が`1.0.0`。旧installed `0.4.0.0`によって隠されない | 実projectを使う競合test、実source probe、metadata実値 |
| MS27-B2-AC03 | metadataのみ、不在、project不正、明示path、既存表示形式を保持し、変更した優先関係が明確 | `test_app_version`成功・最終exit code、既存6観点との対応 |
| MS27-B2-AC04 | source / 模擬frozenでアプリ自身のresourceを採用し、別TOMLを誤採用しない | 配置・CWD・project identityの直接test |
| MS27-B2-AC05 | UTF-8入力の両Windows文字列は厳密に`1.0.0`、固定数値は対応する4要素。loaderとメモリ上round-tripが成立 | resource直接test成功・最終exit code |
| MS27-B2-AC06 | specのversion接続、TOML収集、固定EXE名、B4隔離sourceへの入力追加が対応付く | 静的差分、resource入力path / hash、B4 handoff |
| MS27-B2-AC07 | README・配布readme・Manifestの現行版とZIP候補名が一致し、履歴・fixture・第三者versionは保持 | 文書差分と旧版分類 |
| MS27-B2-AC08 | dependency / runtime / GUI / build実行等の範囲逸脱がなく、whitespace・対象範囲を確認 | tracked / untracked差分の静的検査 |
| MS27-B2-AC09 | B2直接検証と未実施の最終EXE / GUI / ZIP / licenseが区別され、B3〜B5 ownerが明確 | 台帳、未確認表、handoff |

**B2 Pass:** AC01〜AC09とB2-G-RESOLVE / B2-G-RESOURCEを満たし、B2対象の未解消P1 / P2がない。残るP3があれば影響と扱いを明記する。最終EXE未確認はB4所有の予定検証として保持できる。

**B2 Hold:** source値不一致、版数解決方法未確定、resource方式・接続未成立、必須直接testの失敗・非ゼロ・未取得、対象外変更が必要、または未解消P1 / P2。owner、解除条件、依存しない継続可能作業を記録する。

計画段階はPlannedであり、test未実行を実検証失敗としてHoldにはしない。計画作成完了、B2 Pass、MS27全体Pass、公開済みは別の状態である。

## 13. リスクと対策

| リスク | 対応 |
| --- | --- |
| pyprojectだけ更新し旧metadataを表示する | 実project + 旧metadataの直接testとmockなしsource probeを必須にする |
| 単純なTOML優先化で別projectを採用する | 既存resource基準1箇所、暗黙pathのproject.name確認、CWD / ancestor負例 |
| 既存testの旧値を全置換してfallbackを失う | `0.3.8.0`保持、metadataのみとproject取得の各観点を継続 |
| frozenの実配置を模擬testだけで保証する | spec静的根拠と模擬testをB2証拠に限定し、実EXE / 起動はB4 / B5 |
| Windowsの4要素数値を正式版数へ逆流させる | StringFileInfoは3要素文字列、fixedは4要素という対応を各testとB4へ渡す |
| resourceとpyprojectの二重管理がずれる | projectとの一致testと入力hash、後続証拠のstale規則 |
| spec引数・CLI指定を取り違える | 現行EXE APIの`version=`へ接続し、build.ps1の別方式を増やさない |
| resource入力追加が隔離copyから漏れる | B4の明示入力許可一覧に追加、欠落時はHold |
| resource loaderが任意Python式を実行する | 自分たちが作成・レビューした固定入力だけを読む。外部resourceを実行しない |
| root Clean手順を版数検証に混ぜる | B2 commandからbuildを除外し、B1隔離実行契約をB4へ渡す |
| READMEの更新が配布完了宣言になる | MS26受入・B2反映・MS27配布検証中の時制を区別 |

## 14. Codex実装時の注意

- userの明示依頼と本書のB2対象を照合してから実装する。今回の計画依頼では本書以外を変更しない。
- commandは1つずつ実行する。パイプライン、連結、並列シェル、追加サブエージェントを使用しない。
- 編集前と最終報告前に、前提、例外、既存変更、対象外への波及を自己監査する。
- GUI importを避けたversion test / probeに限定する。実source出力の確認をスプラッシュ目視確認と呼ばない。
- 依存追加、venv改変、namespace修復、build手順改修が必要になった場合は、理由と具体的範囲を示してB2 Holdとする。既存の版数決定を再質問しない。
- MS26の実MMD結果はユーザー報告として継承する。Codex実行へ付け替えず、B2-R05を修正済み・無害とも断定しない。
- Git操作や公開を検証の前提にせず、HEAD・差分・hashで追跡する。stage / commit / push等へ自動移行しない。

## 15. Evidence ledger / 実施記録

### 15.1 記録規則

B1 §15のschemaを継承する。commandには`MS27-B2-Cxx`、手動確認には`MS27-B2-Mxx`、findingには`MS27-B2-Fxx`、未確認事項には`MS27-B2-Uxx`を使う。Uxxは成功証拠ではなく、解除に必要な証拠の管理IDである。

実施時は各commandを1行に分け、次を記録する。

`ID / owner / gate・AC / 日時・実施者 / HEAD・対象差分・入力hash / OS・Python path・version・tool / cwd・単独command / 期待・実結果・件数 / 最終process exit / ログ所在 / 判定・finding / 再試行元・stale関係`

新規resourceと変更コードには実装後SHA-256を付け、B4 input identityへ渡す。計画時点で存在しないresource / EXE / ZIPのhashを作らない。

### 15.2 B2検証予定・結果

以下はB2実装時に予約IDへ記録した結果である。C05の失敗は原因を限定修正し、再試行をC10として別記録した。

| ID | 予定対象 | Gate / AC | 実結果 | 最終process exit |
| --- | --- | --- | --- | --- |
| MS27-B2-C01 | 実装開始時のGit status | AC01 | `feature/MS27-implementation`、clean | 0 |
| MS27-B2-C02 | 実装開始時のHEAD取得 | AC01 | `153b2139531e54bdb5636e9f6b503a1c5fe88ecd` | 0 |
| MS27-B2-C03 | current project metadataの読取照会 | AC01 / AC02 | installed `0.4.0.0`、project `1.0.0`を確認 | 0 |
| MS27-B2-C04 | `pytest tests/test_app_version.py` | B2-G-RESOLVE / AC02〜04 | 10 passed in 0.23s | 0 |
| MS27-B2-C05 | resource直接test初回 | B2-G-RESOURCE / AC05 | 1 failed / 1 passed。`VarFileInfo`の型識別条件を修正対象として特定 | 1 |
| MS27-B2-C06 | GUI非起動の実source probe | AC02 / AC03 | installed `0.4.0.0`、project / resolved `1.0.0`、display `Ver. 1.0.0` | 0 |
| MS27-B2-C07 | 旧版表記の限定検索 | AC07 | 現行対象の旧版表記なし。`0.4.0.0`は意図したtest fixtureのみ | 0 |
| MS27-B2-C08 | `git diff --check` | AC08 | whitespace診断なし。LF/CRLF変換warningのみ | 0 |
| MS27-B2-C09 | 最終scope / Git status | AC08 / AC09 | B2対象9ファイル、runtime / 依存 / 外部素材の変更なし。実装後treeは本書更新前に確認 | 0 |

| MS27-B2-C10 | resource直接test再試行 | B2-G-RESOURCE / AC05 | 2 passed in 0.22s。resource値、固定数値、Translation、round-trip、spec接続・固定EXE名を確認 | 0 |
| MS27-B2-C11 | 新規version resourceのwhitespace | AC08 | whitespace診断なし。新規差分由来の終了コード1 | 1 |
| MS27-B2-C12 | 新規resource testのwhitespace | AC08 | whitespace診断なし。新規差分由来の終了コード1、LF/CRLF変換warningのみ | 1 |

spec接続を含む静的確認はC10のresource testで実施した。新規差分由来の`git diff --no-index --check`終了コード1は、診断なしのためwhitespace gateを阻害しない。

### 15.3 計画作成時の実施境界

- 計画作成で実施したこと: live Git確認、指定資料・関係コード / test / 配布定義・PyInstaller現行ソースと公式資料のread-only確認、本書の作成・静的点検。
- 計画作成のGit観測: `feature/MS27-implementation`、HEAD `9e9cc64`、作成前clean、upstream未設定。
- B1のPassは既存文書の実施記録を継承する。今回B1のOS / FFmpeg照会を再実行していない。
- この節の記録は計画作成時点のものであり、B2実装結果は次節へ分離した。

計画文書の静的検査では、`git diff --no-index --check -- NUL docs/Implementation_Plan/MS27-B2_Implementation_Plan.md`はexit code `1`、whitespace診断なしであった（新規差分由来）。`git diff --stat`はexit code `0`でtracked差分なし、`git status --short --branch`はexit code `0`で本書1件のみ未追跡と確認した。これらは文書作成範囲の検査結果であり、B2の実装・直接test成功ではない。

### 15.4 B2実施済みevidence ledger

- 実施者: メインエージェント
- 実施日: 2026-09-13
- 実装開始時HEAD: `153b2139531e54bdb5636e9f6b503a1c5fe88ecd`
- 版数解決: `src/app_version.py`がアプリresource基準の`pyproject.toml`を読み、アプリ自身のproject nameを確認する。installed metadata `0.4.0.0`との不一致時はsource / frozen resourceの`1.0.0`を採用し、resource不在時はinstalled値へfallbackする。
- Windows resource: `MMD_AutoLipTool.version.txt`を作成し、文字列FileVersion / ProductVersionは`1.0.0`、固定数値は両方`(1, 0, 0, 0)`、Translationは`[1033, 1200]`。specの`EXE(version=...)`へ接続した。
- 直接test: `tests/test_app_version.py` 10 passed、`tests/test_ms27_b2_windows_version_resource.py` 2 passed。初回resource testの1 failureは検査ヘルパーの`VarFileInfo`型識別ミスであり、resource方式の不成立ではない。修正後の再試行はC10で終了コード0。
- 独立probe: installed `0.4.0.0`、project `1.0.0`、resolved `1.0.0`、display `Ver. 1.0.0`。
- 入力identity: `pyproject.toml` SHA-256 `C9C376A5400CF9ADBA67E48A580A53C5BF7533CE38EE725DEE6DD6AA95D46034`、`src/app_version.py` SHA-256 `98286DD86379B5AD643478509F88C6DF758ECEF47C446975C730B2FB15A78CF4`、`MMD_AutoLipTool.spec` SHA-256 `2EECD269DCEA20D26F3443A9240690E74D2DB99F3088014087CBCDA4BA31591C`、`MMD_AutoLipTool.version.txt` SHA-256 `12D34A08F8384DF1B944A675A0AEDD10C485A64263B5474820904A352235C41E`。
- 静的差分: 旧`v0.4.x`のManifest現行例を削除し、`MMD_AutoLipTool_v1.0.0_Windows_onefile.zip`へ同期。旧`0.4.0.0`はtest fixtureとして保持した。
- 未実施: full pytest、compileall、PyInstaller onefile、SmokeLaunch、最終EXEのFileVersion/ProductVersion、ZIP生成・展開、GUI、実MMD、FFmpeg license原本、Python 3.11 / 3.12互換性。これらはB2 Passに含めず、後続Blockへ引き継ぐ。

### 15.5 B2実施判定

B2は**Pass**。AC01〜AC09、B2-G-RESOLVE、B2-G-RESOURCEを満たし、今回のresource test初回failureは限定修正後に再試行成功した。最終EXE・ZIP・GUI・実MMD・licenseの未確認は、B2の範囲逸脱ではなくB3〜B5の後続gateで確認する。

## 16. B3 / B4 / B5へのhandoff

| Owner | B2から渡すもの | 後続で確認すること / Hold条件 |
| --- | --- | --- |
| B3 | version差分、依存変更なしの根拠、Manifestの命名差分、build専用resource追加 | license / 同梱許可一覧を確定。resource入力をZIP必須物へ混ぜない。FFmpeg原本不足はB3 Hold |
| B4 | B2証拠ID、HEAD・差分、pyproject / resolver / spec / resourceの入力hash、`pyproject.toml -> .`、version入力path | 隔離source許可一覧へresourceを追加し、B1の絶対cwd / PythonExe契約でbuild。最終EXEの両文字列`1.0.0`と固定数値、内部TOML / metadata / module配置を確認。不一致・欠落ならHold |
| B5 | 固定EXE名、正確なZIP名、B2文書差分、B4で確認すべき版数一覧 | B4と同じEXE hashで組立・展開。実スプラッシュ`Ver. 1.0.0`、正常終了、開発環境からの独立性を確認。未確認ならHold |
| B6 | B2 Pass / Hold、未確認表、旧版分類、非配布文書の状態、証拠失効条件 | MS27全体の証拠・routing・readinessを同期。公開操作は別権限 |

B4では、例えばEXEを起動しない`VersionInfo`照会とresource読取を用い、`FileVersion` / `ProductVersion`文字列と数値partsを別欄へ記録する。具体的commandはB4 planで固定する。Windowsが数値を4要素として表示しても、両文字列が厳密に`1.0.0`である確認を省略しない。

B4にsourceと異なるinstalled metadataが入った場合、表示が一致したことだけで同梱metadataを正しいと記録しない。内部値・出所・採用経路を記録し、version整合または同梱監査に影響するものはB2 / B3へ戻す。B2でmetadataの無差別収集・削除を先行実装しない。

## 17. 未確認事項・ユーザー確認

| ID | 未確認事項 | 状態 / 解除条件 | Owner |
| --- | --- | --- | --- |
| MS27-B2-U01 | 新resolverでの実source解決値と旧metadataとの競合結果 | C03 / C04 / C06で確認済み。installed `0.4.0.0`に対してresolved `1.0.0` | B2 |
| MS27-B2-U02 | Windows resource入力の実作成・loader / round-trip結果 | C10で確認済み。resource入力、文字列、固定数値、Translation、round-tripが一致 | B2 |
| MS27-B2-U03 | spec接続の反映結果・B4 input hash | C10と§15.4のhashで確認済み。B4の隔離sourceへ同一入力を引き継ぐ | B2 |
| MS27-B2-U04 | 最終EXEのFileVersion / ProductVersion、fixed値、frozen resource / metadata | 未確認。B4の同一EXE hashに結び付いた実物証拠 | B4 |
| MS27-B2-U05 | 実スプラッシュ・展開ZIPの版数一致と正常終了 | 未確認。B5の配布環境確認 | B5 |
| MS27-B2-U06 | FFmpeg等の正確なlicense・必要対応物、最終同梱内容 | 未確認。B1の既存未確認を継承。G-LICENSE / artifact証拠 | B3 / B4 / B5 |
| MS27-B2-U07 | Python 3.11 / 3.12互換性 | 未検証。今回のB2から新しい必須実行へ拡張しない | MS27の環境・readiness記録 |

計画・実装時点で新たなユーザー確認は不要と判断する。版数、Windows文字列、EXE / ZIP名は既に固定され、版数解決とresource方式は現行の限定変更として実装・検証できた。

実装時に新規依存、公開値変更、配布方式変更、対象外のnamespace / GUI修復などが必要と判明し、資料と既存権限から解決できない場合は、その選択と影響を具体的に示して質問する。既に固定された`1.0.0`の再確認や、未実施という理由だけの追加承認要求は行わない。

## 18. 完了条件と報告

- **今回の計画作成完了:** 指定1ファイルを作成し、現状対応、解決方針、resource方式、実装順、test / AC / Hold、証拠欄、後続owner、未確認事項を静的照合した時点。
- **B2実装完了（今回）:** §12の条件を満たし、§15.4〜§15.5へ実装結果・直接test・source probe・入力identity・未確認事項を記録した。B2 PassはMS27全体Pass、最終EXE検証、配布公開を意味しない。
- 計画担当は、作成file、確認範囲、実施していない操作、質問の要否をメインへ返す。メインが成果物の採否を確認する。
- 実装担当は、確認・変更file、優先関係の変更、resource接続、testと終了コード、逸脱・残課題・B4未検証を日本語で報告する。
- 報告後、許可されていない実装・Git操作・後続Block・公開へ進まない。
