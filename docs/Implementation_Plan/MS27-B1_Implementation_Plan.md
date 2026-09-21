# MS27-B1 Implementation Plan

## 1. 文書情報

- 文書名: `docs/Implementation_Plan/MS27-B1_Implementation_Plan.md`
- 対象マイルストーン: MS27 Ver.1.0 Packaging / Release Readiness Closeout
- 対象Block: MS27-B1 基準・版数・検証環境gate固定
- 作成日: 2026-09-13
- 対象リポジトリ: `D:\Kanna_Works\MMD_AppWork\MMD_AutoLipTool-dev\MMD_AutoLipTool_Antigravity`
- 計画作成時のユーザー提示ブランチ: `feature/MS27-implementation`
- 計画作成時のユーザー提示HEAD: `2151d7b`（`Document MS26 Closeout A`）
- 計画作成時のユーザー提示upstream: 未設定
- 計画作成時のユーザー提示working tree: `docs/Implementation_Plan/MS27_Block_Breakdown.md`の未追跡のみ
- 正式版数: **`1.0.0`**（メジャー・マイナー・リビジョン。ユーザー決定済み）
- 計画作成時の状態: **Planned。B1の実施、検証、成果物作成、版数反映は未実施。**
- B1実施状態（2026-09-13）: **baseline・環境・FFmpeg入力のevidence取得済み。Windows 11 Pro / 64bitを管理者権限の読み取り専用CIM照会で確認し、B1 gateはPass。B2以降の実装・検証は未実施。**
- 本計画の作成で変更を許可されたファイル: 本文書のみ。本文書以外は変更しない。

### 1.1 現在の作成作業とB1実施の区別

本計画は、B1実施時に行う読み取り、記録、ゲート判定の手順を定める文書である。今回の計画作成では、ユーザーから提示された現行証拠を計画の前提として記載するが、B1のlive Git確認、環境確認、FFmpeg確認、版数テスト、build、SmokeLaunch、ZIP、runtime起動を実行したとは扱わない。

B1を実施するときは、その開始時点のlive Git、HEAD、working tree、環境、入力hashを再取得する。ここに記載した`2151d7b`やworking treeの内容は、B1実施時に再確認すべき開始時証拠であり、将来の検証結果へ自動転用しない。

## 2. 背景

MS26は、MS20〜MS25の機能統合、Windows 11上のGUI確認、実MMDでのVMD・MMD用WAVの確認を含むCloseOut Aとして扱う。MS27は、MS26の機能受入をやり直す工程ではなく、Ver.1.0.0候補の版数、PyInstaller onefile、配布ZIP、依存関係、FFmpeg、ライセンス、最終artifactのrelease readinessを確認する工程である。

既存のMS27 Block Breakdownは、正式版数を`1.0.0`とし、版数反映、onefile build、SmokeLaunch、ZIP内容、Whisper model weights非同梱、runtime JSON / INIと`models`非同梱、`sample`除外、FFmpeg GPL / version3構成、PySide6の最終artifact混入確認、Pass / Hold判定をMS27の対象としている。B1はこれらの後続確認を開始できる基準と、証拠が失効する条件を固定する。

現行のbuild入口は、リポジトリ直下の`build`、`dist\MMD_AutoLipTool`、`dist\MMD_AutoLipTool.exe`を参照する。`build.ps1 -Clean`はこれらのroot配下成果物を削除してからPyInstallerを実行するため、既存のユーザー所有成果物を含むリポジトリrootへ無断で適用してはならない。B1では、B4が使う一時作業コピー、削除対象の所有範囲、実行前の停止条件を定める。

## 3. 目的

1. MS26 CloseOut Aを機能受入の基準として固定し、MS27で実MMD受入を再判定しない境界を明確にする。
2. 正式版数`1.0.0`をB1のversion表へ確定値として記録し、B2がコード・文書・直接テストへ反映する開始条件を定める。
3. Windows、Python、PyInstaller、hooks、依存関係、FFmpeg/build入力、配布確認環境を、設定値と実環境値を分けて記録できるようにする。
4. root成果物を破棄しない隔離build方法、ログ・ZIP・展開先の所有範囲、runtimeデータの境界を固定する。
5. B1〜B6の責務、依存、成果物、受入条件、evidence ledger、証拠失効規則を定める。
6. 不明なライセンス、未確認artifact、版数resourceの反映未実施・最終exe未確認を推測で埋めず、後続BlockのHold条件または未確認事項として渡す。

## 4. In Scope

MS27-B1の実施範囲は、次の読み取り、照合、記録、ゲート固定に限定する。

- B1開始時のlive Git、HEAD、branch、upstream、working tree、既存変更の読み取り専用baseline
- `2151d7b Document MS26 Closeout A`をMS26の引継ぎ基準として記録し、過去の中間Pending / deferred記録とMS26 CloseOut Aを区別
- 正式版数`1.0.0`のversion表作成
- `0.4.0.0`から`1.0.0`への更新対象と、履歴・fixture値・第三者依存versionを維持する境界の分類
- `pyproject.toml`、`README.md`、`readme_mmdautolip.txt`、アプリ版数解決経路、配布ZIP名のB2受入基準の固定
- Windows 11、Python executable / version / architecture、PyInstaller、`pyinstaller-hooks-contrib`、直接依存・実解決依存の実環境表の設計と、B1実施時の取得方法の固定
- `FFmpeg\bin\`のbuild入力ファイル一覧、version、configuration、hash、ライセンス原本の確認状態の記録
- `build.ps1`と`MMD_AutoLipTool.spec`の固定出力名、入力、resource収集、root削除範囲の読み取り
- B4で使う一時作業コピー、build / dist、ログ、ZIP組立、ZIP展開、配布確認用の隔離pathと所有条件の固定
- 実行用ZIPの必須ファイル、license文書、除外対象の判定境界の固定
- 共通evidence ledgerのID、列、所有Block、process exit code、hash、失効・再実行規則の固定
- B2〜B6の責務、依存、成果物、開始条件、Holdの伝播条件の固定
- Windows FileVersion / ProductVersionとも正式版数`1.0.0`に設定する要件、B2のspec/version resource実装方法決定、B4の最終exe検証責務の固定

## 5. Out of Scope

- production code、test code、build設定、PyInstaller spec、依存定義、license文書、READMEその他の文書の変更
- `pytest`、`unittest`、`compileall`、静的解析、直接テストの実行
- PyInstaller onefile build、`build.ps1`実行、SmokeLaunch、GUI起動、通常終了確認
- ZIP作成、ZIP展開、配布環境での起動、最終artifactの生成・検査
- runtimeの`presets.json`、`profiles.json`、`MMD_AutoLipTool.ini`の読み取り、編集、コピー、fixture化
- Whisper model weights、`models`、sample、受入音声・TEXT、PMX / PMD、外部素材のコピー・実行・配布
- 実MMDでのVMD / WAV読込、再生、morph対応、時間同期、見た目の確認。これはMS26 CloseOut Aの記録を再判定しない。
- GitHub Release公開、tag作成、remote push、merge、publish、installer新規導入
- stage、commit、branch変更、既存root成果物の削除、既存データの破棄
- 新規依存の追加、FFmpeg binaryの差し替え、FFmpeg構成の変更、旧Qt / PySide6 GUIの復活
- 過去のMS26 / MS24 / MS25のテスト成功値や静的監査結果を、B1のlive実行結果として扱うこと

## 6. 前提条件

### 6.1 MS26の引継ぎ境界

- MS26はCloseOut Aとして扱う。MS27-B1は、MS26の実MMD受入を再検定せず、MS26で確定した機能基準をpackage検証の入力条件として記録する。
- MS26の実MMD確認はユーザー報告として記録されたものであり、Codex自身がMMDを操作した証拠とは区別する。B1はこの証拠の実施者・範囲を変更しない。
- MS26のPMX hash独立取得不可、B2-R05 daemon候補、過去の中間Pending / deferredは、MS27のpackage failureやMS26未完了へ読み替えない。
- MS27のonefile、ZIP、license、最終artifactの確認はMS26のactual-MMD受入とは別gateである。

### 6.2 現行証拠とB1実施時の再確認

| 項目 | 現行証拠（ユーザー提示・計画作成時点） | B1実施時の扱い |
| --- | --- | --- |
| HEAD | `2151d7b`、`Document MS26 Closeout A` | live `HEAD`、commit title、対象差分を再取得し、証拠へ束縛する |
| branch | `feature/MS27-implementation` | branch名を再取得し、MS27対象branchと一致するか確認する |
| upstream | 未設定 | 未設定を記録する。remote操作やpushを行わず、upstream不在を異常成功へ変換しない |
| working tree | `docs/Implementation_Plan/MS27_Block_Breakdown.md`未追跡のみ | B1開始時の全statusを再取得する。想定外のcode / test / build / runtime変更があればHoldとする |
| 正式版数 | ユーザー決定済み`1.0.0` | version表の確定値として記録する。B1で再交渉しない |
| project version | `pyproject.toml`は`0.4.0.0` | B2の更新前の基準値として記録する。今回B1では変更しない |
| Python metadata | `requires-python = ">=3.11"` | metadataの下限と、実際にB1 / B4で使うPython versionを別欄へ記録する |
| direct dependencies | `wxPython==4.2.5`、`matplotlib==3.10.8`、`numpy==2.4.3`、`openai-whisper==20250625`、`pyopenjtalk==0.4.1`の5件 | 宣言値と実解決値を別々に取得する。第三者package versionを`1.0.0`へ変更しない |
| app version path | `src/app_version.py`はinstalled metadata優先、`pyproject.toml` fallback | B1は読み取りと経路記録のみ。B2が`1.0.0`反映と直接テストを担当する |
| direct version test | `tests/test_app_version.py`は実project versionの期待値`0.4.0.0`を持つ | B2が期待値を`1.0.0`へ更新し、mock値・fallback・解決順のテストを維持する |
| build入口 | `build.ps1`はrepo直下の`build`、`dist\MMD_AutoLipTool`、`dist\MMD_AutoLipTool.exe`を参照し、`-Clean`で削除する | B1はrootで実行しない。B4用隔離copyと削除所有条件を固定する |
| spec | onefile、exe名`MMD_AutoLipTool`、`FFmpeg\bin`内の`.gitkeep`以外の通常ファイルを収集 | B1は設定を変更しない。B4がAnalysis TOC・内部archiveと照合する |
| FFmpeg | `FFmpeg\bin`の現行実体は存在するが、現行license原本は未確認 | B1は入力一覧・version・hash・確認状態を記録し、原本不足を推測で埋めない。G-LICENSEはB3が判定する |
| final artifact | 最終onefile artifactは未確認 | B1は未確認として記録し、B4が新規artifact、B5がZIP候補を担当する |

この表の「現行証拠」はB1の成功結果ではない。B1実施時にlive状態が異なる場合は、差分と影響をevidence ledgerへ記録し、過去値を上書きしない。

### 6.2.1 B1実施時のlive evidence

2026-09-13にB1の読み取り専用baselineを取得した。計画作成時点のHEAD `2151d7b`から、MS27計画文書を記録したコミット`90edd81`へ進んでいる。実施時点の値は次のとおりであり、計画作成時のユーザー提示値へ遡って置き換えない。

| 項目 | B1実施結果 | Evidence |
| --- | --- | --- |
| cwd | `D:\Kanna_Works\MMD_AppWork\MMD_AutoLipTool-dev\MMD_AutoLipTool_Antigravity` | `MS27-B1-C01` |
| branch | `feature/MS27-implementation` | `MS27-B1-C02` / `C03` |
| HEAD | `90edd81601465cff683b8bca6f710f1386a18877`、`Document MS27 implementation plans` | `MS27-B1-C04` / `C05` |
| upstream | 未設定。`git rev-parse --abbrev-ref --symbolic-full-name "@{u}"`は終了コード1 | `MS27-B1-C06` |
| working tree | B1開始時はclean | `MS27-B1-C02` |
| `2151d7b..HEAD`差分 | MS27計画文書2件のみ | `MS27-B1-C30` |
| Python | 3.14.3、64bit、AMD64。実行ファイル絶対pathは`.venv\\Scripts\\python.exe`の解決結果を記録 | `MS27-B1-C07`、`C23` |
| PyInstaller / hooks | PyInstaller 6.19.0、`pyinstaller-hooks-contrib` 2026.3 | `MS27-B1-C08`、`C23` |
| package metadata | direct dependency 5件と`tiktoken`の実解決値を確認。`tiktoken_ext`はdistribution metadataではなくnamespace moduleとして存在 | `MS27-B1-C22` / `C23` |
| FFmpeg | `N-123549-g70537ec8e6-20260318`、`--enable-gpl --enable-version3`等のconfigurationを`ffmpeg` / `ffprobe`双方で確認 | `MS27-B1-C09` / `C10` |
| FFmpeg input hash | 実体10ファイルのSHA-256を取得 | `MS27-B1-C12`〜`C21` |
| OS | 標準照会は`Windows 10 Pro / 2009`または空欄を返したが、管理者権限のCIM照会で`Microsoft Windows 11 Pro`、Version `10.0.26200`、BuildNumber `26200`、`64 ビット`を確認 | `MS27-B1-C24`〜`C27`、`C31` / `C32` |
| lock | `uv.lock`、`poetry.lock`、`Pipfile.lock`は見つからず、`pyproject.toml`と`requirements.txt`が存在 | `MS27-B1-C29` |

標準照会とregistryのProductNameには互換表示由来とみられる不一致があったが、管理者権限のCIM照会でWindows 11 Proを直接確認できたため、OS identityに関するB1 Holdを解消する。registryの値だけを根拠にはしていない。

### 6.3 B1実施開始条件

B1を実施できるのは、次の開始条件を満たす場合である。

- 対象repositoryの場所、対象branch、MS26 CloseOut Aの基準commitが特定できる。
- B1開始時のworking treeを読み取り、既存のユーザー変更を保護できる。
- `1.0.0`を正式版数としてversion表へ記録できる。
- B1がcode / test / build / runtime / external materialを実行しないことを実施者が維持できる。
- B4用の隔離path候補が、repository rootやユーザー作業領域と別に確保できる。
- B4実行時に、隔離sourceの絶対pathを実行cwdへ設定し、`-PythonExe`へ使用Python実行ファイルの絶対pathを渡す手順を固定できる。相対pathの解決先を隔離source内に限定し、repo rootのbuild / dist / exeへ触れない境界を記録できる。
- Windows FileVersion / ProductVersionとも`1.0.0`に設定するユーザー決定をversion tableへ記録し、B2の実装方法決定とB4の最終exe検証のhandoffを固定できる。

## 7. 対象ファイル

### 7.1 B1で読み取り対象とする現行資料

| 分類 | 対象 | B1で行うこと |
| --- | --- | --- |
| 正本routing / roadmap | `docs/MS20_and_Beyond_Roadmap.md`、`docs/MS20_and_Beyond_Index.md` | MS26 CloseOut A、MS27 §14、過去の中間記録の役割を照合 |
| MS27計画 | `docs/Implementation_Plan/MS27_Block_Breakdown.md` | B1責務、`1.0.0` version gate、B2〜B6境界、Pass / Holdを本計画へ対応付ける |
| package manifest | `docs/Release_Package_Manifest.md` | 必須・除外・Whisper weights・sample・PySide6・FFmpeg確認項目を照合 |
| 利用者向け文書 | `README.md`、`readme_mmdautolip.txt` | 現行`0.4.0.0`表記、onefile、モデル非同梱、MMD確認案内を基準値として記録 |
| project / distribution | `pyproject.toml`、`build.ps1`、`MMD_AutoLipTool.spec` | version、依存、resource、FFmpeg収集、root出力・Clean範囲を記録 |
| license | `LICENSE`、`NOTICE`、`THIRD_PARTY_LICENSES.md` | 本文・概要・FFmpeg license原本の確認状態を分けて記録 |

### 7.2 B1で読み取り対象とする実装・テスト境界

B1は実装・テストを変更または実行しないが、版数解決と配布入口を計画へ対応付けるため、次を読み取り対象とする。

- `src/app_version.py`: installed metadata優先、`pyproject.toml` fallbackの版数解決経路
- `src/gui_wx/app.py`: `format_app_version_display(resolve_app_version())`によるスプラッシュ表示経路
- `tests/test_app_version.py`: project version期待値、mock値、fallback、表示形式の検証範囲
- `requirements.txt`: PyInstaller、hooks、依存の宣言値を確認する補助資料

B2は`pyproject.toml`、README、配布用readme、Release Package Manifest等の版数・配布案内と、必要な版数解決コード、`tests/test_app_version.py`の直接期待値更新を所有する。B1はこれらを変更せず、B2が`1.0.0`のコード・文書更新と直接テストを担当することを開始条件へ固定する。

### 7.3 B1で作成を計画する記録

B1実施時の記録は、実際に作成したB1個別計画またはMS27の許可された証拠記録へ置く。今回の計画作成では、次の実行ログ、hash台帳、build copy、ZIP、artifactを作成しない。

- baseline表、環境表、version表
- FFmpeg/build入力一覧と確認状態
- 配布確認環境表、隔離path所有表
- 共通evidence ledgerの初期行とB1 gate判定
- B2〜B6のowner / dependency / start condition / Hold条件表
- 確定済み版数resource要件と未確認事項の一覧

## 8. 実装方針

### 8.1 Version table

B1のversion tableは、正式版数を再決定する表ではなく、ユーザー決定済みの`1.0.0`を後続の各反映箇所へ束縛する表とする。

| 項目 | B1で固定する値・境界 | 実反映・確認のowner |
| --- | --- | --- |
| 正式版数 | `1.0.0` | B1が確定値を記録、B2が反映 |
| 現行project version | `0.4.0.0` | B1が変更前値として記録、B2が更新 |
| `pyproject.toml` | `project.version = "1.0.0"`を目標値とする | B2 |
| アプリ表示 | `Ver. 1.0.0` | B2がsource経路を確認、B4 / B5がfrozen表示を確認 |
| `README.md` | 現行版表示を`Ver. 1.0.0`へ同期 | B2 |
| `readme_mmdautolip.txt` | 現行配布版を`1.0.0`として案内。`v0.4.x`等の履歴は保持 | B2 |
| ZIP名 | `MMD_AutoLipTool_v1.0.0_Windows_onefile.zip` | B2が規則を固定、B5が実物を確認 |
| exe名 | `MMD_AutoLipTool.exe`を維持 | B4 / B5 |
| Windows FileVersion / ProductVersion | 現行specに指定なし。両方を正式版数`1.0.0`に設定する要件はユーザー決定済み | 実際のspec/version resource反映方法はB2が決定・反映し、B4が最終exeで検証。現時点で設定済み・検証済みとは記載しない |
| JSON schema / fingerprint / Whisper manifest version | `1.0.0`へ変更しない | 全Blockで境界を維持 |
| 履歴・fixture・第三者依存version | 現行値を保持し、正式版数変更の対象にしない | B2が差分分類、B6が最終確認 |

`1.0.0`の正式決定と、各対象へ実際に反映されたことは別の事実である。Windows FileVersion / ProductVersionの設定要件も確定済みだが、実際のspec/version resource反映はB2、最終exeでの検証はB4の責務である。B1では決定値を固定し、反映未実施・最終artifact未確認を未実施・未確認として記録する。B2の受入には、source側の値、版数解決、文書、直接テストの一致を含める。

### 8.2 実環境表

B1実施時に、設定ファイルの宣言値と、実際に使用する環境の値を同じ欄へ混在させない。

| 区分 | 記録項目 | 取得・照合内容 | B1時点の状態 |
| --- | --- | --- | --- |
| OS | Windows edition / version / build / architecture | 配布確認に使うWindows 11環境の実値 | 管理者権限のCIMで`Microsoft Windows 11 Pro`、Version `10.0.26200`、BuildNumber `26200`、`64 ビット`を確認。標準照会の互換表示差は注記として保持 |
| Python | executable absolute path、version、architecture | B1 / B4で使うPythonを固定。`requires-python >=3.11`と分離 | 3.14.3、64bit、AMD64。絶対pathは`D:\Kanna_Works\MMD_AppWork\MMD_AutoLipTool-dev\MMD_AutoLipTool_Antigravity\.venv\Scripts\python.exe` |
| PyInstaller | package version、実行経路 | `requirements.txt`の宣言と実環境のversionを比較 | 宣言・実値とも`6.19.0` |
| hooks | `pyinstaller-hooks-contrib` version | 宣言値と実解決値を比較 | 宣言・実値とも`2026.3` |
| direct dependency | wxPython、matplotlib、numpy、openai-whisper、pyopenjtalk | 5件の宣言versionと実解決version、architectureを記録 | 宣言・実値が一致（`wxPython 4.2.5`、`matplotlib 3.10.8`、`numpy 2.4.3`、`openai-whisper 20250625`、`pyopenjtalk 0.4.1`） |
| transitive / native | tiktoken、tiktoken_ext、pyopenjtalk data / DLL、matplotlib backend等 | 実環境とAnalysis資料で収集根拠を照合 | `tiktoken 0.14.0`、`tiktoken_ext`はdistribution metadataなしのnamespace moduleとして実体確認。Analysis資料・native要素は未確認 |
| FFmpeg | `ffmpeg.exe`、`ffprobe.exe`、`ffplay.exe`、DLL一覧、path、size、SHA-256、version、configuration | build入力の実体を固定。過去versionは比較情報に留める | 10実体の一覧・hash、`ffmpeg` / `ffprobe`のversion・configurationを確認。license原本・最終artifactは未確認 |
| packaging input | spec、build script、assets、license文書、package data | B4 copyへ入れる許可一覧を固定 | 実copy未作成 |
| distribution environment | clean extraction path、Python / repo / PATH FFmpegへの依存有無 | ZIP展開後の独立起動条件を固定 | B1では未取得。B5へhandoff |

実解決versionとFFmpeg configurationはB1で取得したが、FFmpeg license原本、Analysis資料、final artifactは未確認である。B1は取得結果と未確認状態を固定し、B3 / B4 / B5が所有する確認へ渡す。

### 8.3 FFmpeg / build入力の扱い

- 現行specは`FFmpeg\bin`の`.gitkeep`を除く通常ファイルを、onefileの内部`FFmpeg`へ収集する。B1ではこの収集設定を変更せず、実在する全入力を一覧化する。
- `ffmpeg.exe`、`ffprobe.exe`、`ffplay.exe`、DLLの必要性、同梱可否、通知範囲は、拡張子や過去の記録だけで決めない。
- 過去資料にあるFFmpeg versionや`--enable-gpl --enable-version3`は履歴情報として記録する。B1は現在のbinaryへ同じ構成を推定適用しない。
- 現行FFmpeg license原本と、B4で生成される最終artifactは未確認である。正確なlicense本文、copyright、configuration、再配布条件、必要な通知・対応物が確認できない場合は、B3のG-LICENSEをHoldとし、B4以降へPassを渡さない。
- `THIRD_PARTY_LICENSES.md`の概要、`NOTICE`の一般案内、過去のP2解消記録だけでは、採用binaryの正確なライセンス証拠を代替しない。

2026-09-13のB1実施では、`ffmpeg.exe` / `ffprobe.exe`のversion表示とconfigurationを確認し、次の10ファイルについてSHA-256を取得した。これらは入力identityであり、license適合、onefile内部への最終同梱、ZIP配布可否のPassを意味しない。

| File | SHA-256 | Evidence |
| --- | --- | --- |
| `avcodec-62.dll` | `BE77A6E1872DF4591F090D948CD19FE3A1D0C02EF2642BF8A3307C33898F4E50` | `MS27-B1-C12` |
| `avdevice-62.dll` | `663A69109279A8A1C49AAA85FF18613C31C0FD9FE9F2DD87371C068B36B20858` | `MS27-B1-C13` |
| `avfilter-11.dll` | `59A7058E977D70C9B3A126303C44D691562CFF61080E8C89B9CD5D5168B3E847` | `MS27-B1-C14` |
| `avformat-62.dll` | `4B7E2144962F7851B828169BA162146CE77F99ED3AEBACD10959E6E4E619BD2B` | `MS27-B1-C15` |
| `avutil-60.dll` | `1B37A5835A1D895FB24A5DD0CAA84231B9EDFB753A76B5231748CE069E656259` | `MS27-B1-C16` |
| `ffmpeg.exe` | `25F9F739794E20C7EBA08DD2E6C9165F79CA5C6D4423E07E9575DA0EA957E6D5` | `MS27-B1-C17` |
| `ffplay.exe` | `EDA12E438A5D509B0BE4D05292D58DB916C9049544A03A49BCF6B7F10A8C20F3` | `MS27-B1-C18` |
| `ffprobe.exe` | `29221ACCA37F2BFB30CC17F1F9F219CEE0636383DFE48B4A8292B895AF988980` | `MS27-B1-C19` |
| `swresample-6.dll` | `C003F7911D0C160C0387D74F54A55BAF40C003405F7B322B46545988C2D76775` | `MS27-B1-C20` |
| `swscale-9.dll` | `E4089B3487534BAE9D4CAB56D694A738787C69201CB891BDE2DC3D0CC45267F9` | `MS27-B1-C21` |

### 8.4 `build.ps1 -Clean`の安全な隔離方法

B1はbuildを実行しないが、B4がroot成果物を無断破棄しないよう、次の方法をB4開始条件として固定する。

**B4実行契約（必須順序）:** B1で固定した隔離sourceの絶対pathを実行cwdに設定してから、その隔離source内の`.\build.ps1`を呼ぶ。`-PythonExe`には使用するPython実行ファイルの絶対pathを渡す。`build.ps1`およびspecの相対`FFmpeg`、`build`、`dist`、spec入力pathは、このcwd内に解決される。repo rootの`build`、`dist`、`MMD_AutoLipTool.exe`には触れない。実際の絶対path値はB1実施時に確定する。B4候補commandは次の2 commandをこの順に別々に実行する形で記録し、今回のB1では実行しない。

```powershell
Set-Location -LiteralPath <absolute-isolated-source>
powershell -ExecutionPolicy Bypass -File .\build.ps1 -PythonExe <absolute-python-exe> -Clean -SmokeLaunch
```

1. B4はリポジトリrootとは別の新規所有pathを作る。標準候補は`C:\tmp\MMD_AutoLipTool_MS27\B4\<run-id>\`とし、`<run-id>`は実施日時または一意な識別子で置き換える。既存の同名pathを再利用しない。
2. `source\`へ、buildに必要なソース、`src/core/whisper_models.json`、assets、`pyproject.toml`、`MMD_AutoLipTool.spec`、`build.ps1`、`FFmpeg\bin`入力、`LICENSE`、`NOTICE`、`THIRD_PARTY_LICENSES.md`等だけを明示一覧に基づいて配置する。
3. `source\build\`、`source\dist\`、`source\dist\MMD_AutoLipTool\`、`source\dist\MMD_AutoLipTool.exe`が、作成した隔離copyの所有物であることを、実行前の絶対path解決と一覧で確認する。rootの同名pathを参照しない。
4. `-Clean`を使う場合、削除対象はその隔離copy内部の`build`、`dist\MMD_AutoLipTool`、`dist\MMD_AutoLipTool.exe`に限定する。canonical pathが隔離rootの外へ出る、reparse point / junction / UNC / remote pathを含む、既存ユーザーdataが混在する場合は実行せずHoldとする。
5. 隔離copyに作成前から存在するbuild / distを削除する必要がある場合、所有者、作成時刻、内容、削除対象の絶対pathを記録し、ユーザーの明示許可が得られるまで`-Clean`を実行しない。許可なしにリポジトリrootや既存distを削除する手順は採用しない。
6. 新規空copyでbuild / distが存在しない場合も、`-Clean`の対象path確認を省略しない。実行するか、空copyのfresh buildとして`-Clean`なしで行うかは、B4個別計画で固定する。どちらの場合もroot成果物へ触れない。
7. build copy、ログ、ZIP組立、ZIP展開、配布確認の各pathを分け、検証起動で生成されたruntime JSON / INIや`models`をZIP組立pathへ戻さない。B1ではこれらを作成しない。

この手順は、`build.ps1`のroot固定参照を変更する提案ではない。B4で実行するcwdと入力copyを隔離し、既存rootへの破壊的副作用を避けるための運用条件である。

### 8.5 配布確認環境

B1は配布確認を実行しないが、B5が使う環境を次の条件で固定する。

- ZIP組立path、展開path、実行pathは、リポジトリroot、開発用`.venv`、既存`dist`、既存runtime dataと別の新規pathとする。
- 展開直後のpathには、ZIPに許可したfileだけを置く。起動後に生成された`presets.json`、`profiles.json`、`MMD_AutoLipTool.ini`、`models`等は検証pathに留め、ZIPへ再取り込みしない。
- 配布起動の確認は、開発repoの`src`、Python import path、repo外のPATH上FFmpeg、既存Whisper weightsに偶然依存しない状態で行う。
- Whisper model weightsは配布候補へ入れない。モデル未配置の状態で起動案内・候補表示・解析時no-download境界を確認する場合も、B1では起動せず、B5が隔離環境で行う。
- `sample/`、受入音声、TEXT、PMX / PMD、MMD実行ファイル、生成VMD / WAV / reportは、配布候補の入力・出力へ混ぜない。
- ZIPの必須5ファイルは、`MMD_AutoLipTool.exe`、`readme_mmdautolip.txt`、`LICENSE`、`NOTICE`、`THIRD_PARTY_LICENSES.md`。G-LICENSEで確定した追加license texts / notices / 対応物があれば、その配置をB3で固定する。

## 9. 詳細ステップ

### B1-01: live Git / HEAD / tree baselineの固定

**責務:** B1開始時点の作業対象とMS26引継ぎ基準を、実施時のlive状態へ束縛する。

**実施内容:**

1. 対象cwdを確認する。
2. `git status --short --branch`でbranchと変更・未追跡一覧を取得する。
3. `git branch --show-current`でbranch名を取得する。
4. `git rev-parse HEAD`で完全HEADを取得し、短縮値とcommit titleを記録する。
5. `git log --oneline -n 10`で直近履歴を確認し、`2151d7b Document MS26 Closeout A`との関係を記録する。
6. upstream参照を読み取り、未設定なら未設定として記録する。remote操作、fetch、push、mergeは行わない。
7. code、test、build、runtime、外部素材に関する想定外変更があれば、既存変更を保護したままB1をHoldとする。

**成果物:** B1 baseline表、実行HEAD、branch / upstream / treeの記録、MS26基準commitとの対応。

**受入条件:** B1の全証拠が同一の実行HEADとworking tree状態へ結び付いている。ユーザー提示の開始時証拠と実施時live結果が異なる場合、その差分、所有者、影響、次の判断が記録されている。

**今回の状態:** この計画作成では上記Git commandを実行していない。ユーザー提示のHEAD、branch、upstream、working treeを計画上の開始証拠として区別して記載する。

### B1-02: 現行資料・コード境界・過去証拠の照合

**責務:** MS27 Block Breakdownと指定資料を現行の版数・配布・build境界へ対応付ける。

**実施内容:**

1. Roadmap §13.5のMS26 CloseOut Aと§14のMS27責務を確認する。
2. Indexの最終MS26記録と途中のPending / deferred記録を分け、現在のMS27開始条件を記録する。
3. MS27 Block Breakdownの`1.0.0` version table、B1〜B6 ownership、G-LICENSE、G-ARTIFACT、G-PACKAGE、Pass / Holdを本計画へ対応付ける。
4. README、配布用readme、Release Package Manifest、NOTICE、THIRD_PARTY_LICENSESの現行説明と未確定事項を照合する。
5. `pyproject.toml`、`src/app_version.py`、`src/gui_wx/app.py`、`tests/test_app_version.py`、`build.ps1`、specの責務を読み取り、B1が変更しない境界を記録する。
6. 過去のtest totals、FFmpeg version、PySide6 xref、静的package auditを履歴証拠として扱い、B1のlive passへ転用しない。

**成果物:** 資料対応表、現行 / 履歴 / 未確認の分類、B2以降の参照範囲。

**受入条件:** MS26 CloseOut A、MS27 package検証、過去証拠、今回未実施の作業が文書上で混同されていない。

### B1-03: `1.0.0` version gateの固定

**責務:** 正式版数を確定値として記録し、B2の更新対象と直接テストを固定する。

**実施内容:**

1. version tableへ正式版数`1.0.0`を記録する。
2. project versionの現行値`0.4.0.0`を変更前値として記録する。
3. `pyproject.toml`、アプリ表示`Ver. 1.0.0`、README、配布用readme、ZIP名を更新対象として対応付ける。
4. `src/app_version.py`のinstalled metadata優先・TOML fallbackをB2の確認対象とし、B1では変更しない。
5. `tests/test_app_version.py`の実project version期待値更新をB2の直接テスト作業として固定する。`0.3.8.0`等のmock値、履歴、fixture、第三者依存versionを一括変更対象にしない。
6. Windows FileVersion / ProductVersionとも正式版数`1.0.0`に設定するユーザー決定を記録する。実際のspec/version resource反映方法はB2が決定・反映し、B4が最終exeで検証する。B1は設定済み・検証済みとは記録しない。

**成果物:** `1.0.0` version table、更新対象分類、B2開始条件、B2実装・B4検証へのhandoff。

**受入条件:** 正式版数の値が`1.0.0`で固定され、Windows FileVersion / ProductVersionとも`1.0.0`に設定する要件、B2のspec/version resource実装方法決定・反映、B4の最終exe検証の責務が明記されている。B2がコード・文書・直接テストを所有し、B1が版数やversion resourceを実際に反映・検証したとは記録しない。

**Hold条件:** B2がspec/version resourceの実装方法を決定できない場合はB2の版数反映をHoldとし、B4が最終exeのFileVersion / ProductVersionを確認できない場合はB4のG-VERSION検証をHoldとする。正式版数と設定要件は確定済みであり、反映未実施・最終artifact未確認を設定済み・検証済みとは記録しない。

### B1-04: Windows / Python / PyInstaller / hooks / dependency環境表の固定

**責務:** B4のbuild・SmokeLaunchとB5の配布確認が、どの環境で行われたかを追跡できる状態にする。

**実施内容:**

1. Windows 11のedition、version、build、architectureを記録する。
2. 使用Python executableの絶対path、version、architecture、`sys.executable`を記録する。
3. PyInstallerと`pyinstaller-hooks-contrib`の実解決versionを取得し、`requirements.txt`の宣言値と比較する。
4. `pyproject.toml`の5件のdirect dependencyと、実環境のinstalled metadataを対応付ける。
5. tiktoken、tiktoken_ext、pyopenjtalk data / DLL、matplotlib backendなどの推移・native要素を、実環境またはB4 Analysis資料で確認する責任を明示する。
6. version差分がある場合は、B2の版数更新と第三者依存versionの変更を分離し、依存を黙って更新しない。

**成果物:** 実環境表、宣言 / 実解決差分表、B3 / B4へのhandoff。

**受入条件:** 実値未取得の項目が`未確認`として列挙され、設定値を実環境値として扱っていない。依存追加・更新はB1の成果物に含めない。

### B1-05: FFmpeg / build入力とlicense確認状態の固定

**責務:** B4が使うbinary入力と、B3が解決すべきlicense不足を分けて記録する。

**実施内容:**

1. `FFmpeg\bin`の通常ファイル一覧を取得し、`ffmpeg.exe`、`ffprobe.exe`、`ffplay.exe`、DLLのpath、size、SHA-256を記録する。
2. 実binaryのversionとconfigurationを取得し、過去の`N-123549-g70537ec8e6-20260318`等とは別欄に記録する。
3. `MMD_AutoLipTool.spec`が収集する入力と、`build.ps1`が存在を要求する`ffmpeg.exe` / `ffprobe.exe`を比較する。
4. `LICENSE`、`NOTICE`、`THIRD_PARTY_LICENSES.md`、FFmpeg配布元原本、適用されるGPL / version3本文、必要な通知・対応物の確認状態を記録する。
5. 正確なFFmpeg license原本、binaryとの対応、再配布条件、必要な文書が確認できない場合は、B3のG-LICENSEをHoldとしてhandoffする。

**成果物:** FFmpeg/build入力台帳、binary hash、license確認状態、G-LICENSE handoff。

**受入条件:** 現行FFmpeg license原本と最終artifactが未確認である事実が保持され、未確認をPassとして扱っていない。FFmpegの差し替えやlicense文書の作成はB1で行わない。

### B1-06: build / log / ZIP pathと破壊的操作境界の固定

**責務:** B4 / B5が既存root成果物を破壊せず、各証拠を混ぜずに保存できる作業領域を定める。

**実施内容:**

1. `C:\tmp\MMD_AutoLipTool_MS27\B4\<run-id>\`を一時作業copyの候補として記録する。
2. `source\`、`evidence\`、`zip-input\`、`zip-extracted\`、`distribution-run\`を用途別に分離する。B4の実行cwdは`source`の絶対pathとし、B1ではpathを作成しない。
3. source copyへ入れる許可一覧と、入れてはならないruntime / user data一覧を固定する。
4. `build.ps1 -Clean`の削除対象が隔離copy内だけであること、canonical pathがroot外へ出ないこと、reparse point / junction / UNC / remote pathがないことをB4開始条件とする。B4は`-PythonExe`へ使用Python実行ファイルの絶対pathを渡し、相対`FFmpeg`、`build`、`dist`、spec入力pathを隔離source cwd内へ解決する。repo rootのbuild / dist / exeは対象にしない。
5. 隔離copyに既存のbuild / distがある場合は、所有・作成時刻・内容を記録し、明示許可なしに削除しない。rootの`build` / `dist` / exeを削除する手順は採用しない。
6. buildログ、PyInstaller warn / xref / TOC、exe hash、ZIP hash、配布起動ログを別pathへ保存する。検証ログやruntime生成物をZIPへ混入させない。

**成果物:** path ownership表、許可入力一覧、除外一覧、B4 / B5開始条件。

**受入条件:** root成果物を対象とする削除手順がなく、削除対象・所有者・許可条件・停止条件が具体化されている。B4の実行cwdが隔離sourceの絶対path、`-PythonExe`が使用Python実行ファイルの絶対pathであり、相対pathの解決先が隔離source内、repo root非接触であることを開始条件・handoffへ記録できる。B1は一時copyや成果物を作成していない。

### B1-07: 配布確認環境と同梱 / 除外境界の固定

**責務:** B5が、開発環境に偶然依存しない配布候補を確認できる条件を定める。

**実施内容:**

1. 配布確認用の新規展開pathと、開発repo / `.venv` / PATH上FFmpegからの独立条件を記録する。
2. ZIP外側の必須5ファイルと、G-LICENSEで追加確定する第三者文書の位置を固定する。
3. onefile内部で確認するFFmpeg / DLL、Whisper manifest、package assets、license文書、pyproject、icon / splash等の対象を記録する。
4. `small.pt`、`medium.pt`、`large-v3-turbo.pt`等のWhisper weights、runtime `presets.json` / `profiles.json` / `MMD_AutoLipTool.ini`、`models`、`sample`、検証素材、開発用source / tests / docsを除外対象として固定する。
5. `PySide6`、`shiboken`、Qt関連moduleがAnalysisまたは最終exeに現れた場合は、B4が必要性、version、license、サイズ、除外可否を確認するHold条件を記録する。

**成果物:** G-PACKAGE入力・除外表、配布確認環境表、B5開始条件。

**受入条件:** weights、runtime JSON / INI、models、sampleを同梱しない境界が明記され、B1が実ZIPや実artifactを確認済みと記録していない。

### B1-08: common evidence ledgerとB2〜B6 handoffの固定

**責務:** 各Blockの証拠を同じcandidateへ結び付け、変更後の再検証を判断できるledgerを定める。

**実施内容:**

1. §15のledger schemaとID規則を採用する。
2. B1 baseline、version table、環境表、FFmpeg台帳、隔離path表をB1所有行として登録する。
3. B2〜B6のowner、依存、成果物、受入条件、開始条件、Hold伝播条件を§16へ登録する。
4. HEAD、source / input hash、実環境、exe hash、ZIP hashを証拠単位として固定する。
5. version、code、dependency、FFmpeg、spec、license、artifact、ZIPの変更ごとの失効範囲を記録する。

**成果物:** common evidence ledger schema、B1初期行、Block handoff matrix、失効規則。

**受入条件:** B2〜B6がB1の結果をどの条件で利用できるか、どの変更で再取得するかが判断可能である。B1自身の未実行事項は未実行のまま記録される。

## 10. 状態遷移 / データ契約

### 10.1 B1からB6への状態遷移

```text
MS26 CloseOut A
    |
    v
B1 baseline / version / environment / isolation fixed
    |-- unresolved required decision or unsafe path --> Hold
    v
B2 1.0.0 code / document / version resource update / direct test
    |
    v
B3 dependency / FFmpeg / license / package manifest gate
    |-- missing exact license or redistribution evidence --> Hold
    v
B4 isolated onefile build / SmokeLaunch / final artifact inspection
    |-- artifact mismatch, PySide6 unresolved, nonzero process --> Hold
    v
B5 ZIP / extraction / distribution environment gate
    |-- required file missing, excluded data included, runtime failure --> Hold
    v
B6 final evidence / document sync / Pass or Hold
```

B1のPassはMS27全体のPassではない。B1は、`1.0.0`の決定、live baseline、環境表、入力・path・ledger・ownerを固定した状態を意味する。B2以降の反映・build・ZIP・license・artifactの成功は、対応するBlockで別に証明する。

### 10.2 共通candidate identity

各証拠は、次の組み合わせを保持する。

- 実行HEADとbranch、working treeの対象差分
- source / build input / FFmpeg / license文書のpath、size、SHA-256
- Python executable、OS、PyInstaller、hooks、実解決dependencyのversion
- build時のspec、build script、実行cwd、隔離path
- exeのpath、size、SHA-256、Analysis / archive一覧
- ZIPのpath、size、SHA-256、内容一覧、展開先一覧
- 実施者、実施日時、単独command、期待結果、実結果、process exit code

履歴のcommit ID、過去のtest total、過去のFFmpeg version、ユーザー報告だけでは、新しいcandidateのidentityを構成しない。

### 10.3 証拠失効

- HEADが変わり、runtime code、test、dependency、pyproject、spec、build script、FFmpeg、license、package dataに影響する差分がある場合、影響するB1〜B6の証拠をstaleとする。
- `pyproject.toml`、`src/app_version.py`、表示経路、版数文書、package manifestの変更は、B2 version証拠を更新し、exeとZIPを再作成・再確認する条件とする。
- FFmpeg binary、DLL、build configuration、license本文、NOTICE、THIRD_PARTY_LICENSES、同梱許可一覧の変更は、B3 G-LICENSE、B4 artifact、B5 ZIP、B6判定をstaleとする。
- spec、build script、PyInstaller、hooks、依存環境の変更は、B4 build / Analysis / SmokeLaunchとB5配布確認を更新する。
- exeのhashが変わった場合、B5 ZIPとB6最終判定を更新する。ZIP外側のreadme / licenseだけが変わった場合もZIP hashはstaleとする。
- runtime JSON / INI、model weights、sample、ユーザー素材がsource copyやZIP組立pathへ混入した場合、candidateを破棄して隔離pathを作り直す。既存rootやユーザーdataを削除して修復しない。
- 説明だけのB1計画文書変更は、candidate bytesに影響しないことを確認してledgerへ理由を記録する。ただし、対象file・受入条件・gateの意味を変えた場合は関連Blockの計画を再照合する。

## 11. テスト・検証方針

### 11.1 B1の検証境界

B1は、コード・テスト・build・SmokeLaunch・ZIP・runtime JSON / INI・外部素材・実MMDを実施しない。B1で行う確認は、既存資料・コード・設定の読み取りと、実施時に取得すべきbaseline / environment / input情報の定義に限る。

| 操作 | B1での扱い | 所有Block |
| --- | --- | --- |
| Git live baseline | B1実施時に読み取りcommandを単独実行し、exit codeを記録 | B1 |
| project / app version反映 | 実施しない。`1.0.0`をversion tableへ記録するだけ | B2 |
| direct version test | 実施しない | B2 |
| PyInstaller onefile build | 実施しない | B4 |
| SmokeLaunch | 実施しない | B4 |
| PySide6最終artifact確認 | 実施しない | B4 |
| ZIP作成 / 展開 | 実施しない | B5 |
| runtime JSON / INI / models | 読み取り・コピー・編集・生成をしない | B5の隔離環境確認対象 |
| 外部素材 / 実MMD | 実施しない。MS26 CloseOut Aを再判定しない | MS26の既存記録 |

### 11.2 B1実施時のcommand記録候補

以下はB1実施時に単独で使う候補であり、計画作成時点では実行していなかった。2026-09-13のB1実施結果は§15.4へ記録する。B1実施者は一つのcommandを実行し、結果と終了を確認してから次へ進む。未実行のcommandへ`0`を記入しない。

| ID | 目的 | command例 | 記録 |
| --- | --- | --- | --- |
| MS27-B1-C01 | cwd | `Get-Location` | path、日時、exit code |
| MS27-B1-C02 | tree / branch | `git status --short --branch` | branch、modified、untracked、exit code |
| MS27-B1-C03 | branch | `git branch --show-current` | branch、exit code |
| MS27-B1-C04 | HEAD | `git rev-parse HEAD` | full HEAD、exit code |
| MS27-B1-C05 | recent history | `git log --oneline -n 10` | commit title、exit code |
| MS27-B1-C06 | upstream | `git rev-parse --abbrev-ref --symbolic-full-name "@{u}"` | configured / unset、exit code、エラーの意味 |
| MS27-B1-C07 | Python | `.\.venv\Scripts\python.exe --version` | absolute path、version、architecture、exit code |
| MS27-B1-C08 | PyInstaller | `.\.venv\Scripts\python.exe -m PyInstaller --version` | version、exit code |
| MS27-B1-C09 | FFmpeg | `.\FFmpeg\bin\ffmpeg.exe -version` | version、configuration、exit code |
| MS27-B1-C10 | ffprobe | `.\FFmpeg\bin\ffprobe.exe -version` | version、configuration、exit code |
| MS27-B1-C11 | input inventory | `Get-ChildItem -LiteralPath FFmpeg\bin -File` | file list、size、exit code |
| MS27-B1-C12 | input hash | `Get-FileHash -LiteralPath <one-input-file> -Algorithm SHA256` | file、hash、exit code。対象ごとに別ID |

Python / PyInstaller / FFmpeg commandはversionとconfigurationの読み取りであり、buildやテストの実行ではない。計画作成時点では未実行だったが、B1実施時に実行した結果と失敗codeは§15.4へ記録する。commandが失敗した場合は、失敗codeと原因を記録し、必要な環境値が欠けるBlockをHoldとする。

### 11.3 process exit codeの記録

各commandは次の形式で記録する。

```text
Evidence ID:
Command ID:
実行日時 / 実施者:
実行HEAD / branch / working tree:
cwd:
単独で実行したcommand:
期待結果:
実結果:
process exit code:
stdout / stderrの保存先:
失敗・skip・未取得の理由:
次のBlock / 次の確認:
```

- processの成功表示やPowerShell cmdletの成功だけで`0`を推定しない。
- upstream未設定の確認など、想定された非ゼロ終了は、commandの意味とstderrを記録したうえで「未設定」と判定する。成功したGit状態を捏造しない。
- `Get-FileHash`や資料照合にprocess exit codeがない場合は`N/A（照合）`と記録する。
- B1のユーザー決定`1.0.0`は`N/A（ユーザー決定）`であり、commandの`0`ではない。
- B2の直接test、B4のbuild / SmokeLaunch、B5のZIP / 配布起動は、各Blockのrunnerとprocess exit codeを個別に記録する。

## 12. 受け入れ条件

### 12.1 B1受入条件

| ID | 条件 | 状態の意味 |
| --- | --- | --- |
| MS27-B1-AC01 | B1実施時のlive branch、HEAD、working tree、upstream、MS26基準commitが記録されている | 過去のGit snapshotではなく実施時baselineへ束縛済み |
| MS27-B1-AC02 | MS26 CloseOut AとMS27 package / release readinessの責務、MS26 actual-MMD再判定除外が記録されている | MS26の受入とMS27のpackage gateが分離済み |
| MS27-B1-AC03 | 正式版数`1.0.0`、現行`0.4.0.0`、更新対象、保持する履歴・fixture・第三者versionがversion tableへ記録されている | B2が版数反映へ進める基準が固定済み |
| MS27-B1-AC04 | B2が`1.0.0`のコード・文書更新と`tests/test_app_version.py`の直接テストを所有することが明記されている | B1がB2作業を先取りしていない |
| MS27-B1-AC05 | Windows / Python / PyInstaller / hooks / direct・transitive dependencyの宣言値・実値・未確認が分離されている | B3 / B4の環境再現性が追跡可能 |
| MS27-B1-AC06 | FFmpeg / ffprobe / ffplay / DLLのbuild入力、version、configuration、hash、license原本の確認状態が記録されている | FFmpeg license不足を推測でPassにしていない |
| MS27-B1-AC07 | build copy、build / dist、ログ、ZIP、展開、配布確認pathと所有範囲が固定され、B4の実行cwdが隔離sourceの絶対path、`-PythonExe`が絶対path、相対pathが隔離source内に解決され、root成果物を削除する手順がない | B4 / B5が既存rootを破壊しない |
| MS27-B1-AC08 | weights、runtime JSON / INI、models、sample、外部素材の非同梱境界と、PySide6最終artifact確認のownerが明記されている | G-ARTIFACT / G-PACKAGEの開始条件が固定済み |
| MS27-B1-AC09 | common evidence ledger、process exit code、artifact hash、stale / rerun規則が定義されている | B2〜B6の証拠を同一candidateへ追跡可能 |
| MS27-B1-AC10 | B2〜B6の責務、依存、成果物、開始条件、Hold伝播条件が記録されている | 後続BlockがB1結果を誤って再利用しない |
| MS27-B1-AC11 | Windows FileVersion / ProductVersionとも正式版数`1.0.0`に設定するユーザー決定、B2のspec/version resource実装方法決定、B4の最終exe検証責務が記録されている | 設定要件は確定済みだが、実際の反映・最終artifact検証を済みとは扱わない |
| MS27-B1-AC12 | B1がコード、テスト、build、SmokeLaunch、ZIP、runtime、外部素材、実MMDを実施していないことが明記されている | B1の証拠範囲が過大化されていない |

### 12.2 B1判定

- **Pass:** AC01〜AC12を満たし、実施時baseline、`1.0.0` version table、Windows FileVersion / ProductVersionの確定要件とB2実装・B4検証handoff、環境表、FFmpeg入力状態、隔離path、ledgerが揃っている。FFmpeg license原本やfinal artifactの未確認は、B3 / B4 / B5のHold条件として正しく引き継がれていれば、B1の事実記録を妨げない。
- **Hold:** live baselineが取得できない、想定外の既存変更を保護できない、`1.0.0`の記録対象またはversion resourceの実装・検証境界が不明、root成果物を削除しない隔離方法が確保できない、または記録が過去証拠に依存している。

B1 Passは、B2の直接test、B3のlicense、B4のbuild / SmokeLaunch / artifact、B5のZIP / 配布確認、B6のMS27 Passを意味しない。

## 13. リスクと対策

| リスク | 影響 | 対策 / Hold条件 |
| --- | --- | --- |
| rootの`build.ps1 -Clean`が既存build / dist / exeを削除する | ユーザー成果物を破棄する | rootでは実行しない。隔離sourceの絶対pathをcwdへ設定し、`-PythonExe`へ絶対pathを渡してから隔離source内の`.\build.ps1`を呼ぶ。canonical path検査、所有範囲記録、必要時の明示許可を必須にする |
| installed metadataが古い版数を優先する | sourceとfrozen表示が`1.0.0`にならない | B1は経路を記録し、B2が必要なコード / metadata対策と直接testを所有。解決しない候補はHold |
| `pyproject`の宣言依存だけでpackage内容を判断する | 未知の推移依存・native DLL・licenseが漏れる | 実解決依存、Analysis TOC、final artifactをB3 / B4で照合 |
| FFmpegのGPL / version3構成と正確なlicense原本が対応しない | 再配布条件の確認不足 | G-LICENSEをHold。概要文書や過去記録で代替しない |
| PySide6がAnalysisへ現れたが、最終exe内部を確認しない | 不要module・license notice不足を見逃す | B4がwarn / xref / TOCと内部archiveを確認。必要性・license不明ならHold |
| runtime JSON / INI、models、weights、sampleがZIPへ混入する | 個人設定・大容量weights・未許諾素材を配布する | source copy / ZIP inputを許可一覧から組み立て、展開後生成物を再圧縮しない |
| 過去のtest / static auditを現行Passへ転用する | 未実施のbuild・artifact確認を済みと誤認する | evidence ID、HEAD、入力hash、実行日時、exit codeを必須にする |
| 計画作成後にHEADや対象差分が変わる | 証拠が別candidateへ紐付く | B1開始時に再取得し、影響するledger行をstaleにする |
| Windows FileVersion / ProductVersionの確定要件をB2が実装方法へ落とさず、B4が最終exeを確認しない | 正式版数とWindows version resourceが不一致になる | 要件は`1.0.0`として確定済みと記録し、B2がspec/version resourceの実装方法を決定・反映、B4が最終exeの値を検証する。未実施・未確認は設定済み・検証済みと扱わない |

## 14. Codex実施時の注意

- 今回は本文書だけを作成し、他の文書、コード、テスト、build設定、runtime data、外部素材を変更しない。
- 計画作成時点ではlive Git command、Python、PyInstaller、FFmpegを実行していなかった。B1実施では読み取り専用のGit、Python version / metadata、PyInstaller version、FFmpeg version / inventory / hashを実行し、結果を§15.4へ記録した。pytest、compileall、build、SmokeLaunch、ZIP、GUI、実MMDは引き続き実行していない。実行していないcommandを成功扱いしない。
- B1の実施時も、Gitは読み取り専用baselineに限る。stage、commit、branch変更、merge、push、tag、releaseを行わない。
- B1はサブエージェントを起動しない。最終的なbaseline、owner、Hold、Passの判断はメインエージェントが行う。
- B1で既存変更を見つけても、restore、reset、clean、削除、上書きを行わない。想定外変更は所有者と影響を記録してHoldまたはユーザー確認候補とする。
- B4の実行cwdが隔離sourceの絶対pathでない、`-PythonExe`が絶対pathでない、相対pathが隔離source内へ解決されない、または対象pathが一時copyの所有範囲から外れる場合は、実行を停止する。root成果物の削除で問題を解消しない。
- runtime `presets.json`、`profiles.json`、`MMD_AutoLipTool.ini`、Whisper model weights、sample、外部素材を確認用にコピーしない。必要なB5検証は隔離された空の配布pathで行う。
- MS26 actual-MMDの結果をMS27の再受入結果として表現しない。MS26のユーザー報告、Codexのread-only確認、未確認事項を分けて記録する。
- 正確なFFmpeg license原本、PySide6最終混入、最終exe、ZIPのいずれも今回確認済みとは記載しない。不足はB3〜B5のHoldとして渡す。
- process exit codeはcommand単位で記録する。`N/A（ユーザー決定）`、`not run`、`unknown`、実際の数値を混同しない。

## 15. Evidence ledger / 実施境界

### 15.1 ID規則

- B1 command: `MS27-B1-Cxx`
- B1 manual / environment observation: `MS27-B1-Mxx`
- B1 finding / Hold: `MS27-B1-Fxx`
- Block handoff: `MS27-B1-Hxx`
- B2〜B6の証拠IDは各個別計画で同じ規則を継承し、同一IDを再利用しない。
- 再試行は新しいIDを付け、初回失敗を削除しない。

### 15.2 Ledger schema

| 列 | 内容 |
| --- | --- |
| Evidence ID | command、manual、finding、handoffの一意ID |
| Owner / Block | B1〜B6の責任Block、実施者 |
| Gate / AC | G-VERSION、G-LICENSE、G-ARTIFACT、G-PACKAGE、受入条件ID |
| Fact / Plan / User report | 確認済み事実、計画、ユーザー報告の区別 |
| Timestamp | 実施日時。今回未実施は`not run` |
| HEAD / branch / tree | 実行HEAD、branch、対象差分、working tree |
| Environment | OS、Python、PyInstaller、hooks、dependency、FFmpeg |
| Input identity | source、binary、license、spec、scriptのpath / size / SHA-256 |
| Command / Operation | 単独commandまたは手動操作 |
| Expected / Actual | 期待結果と実結果 |
| Counts | pass、skip、failure、error、対象file数 |
| Process exit code | 数値、`N/A（照合）`、`not run`、`unknown`と理由 |
| Artifact identity | exe / ZIP /文書のpath、size、SHA-256 |
| Status | Pass、Hold、not run、stale |
| Finding / Next action | 問題、Hold条件、次のowner、再試行 |
| Invalidation | 失効条件、失効したEvidence ID、再実行ID |

### 15.3 B1初期ledgerの扱い

作成前にユーザーから提示されたHEAD、branch、upstream、working tree、project version等は、`Fact = User-provided current evidence`として参照できるが、B1 commandのexit codeを持つ実施証拠ではない。B1実施後は、次のplanned rowと§15.4へ実行結果を追加する。

| Planned row | 所有 | 内容 | 今回の状態 |
| --- | --- | --- | --- |
| `MS27-B1-C01`〜`C06` | B1 | cwd、Git、HEAD、history、upstream | 実施済み。`C06`はupstream未設定の終了コード1 |
| `MS27-B1-C07`〜`C11` | B1 | Python、PyInstaller、FFmpeg、input inventory | 実施済み。各終了コード0 |
| `MS27-B1-C12`〜`C21` | B1 | FFmpeg各入力のSHA-256 | 実施済み。各終了コード0 |
| `MS27-B1-C22` | B1 | 初回package metadata probe | 終了コード1。`tiktoken_ext`にdistribution metadataがないため、原因を記録 |
| `MS27-B1-C23` | B1 | package metadata / module spec再取得 | 実施済み。終了コード0 |
| `MS27-B1-C24`〜`C27` | B1 | OS identityの標準情報源 | 部分取得。`C25` / `C27`はアクセス拒否、標準情報源だけではidentity未確定 |
| `MS27-B1-C28`〜`C30` | B1 | FFmpeg追跡状態、lock候補、MS26 CloseOut A以降の差分 | 実施済み。各終了コード0 |
| `MS27-B1-C31`〜`C32` | B1 | 管理者権限CIMによるOS identity再確認 | 実施済み。各終了コード0。Windows 11 Pro / 64bitを確認 |
| `MS27-B1-M01` | B1 | `1.0.0` version tableとB2 handoff | plan only。ユーザー決定は`N/A（ユーザー決定）` |
| `MS27-B1-M02` | B1 | build copy / path ownership / B4 cwd・PythonExe絶対path契約判定 | 契約確認済み。隔離copyは未作成、実際のB4絶対pathは未確定 |
| `MS27-B1-M03` | B1 | Windows FileVersion / ProductVersionとも`1.0.0`に設定するユーザー決定とB2 / B4 handoff | 設定要件はユーザー決定として確定。B2のspec/version resource反映とB4の最終exe検証は未実施 |
| `MS27-B1-H01` | B1 | B2〜B6 owner、依存、開始条件 | 本計画の§16へ記録済み。後続Blockの実施結果は未取得 |

### 15.4 B1実施済みevidence ledger

以下は2026-09-13にメインエージェントがB1として実行した、単独commandごとの記録である。B1の実施は読み取り専用であり、`C06`、`C22`、`C25`、`C27`は非zeroまたは部分取得の理由を保持する。`C24`の終了コード0は、Windows 11 identityが確定したことを意味しない。

| Evidence ID | Command / operation | Actual result | Process exit code | Status |
| --- | --- | --- | ---: | --- |
| `MS27-B1-C01` | `Get-Location` | repository rootを確認 | 0 | Pass |
| `MS27-B1-C02` | `git status --short --branch` | `feature/MS27-implementation`、clean | 0 | Pass |
| `MS27-B1-C03` | `git branch --show-current` | `feature/MS27-implementation` | 0 | Pass |
| `MS27-B1-C04` | `git rev-parse HEAD` | `90edd81601465cff683b8bca6f710f1386a18877` | 0 | Pass |
| `MS27-B1-C05` | `git log --oneline -n 10` | top commit `90edd81 Document MS27 implementation plans` | 0 | Pass |
| `MS27-B1-C06` | `git rev-parse --abbrev-ref --symbolic-full-name "@{u}"` | upstream未設定 | 1 | Hold / expected unset |
| `MS27-B1-C07` | `.\\.venv\\Scripts\\python.exe --version` | Python `3.14.3` | 0 | Pass |
| `MS27-B1-C08` | `.\\.venv\\Scripts\\python.exe -m PyInstaller --version` | PyInstaller `6.19.0` | 0 | Pass |
| `MS27-B1-C09` | `.\\FFmpeg\\bin\\ffmpeg.exe -version` | `N-123549-g70537ec8e6-20260318`、GPL / version3等のconfiguration | 0 | Pass / license別gate |
| `MS27-B1-C10` | `.\\FFmpeg\\bin\\ffprobe.exe -version` | `N-123549-g70537ec8e6-20260318`、C09と同じconfiguration | 0 | Pass / license別gate |
| `MS27-B1-C11` | `Get-ChildItem -LiteralPath FFmpeg\\bin -File` | `.gitkeep`と10 binary / DLL | 0 | Pass |
| `MS27-B1-C12`〜`C21` | FFmpeg各10 fileへの`Get-FileHash -Algorithm SHA256` | §8.3のhash表 | 0 | Pass |
| `MS27-B1-C22` | Python package metadata probe | `tiktoken_ext`をdistributionとして取得できず、部分出力後に例外 | 1 | Finding |
| `MS27-B1-C23` | 修正したpackage metadata / module spec probe | direct dependency実値、`tiktoken 0.14.0`、`tiktoken_ext` namespace、`pyopenjtalk`実体を確認 | 0 | Pass |
| `MS27-B1-C24` | `Get-ComputerInfo -Property WindowsProductName,WindowsVersion,OsBuildNumber,OsArchitecture` | `Windows 10 Pro / 2009`、build / architecture空欄 | 0 | Hold |
| `MS27-B1-C25` | `Get-CimInstance Win32_OperatingSystem` | アクセス拒否 | 1 | Hold |
| `MS27-B1-C26` | Windows registry `CurrentVersion` read | ProductName `Windows 10 Pro`、CurrentBuild `26200`、DisplayVersion `25H2` | 0 | Evidence / unresolved |
| `MS27-B1-C27` | `systeminfo` | アクセス拒否 | 1 | Hold |
| `MS27-B1-C28` | `git ls-files FFmpeg/bin` | FFmpeg 11 entriesがGit追跡対象 | 0 | Pass |
| `MS27-B1-C29` | lock候補のfile search | `pyproject.toml` / `requirements.txt`のみ。lock fileなし | 0 | Pass / no lock |
| `MS27-B1-C30` | `git diff --name-status 2151d7b..HEAD` | MS27計画文書2件のみ | 0 | Pass |
| `MS27-B1-C31` | 管理者権限 `Get-CimInstance Win32_OperatingSystem` | Version `10.0.26200`、BuildNumber `26200` | 0 | Pass |
| `MS27-B1-C32` | 管理者権限 `Get-CimInstance -ClassName Win32_OperatingSystem -Property Caption,Version,BuildNumber,OSArchitecture` | `Microsoft Windows 11 Pro`、Version `10.0.26200`、BuildNumber `26200`、`64 ビット` | 0 | Pass |

`MS27-B1-C22`は`tiktoken_ext`のmodule実体がないことを示すものではなく、distribution metadataを持たないnamespace packageへ`metadata.version()`を適用した取得方法の不一致である。`C23`でmodule specとdistributionを分けて再取得した。

## 16. B2〜B6 ownership / dependency / handoff

| Block | 主責務 | 依存・開始条件 | 主成果物 | B1からのHandoff / Hold |
| --- | --- | --- | --- | --- |
| MS27-B1 | live baseline、MS26境界、`1.0.0` version table、実環境表、FFmpeg入力、隔離path、ledger、owner固定 | MS26 CloseOut A、本文書 | baseline、version / environment / path表、ledger schema、handoff | live evidence取得済み。Windows 11 identityを管理者権限の読み取り専用CIMで確認し、B1 Passへ到達。B2以降の実装・検証は未実施 |
| MS27-B2 | `1.0.0`のproject / app version / README / 配布用readme / ZIP規則反映、Windows version resourceの実装方法決定・反映、必要なversion解決コード、直接test | B1 Pass、version table、対象差分が固定 | version差分、旧版分類、`test_app_version`結果、source表示証拠、version resource実装記録 | B1が更新対象を固定。B2がコード・文書・version resource実装・直接testを所有。版数解決または実装方法を確定できない場合はB2 Hold |
| MS27-B3 | 宣言 / 実解決依存、FFmpeg、GPL / version3、正確なlicense、package manifest、同梱許可一覧 | B1 Pass、B2差分、実環境表、FFmpeg入力 | 依存台帳、license原本 / notice、G-LICENSE、package list | license原本・再配布条件・binary対応不足はB3 Hold。B4へPassを渡さない |
| MS27-B4 | 隔離copyでonefile build、SmokeLaunch、warn / xref / TOC、PySide6、内部archive、Windows FileVersion / ProductVersion、resource / weights確認 | B1の実行契約Pass（隔離source cwd絶対path、`-PythonExe`絶対path、root非接触）、B2完了、B3 G-LICENSE Pass、path ownership Pass、必要時の削除許可 | exe、build / smoke記録、内部一覧、exe hash、Windows version resource検証、G-ARTIFACT | cwd / PythonExe / 相対path解決が不明、root path、未許可削除、nonzero process、PySide6 / license不明、FileVersion / ProductVersion不一致、weights混入はB4 Hold |
| MS27-B5 | 許可fileだけのZIP、展開、必須 / 除外、配布環境起動、normal exit、runtime独立性 | B3 package list、B4 exe / G-ARTIFACT Pass | ZIP、展開一覧、ZIP hash、配布確認記録、G-PACKAGE | required file欠落、runtime data / weights / sample混入、開発環境依存はB5 Hold |
| MS27-B6 | 最終candidate、全evidence、文書、未確認、P1 / P2 / P3、Pass / Holdの最終照合 | B1〜B5の最新証拠、staleなし | readiness判定、ledger、必要な文書同期、残課題 / handoff | HoldをPassへ格上げしない。GitHub公開・tag・push・installerへ移行しない |

### 16.1 B1完了からB2開始へのhandoff

B1からB2へ、次の値を渡す。

- 実施時HEAD、branch、working tree、upstreamの状態と、B1 evidence ID
- MS26 CloseOut Aを継承し、actual-MMD再判定をしない境界
- 正式版数`1.0.0`、現行`0.4.0.0`、更新対象、保持対象のversion分類
- `pyproject.toml`、README、配布用readme、`src/app_version.py`、`src/gui_wx/app.py`、`tests/test_app_version.py`のowner境界
- Windows FileVersion / ProductVersionとも`1.0.0`に設定する確定要件、B2のspec/version resource実装方法決定、B4の最終exe検証責務。反映未実施・最終artifact未確認はそのまま引き継ぐ
- B2の直接testで必要なprocess exit code、実行HEAD、旧mock / fixture保持条件

### 16.2 B1からB3〜B6への共通handoff

- 実解決環境表と、未取得項目を推測で埋めない一覧
- FFmpeg入力file、version、configuration、hash、license原本の確認状態
- B4専用隔離copyのpath規則、`build.ps1 -Clean`削除範囲、明示許可条件
- B4実行時は隔離sourceの絶対pathを先にcwdへ設定し、そのcwdの`.\build.ps1`へ`-PythonExe <absolute-python-exe>`を渡す契約。相対FFmpeg / build / dist / spec pathは隔離source内に解決し、repo rootのbuild / dist / exeへ触れない。実際の絶対pathとprocess exit codeはB4で記録する
- ZIP必須5ファイル、weights / runtime JSON / INI / models / sample除外、PySide6確認責任
- common ledgerのID、candidate identity、process exit code、artifact hash、stale規則
- B1ではbuild、SmokeLaunch、ZIP、runtime、外部素材、実MMDを実施していないという証拠境界

## 17. 未確認事項・残課題

| ID | 内容 | 状態 / 解除条件 | 所有 |
| --- | --- | --- | --- |
| MS27-B1-U01 | B1実施時のlive HEAD、branch、working tree、upstreamの再確認 | `90edd81601465cff683b8bca6f710f1386a18877`、`feature/MS27-implementation`、clean、upstream未設定を取得済み。次の影響差分でstale化する | B1 |
| MS27-B1-U02 | B1 / B4で使うWindows、Python、PyInstaller、hooks、実解決依存の値 | Python 3.14.3 / 64bit / AMD64、PyInstaller 6.19.0、hooks 2026.3、direct dependency実値は取得済み。Windows 11 identity、Analysis / native要素は未確定 | B1 / B3 |
| MS27-B1-U03 | 現行FFmpeg binaryのexact version / configuration / hash | 過去記録から推測しない。実入力台帳を取得するまでG-LICENSEは未判定 | B1 / B3 |
| MS27-B1-U04 | FFmpegの正確なlicense原本、GPL / version3本文、copyright、再配布条件、必要通知・対応物 | 不足時はB3 Hold。`NOTICE`や概要だけでPassにしない | B3 |
| MS27-B1-U05 | PySide6 / shiboken / Qtが最終exe内部へ入るか | B4の新しいAnalysis資料と内部archiveが必要。未確認のままPassにしない | B4 |
| MS27-B1-U06 | 最終onefile、ZIP、展開一覧、配布環境の起動・正常終了 | B4 / B5の実行とhashが必要。今回未実施 | B4 / B5 |
| MS27-B1-U07 | `build.ps1 -Clean`を使う際の隔離copy内既存成果物の削除許可 | pathが新規空copyなら削除不要。既存物を削除する場合は所有・対象・明示許可が必要 | B4 |
| MS27-B1-U08 | Windows FileVersion / ProductVersionの実装・最終exe検証結果 | 設定要件はユーザー決定済み`1.0.0`。B2のspec/version resource反映は未実施、B4の最終artifact検証は未確認。設定済み・検証済みとは扱わない | B2 / B4 |
| MS27-B1-U09 | B4実行時の隔離source cwd、`-PythonExe`絶対path、相対path解決、repo root非接触の実行証拠 | B1の実行契約は計画済み。実際の絶対path、cwd、相対path解決、root非接触、process exit codeはB4で記録するまで未確認 | B1 / B4 |
| MS27-B1-U10 | B1実施環境がWindows 11であることの独立確認 | 管理者権限のCIMで`Microsoft Windows 11 Pro`、Version `10.0.26200`、BuildNumber `26200`、`64 ビット`を確認済み。標準照会とregistryの互換表示差は注記として保持 | B1 |

### 17.1 B1実施後の判定

- B1: **実施済み・Pass**。live Git baseline、Python / PyInstaller / dependency、Windows 11 Pro / 64bit、FFmpeg version / configuration / inventory / hash、evidence ledgerを取得した。upstream未設定とFFmpeg license未確認は事実として後続Blockへ引き継ぐ。
- B4実行契約: 隔離source絶対pathをcwdへ設定し、`-PythonExe`へ絶対pathを渡し、相対pathを隔離source内へ解決する計画は固定済み。実際のcwd、PythonExe、path解決、root非接触、process exit codeは未確認。
- G-VERSION: 正式版数とWindows FileVersion / ProductVersionの設定要件は`1.0.0`として確定済み。各対象への反映はB2未実施、最終exeのversion resource検証はB4未確認。
- G-LICENSE: 現行FFmpeg license原本と最終artifactは未確認。B3の判定待ち。
- G-ARTIFACT / G-PACKAGE: onefile、SmokeLaunch、内部archive、ZIP、配布環境は未確認。
- MS26 actual-MMD: MS26 CloseOut Aの既存記録を維持し、MS27-B1では再判定しない。

## 18. 完了条件と報告

### 18.1 B1実施完了

B1は、MS27-B1-AC01〜AC12を満たし、次の記録が揃った場合に完了とする。

- 実施時live Git / HEAD / tree baseline
- MS26 CloseOut Aとの境界記録
- 正式版数`1.0.0`のversion tableとB2 handoff
- Windows / Python / PyInstaller / hooks / dependency実環境表
- FFmpeg/build入力台帳、license確認状態、未確認の明示
- build / log / ZIP / extraction / distribution pathの所有・安全条件
- common evidence ledger、process exit code、hash、stale規則
- B2〜B6のowner、依存、開始条件、Hold伝播
- Windows FileVersion / ProductVersionの確定要件、B2実装方法・B4検証責務、および反映未実施・最終artifact未確認の記録
- B1が実施しなかった操作の記録

未確認のFFmpeg license原本やfinal artifactは、B1の記録上で未確認のまま残す。B1完了を理由にMS27全体をPassとしない。

### 18.1.1 B1実施結果

- 実施者: メインエージェント
- 実施日: 2026-09-13
- 実施範囲: Git baseline、Python / PyInstaller / package metadata、OS情報源、FFmpeg version / inventory / hash、lock候補、隔離build契約の読み取り専用確認
- 変更: 本番コード、テストコード、依存定義、build設定、runtime JSON / INI、外部素材、実MMDは変更・操作していない
- 判定: **Pass**
- OS確認: 標準照会とregistryには`Windows 10 Pro / 2009`という互換表示差があったが、管理者権限のCIM照会で`Microsoft Windows 11 Pro`、Version `10.0.26200`、BuildNumber `26200`、`64 ビット`を確認した（`MS27-B1-C31` / `C32`）。
- 継続可能なhandoff: `1.0.0` version table、B2のversion resource実装責務、B3のFFmpeg license確認、B4の隔離build契約を後続へ渡す。FFmpeg license原本、Analysis、artifact、ZIP、配布環境は引き続き未確認であり、各Blockのgateで判定する。

### 18.2 今回の計画作成完了

計画作成時の作業は、指定された新規ファイルへ本計画を保存し、B1の責務・`1.0.0`版数表・開始条件・隔離build方針・証拠境界・受入条件・未確認事項を記載した時点で完了した。B1実施後の判定と実行結果は§15.4、§17.1、§18.1.1へ追記し、B1のPass / Hold、MS27 Pass、配布公開を混同しない。

## 19. 今回の実施境界

- 変更対象: `docs/Implementation_Plan/MS27-B1_Implementation_Plan.md`のみ。
- 計画内容: MS27-B1の読み取り専用baseline、version、環境、FFmpeg、隔離path、ledger、handoff、Hold条件。
- 実施済み: Git live baseline、Python / PyInstaller version、package metadata、FFmpeg version / configuration / inventory / hash、OS情報源の読み取り。詳細は§15.4。
- 未実施: code変更、test、build、SmokeLaunch、compileall、ZIP、artifact生成、runtime JSON / INI操作、model / sample / 外部素材、実MMD、stage、commit、push、merge、tag、release、installer。
- 版数: 正式版数`1.0.0`を確定値として記載。現行`0.4.0.0`、履歴、fixture、第三者依存versionは変更対象にしない。
- 次工程: B1 Passを基準に、ユーザーの追加承認なしにB2へ自動移行せず、次の明示依頼を受けてB2のspec/version resource実装方法決定・反映へ進む。
