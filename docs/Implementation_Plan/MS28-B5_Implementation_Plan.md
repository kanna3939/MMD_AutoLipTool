# MS28-B5 Implementation Plan

## 1. 文書情報

- Block ID: `MS28-B5`
- 名称: Help / About 実装
- 作成日: 2026-09-21
- 状態: 実装前の計画
- 対象ブランチ: `feature/MS28-B1-implementation`
- 実装開始条件: 本計画の内容確認後、別途実装依頼を受けること
- 版数方針: `1.0.0`を維持し、バージョン表記を変更しない

本計画は、MS13で配置されたまま無効化されている「使い方」「About」メニューを、現行wxPython構成へ接続するための計画である。MS28-B3/B4のデバッグ機構・無音処理契約は変更対象にしない。

## 2. 背景

現行GUIには、次のメニュー項目が存在する。

- `ヘルプ > 使い方(&H)...`
- `ヘルプ > About(&A)...`

これらはMS13-B3でUI骨格として配置され、MS13-B5で`AppController`へのルーティングStubが追加されたが、現在も`update_action_states()`で常時Disabledとなっている。Controller側もステータス表示だけのStubで、実ダイアログ、表示文書、テストは存在しない。

一方、基本操作や現行機能の説明は`README.md`と`readme_mmdautolip.txt`に存在する。B5ではこれらをGUIから参照できるHelp導線と、実行環境の状態を確認できるAbout導線を追加する。

## 3. 目的

1. Helpメニューから、PyInstallerで同梱されるJSON由来の使い方テキストを読み取り専用ポップアップで表示できるようにする。
2. Aboutメニューから、現在のアプリケーションと実行環境の情報を表示できるようにする。
3. Light / Dark / Systemテーマで両ダイアログが視認可能な状態を維持する。
4. EXE実行時にも、ユーザーが別途配置する外部Helpファイルへ依存せず、specで同梱したJSONから使い方テキストを表示できるようにする。
5. Whisper未読み込み、FFmpeg未検出、GPU情報取得不能などの部分的な取得失敗で、About全体を表示不能にしない。

## 4. In Scope

### 4.1 Help

- `assets/usage_guide.json`へHelp表示用の日本語テキストをJSONとして分離する。
- `src/gui_wx/help_about_dialogs.py`で、通常実行時とPyInstaller実行時のresource pathからJSONを読み込む。
- テキストは現行実装に合わせ、次を詳しく説明する。
  - ツールの用途と、どのようなMMD制作場面で使う機能か
  - 読み込み可能なTEXT（UTF-8の`.txt`）、WAV、MP3、M4A
  - 書き出すVMD、MMD用WAV、診断レポート
  - TEXT＋音声入力と音声のみ入力の基本手順
  - 音声のみ入力の書き起こし確認・編集・再解析
  - 波形・母音タイムライン・Previewの確認
  - 開口維持、閉口スムーズの使い方
  - Preview上の母音イベント選択と選択イベント編集
  - Undo / Redo
  - 組み込み／ユーザープリセットの選択・適用・保存
  - モデルプロファイルの選択・適用・プロファイルなしへの復帰
  - Whisperモデルの確認・取得・適用
  - VMD保存、MMD用WAV出力、MMD一括出力
  - デバッグモードの用途と保存先の概要
  - MMD側での最終確認と既存出力保護に関する注意
- 文書の見出しは、少なくとも次を固定する。
  - `基本的な使い方`
  - `開口維持と閉口スムーズ`
  - `選択イベントの操作`
  - `プリセット`
  - `モデルプロファイル`
  - `Whisperモデル`
  - `保存とMMDでの確認`
- Helpダイアログは、JSONから読み込んだテキストをスクロール可能な読み取り専用テキスト領域へ表示する。
- Help表示はユーザーが別途配置する外部文書には依存せず、sourceではリポジトリ内JSON、PyInstallerではspec同梱JSONを使用する。

### 4.2 About

Aboutダイアログには、開いた時点で取得した次の情報を表示する。

- アプリケーションバージョン
- Whisper runtime package version（`whisper`モジュールが既に読み込まれている場合）
- 解決済みFFmpegのversion
- CPU名と論理プロセッサ数
- 物理メモリ総容量
- GPU製品名（複数検出時は重複を除いて表示）
- ダイアログ最下部の作者連絡用リンク: `https://x.com/kanna3939`

表示値が取得できない場合は、空文字や推測値に置き換えず、固定状態値`not_available`または`not_loaded`を表示する。

Aboutは読み取り専用とし、設定変更、モデル取得、音声変換、解析、通常のFFmpeg処理、ネットワーク通信、テレメトリを開始しない。例外として、解決済み`ffmpeg.exe`へのversion問い合わせだけを行う。作者リンクはダイアログ表示時には通信せず、ユーザーがクリックした場合だけ既定ブラウザへの遷移を許可する。

### 4.3 メニュー・状態・テーマ

- `使い方`と`About`を有効化する。
- 解析中、保存中、デリバリー中でも、読み取り専用のHelp/Aboutは開けるようにする。
- 既存の`MainFrame`→`AppController`→`MainFrame`の責務境界を維持する。
- 既存の`ThemeManager`を使い、ダイアログ生成時とテーマ変更後の再表示で現在テーマを適用する。
- ダイアログを閉じた後、親Frame、Busy状態、解析結果、Undo / Redo履歴、設定を変更しない。

## 5. Out of Scope

- バージョン番号の変更、リリース番号の更新、tag、push、公開。
- README全体の書き直し。既存READMEと配布用説明書は維持し、Help表示用の説明はアプリ内部へ埋め込む。
- 設定ダイアログ、ライセンスダイアログ、更新確認、オンラインマニュアル、作者リンク以外の外部URL起動。
- Whisperモデルの自動読み込み、自動取得、再解析。
- GPU名を利用した処理分岐、CUDA設定、性能測定、ベンチマーク。
- FFmpegの自動導入、PATHやINIの変更。
- 新規Python依存の追加。
- MS28-B3/B3B/B3Cのデバッグartifact契約変更。
- MS28-B4/B4Bの`EventSilenceAdmission`、required-zero、Preview/Writer投影契約変更。

## 6. 前提条件

1. 現行GUIはwxPythonであり、旧Qt/PySide6系を再導入しない。
2. アプリバージョンは既存の`resolve_app_version()`を正本として利用し、About専用の版数リテラルを追加しない。
3. Whisper versionは、解析やモデル適用で既に`sys.modules`へ読み込まれている`whisper.__version__`だけを参照する。About表示のためだけにWhisperをimportしない。
4. FFmpegは既存の`locate_ffmpeg_tools()`で解決した`ffmpeg.exe`を使用し、repo-local、PyInstaller同梱、PATHの既存探索順を変更しない。
5. CPU・メモリ・GPUはWindowsのローカル情報だけを取得する。ユーザー入力値や外部サービスは参照しない。
6. GPU情報取得には新規依存を追加しない。`powershell.exe -NoProfile -NonInteractive -Command "Get-CimInstance -ClassName Win32_VideoController | Select-Object -ExpandProperty Name"`という固定CIM照会を使用し、実行ファイルまたは照会が利用できない場合は`not_available`へ収束させる。外部プロセスには既存FFmpeg runnerと同じく`shell=False`および`CREATE_NO_WINDOW`を適用する。
7. FFmpeg versionおよびGPU情報取得はUIスレッドを長時間ブロックしない。About表示は取得中状態を許容し、完了・失敗・キャンセル後に安全に更新する。FFmpeg version問い合わせとGPU照会のtimeoutは各3.0秒、stdout/stderrの保持上限は各64 KiBとする。
8. HelpテキストはJSONへ分離し、source実行ではリポジトリ内のJSON、PyInstaller onefileではspecで同梱されたJSONを、同じresource path解決経路から表示する。

## 7. 対象ファイル

### 7.1 主変更

| 区分 | ファイル | 変更内容 |
| --- | --- | --- |
| 新規 | `docs/Implementation_Plan/MS28-B5_Implementation_Plan.md` | 本計画 |
| 新規 | `src/core/system_info.py` | About表示用の不変snapshotとCPU・メモリ・GPU・Whisper・FFmpeg情報取得 |
| 新規 | `assets/usage_guide.json` | Help表示用の本文を保持するJSONリソース |
| 新規 | `src/gui_wx/help_about_dialogs.py` | JSON由来のHelpテキスト、Help/Aboutダイアログ、テーマ適用、読み取り専用表示 |
| 変更 | `src/gui_wx/main_frame.py` | メニュー有効化、Help/About表示入口、ダイアログの親Frame・テーマ・終了管理 |
| 変更 | `src/gui_wx/app_controller.py` | Help/About要求を実処理へ委譲し、既存Stubを置換 |
| 新規 | `src/gui_wx/system_info_worker.py` | About用system infoの非同期取得、job ID、close後callback破棄 |

`system_info_worker.py`は必須の追加対象とし、workerの責務をAbout用snapshot取得に限定する。Helpテキストは`assets/usage_guide.json`から読み込み、ユーザー編集用の外部ファイルとしては扱わない。

### 7.2 関連確認

- `src/app_version.py`: 既存version resolverを再利用し、変更不要か確認する。
- `src/core/ffmpeg_locator.py`: 既存探索順と未検出状態を維持する。
- `src/gui_wx/theme.py`: 既存paletteをダイアログへ適用する。
- `src/gui_wx/ui_state.py`: 現在テーマとBusy状態を参照する。Help/Aboutのために状態項目を増やさない。
- `MMD_AutoLipTool.spec`: `assets/usage_guide.json`を`assets`配下へ同梱し、不要なdatas追加がないことを確認する。

### 7.3 テスト

- 新規 `tests/test_ms28_b5_system_info.py`: system infoの正常・部分失敗・固定状態値・timeout・重複GPUを検証する。
- 新規 `tests/test_wx_ms28_b5_help_about.py`: menu enable、Controller routing、Help/About表示、読み取り専用、閉じた後の状態保持、テーマ適用を検証する。
- 新規 `tests/test_ms28_b5_usage_document.py`: JSON Help本文の読み込み、必須見出し、対応ファイル形式、用途説明を検証する。
- 既存の関連wxテスト: `tests/helpers.py`のApp/Frame teardown契約を使用する。

## 8. 実装方針

### 8.1 SystemInfoSnapshot

GUIへ直接個別値を渡さず、次のようなimmutableなsnapshotを一度生成して渡す。

```text
SystemInfoSnapshot
  app_version: str
  whisper_version: str
  whisper_status: "loaded" | "not_loaded" | "not_available"
  ffmpeg_version: str
  cpu_name: str
  cpu_logical_count: int | "not_available"
  memory_total_gib: str
  gpu_names: tuple[str, ...]
```

フィールド値は次のように固定する。

| フィールド | 取得成功 | 取得不能・未読込 |
| --- | --- | --- |
| `app_version` | prefixなしの既存resolver生値（例：`1.0.0`） | `not_available` |
| `whisper_version` | `whisper.__version__` | モジュール未読込は`not_loaded`、読込済みで値不正は`not_available` |
| `whisper_status` | `loaded` | `not_loaded`または`not_available` |
| `ffmpeg_version` | version問い合わせから抽出したversion | `not_available` |
| `cpu_name` | CPU名 | `not_available` |
| `cpu_logical_count` | 0より大きい論理プロセッサ数 | `not_available` |
| `memory_total_gib` | `x.x GiB`形式 | `not_available` |
| `gpu_names` | 製品名のtuple | 空または照会不能時は`("not_available",)` |

自由な例外文や環境依存のパスはsnapshotへ入れない。Aboutの表示用snapshotを保存契約・identity・runtime設定・debug artifactへ渡さない。

### 8.2 個別情報の取得契約

- App version: `resolve_app_version()`を使用し、snapshotにはprefixなしのresolver生値（例：`1.0.0`）を保存する。取得不能時は`not_available`とする。Aboutの表示時だけ、`not_available`以外の値へ既存`format_app_version_display()`を一度適用し、`Ver. 1.0.0`の形式で表示する。`not_available`へ`Ver. ?`などの別fallbackを適用しない。
- Whisper: `whisper`が既にロードされている場合だけ`__version__`を検証して表示する。未ロードは`not_loaded`、値不正は`not_available`。
- FFmpeg: `locate_ffmpeg_tools()`で解決した`ffmpeg.path`へ、`-version`だけの固定引数でversion問い合わせを行う。先頭のversion行だけを解析し、未検出・終了コード異常・3.0秒timeout・64 KiB超過・解析不能は`not_available`。
- CPU: `platform.processor()`を優先し、空の場合は`platform.uname().processor`へfallbackする。論理プロセッサ数は`os.cpu_count()`を使用する。
- メモリ: Windowsの物理メモリ総容量を取得し、表示用にGiBへ整形する。取得不能は`not_available`。
- GPU: 上記の固定PowerShell/CIM照会で製品名を取得し、空値・重複を除去する。3.0秒timeout、プロセス起動失敗、64 KiB超過、0件は`("not_available",)`へ収束させる。

外部コマンドを使う場合は、固定 executable、固定引数、`shell=False`、`CREATE_NO_WINDOW`、3.0秒timeout、stdout/stderr各64 KiB上限を使用する。各ストリームは最大64 KiBだけを保持し、上限超過を検出した場合は追加出力を保持せず、そのcollectorを`not_available`へ収束させる。取得対象にユーザー入力パスを含めない。

### 8.2.1 SystemInfoWorkerの固定契約

- Aboutを開いた時点でdialogを生成し、表示値は初期状態`取得中...`とする。
- workerは`job_id`、成功callback、失敗callbackを受け取り、collectorを1回だけ実行する。
- worker状態は`pending`、`running`、`completed`、`failed`、`cancelled`のいずれかとする。`cancelled`はダイアログ終了時にジョブを無効化する論理キャンセルであり、実行中のPythonスレッドまたは外部プロセスを強制停止する契約ではない。
- 個別collectorの失敗はsnapshot内の該当フィールドだけを`not_available`または`not_loaded`にし、worker全体を失敗にしない。
- 予期しないworker例外時は、全項目を未取得値にしたsnapshotと固定reason `system_info_unavailable`を返し、About自体は閉じない。
- dialog close時は一度だけ`cancel(job_id)`を適用し、`pending`または`running`のjobを`cancelled`へ遷移させて無効化する。collectorが後から終了しても`cancelled`から`completed`または`failed`へ戻さず、`wx.CallAfter`で到着したcallbackは`job_id`とdialog identityが一致する場合だけ反映する。
- worker終了を待つためにUIスレッドをjoinしない。アプリ終了時はcallbackを破棄し、既存の終了処理を阻害しない。

### 8.3 JSON Helpテキスト

- `assets/usage_guide.json`をHelp表示の本文の正本とする。
- JSONは`lines`配列を持ち、アプリ側で改行結合して表示する。source実行ではリポジトリ内のJSON、PyInstaller onefileではspecで`assets`へ同梱されたJSONを読む。
- ユーザーが実行ファイルの外へHelp文書を配置・編集する契約にはしない。読み込み失敗時は固定の失敗文を表示し、アプリ全体を終了させない。
- Help表示用にREADMEを自動変換・結合しない。内容の重複は許容するが、JSON Help本文はGUI操作に必要な説明を優先する。

### 8.4 ダイアログ

- `wx.Dialog`を使用し、既存のダイアログ生成・`ShowModal()`・`Destroy()`の慣例に合わせる。
- Helpは読み取り専用の複数行`wx.TextCtrl`、縦スクロール、閉じるボタンを持つ。
- Aboutは項目名と値を見やすく並べ、値の編集操作を提供しない。
- ダイアログの生成時に現在の`theme_mode`を`ThemeManager.apply_theme()`へ渡す。
- ダイアログは親Frameを所有者として生成し、閉じた後に参照を残さない。
- About最下部に`wx.adv.HyperlinkCtrl`または同等の読み取り専用リンクを配置し、表示ラベルとhrefを`https://x.com/kanna3939`へ固定する。
- system info workerの取得中はAboutの値欄へ`取得中...`を表示し、完了後にsnapshot値へ置き換える。dialog identityとjob IDを照合し、閉じたdialogへの遅延callbackを破棄する。

### 8.5 メニューとController

- `MainFrame._on_mi_help()`と`_on_mi_about()`の入口は維持する。
- `AppController.request_open_help()`と`request_show_about()`はStub status更新からviewの専用表示入口へ変更する。
- `update_action_states()`ではHelp/Aboutを常時有効とする。ただし親Frameが破棄済み、またはアプリ終了処理中の場合は表示要求を破棄する。
- 解析、Preview、Writer、VMD保存、debug trace、runtime user dataの状態を変更しない。

## 9. 詳細ステップ

1. B5対象コードと現行README / 配布用説明書を再照合し、Helpテキストへ記載する操作名、対応ファイル形式、利用場面を固定する。
2. `SystemInfoSnapshot`と個別collectorを追加し、固定状態値、timeout、部分失敗の収束を実装する。
3. system info collectorのunit testを追加する。OS、Whisper、FFmpeg、GPUの実環境値へ依存しない。
4. `assets/usage_guide.json`を作成し、対応ファイル形式、利用場面、現行機能、GUIラベルを照合する。
5. Help/Aboutダイアログと`system_info_worker.py`を追加し、JSON Helpテキストのresource path読み込み、読み取り専用表示、テーマ適用、閉じる処理、job IDによる遅延callback破棄を実装する。
6. AppControllerとMainFrameのメニュー経路を接続し、Help/Aboutを有効化する。
7. `MMD_AutoLipTool.spec`へ`assets/usage_guide.json`を`assets`配下として登録し、source / onefileで同じコード経路から表示されることを確認する。
8. Core、worker、GUI、JSON Helpテキスト、resource path読み込みのテストを追加し、wx teardown後のnative exceptionが発生しないことを確認する。
9. 対象回帰を実行し、差分と`git diff --check`を確認する。
10. 実装後にsource実行、EXE実行、Light / Dark / System、Whisper loaded / not loaded、FFmpeg absent、GPU情報取得不能の手動確認を行う。

## 10. 状態遷移 / データ契約

### 10.1 Help

```text
  menu disabled (現状)
  -> menu enabled
  -> bundled JSON usage text
       -> JSON loaded: read-only text window
       -> load failure: fixed failure text window
  -> close
  -> application state unchanged
```

Helpは解析状態・入力状態・Busy状態に依存しない。JSON本文の表示は設定やruntime user dataを更新しない。

### 10.2 About

```text
menu disabled (現状)
  -> menu enabled
  -> dialog opened
  -> snapshot collecting
       -> completed: values shown
       -> partial failure: available values + not_available/not_loaded
       -> timeout: affected value only becomes not_available
  -> close / late callback discarded
  -> application state unchanged
```

`not_available`、`not_loaded`、`loaded`などの状態値は固定値とし、例外文字列や環境依存の自由文を契約値として保存しない。

### 10.3 既存状態との境界

- AboutのWhisper表示は、現在の`UiState.whisper_model_selection`やanalysis identityを書き換えない。
- FFmpeg version取得は音声変換、解析用WAV生成、MMD用WAV生成を開始しない。
- Help/Aboutの表示は`debug`フォルダ、diagnostic artifact、save-state fingerprintへ書き込まない。
- メニューを有効化しても、既存の入力・解析・保存のenable条件を変更しない。

## 11. テスト方針

### 11.1 Core / collector

- app versionの正常値と取得不能時の`not_available`
- Whisper未ロード、ロード済み正常version、version不正
- FFmpeg正常version、未検出、終了コード異常、timeout、出力解析不能
- CPU名fallback、論理プロセッサ数取得不能
- メモリ取得正常・失敗
- GPU複数値、重複、空値、照会失敗
- 部分失敗時に他項目が保持され、snapshot全体が失敗しないこと
- 外部コマンドが`shell=False`、固定引数、`CREATE_NO_WINDOW`、timeout付きで呼ばれ、stdout/stderrを各64 KiBを超えて保持しないこと。上限超過時は該当値が`not_available`へ収束すること

### 11.2 GUI

- Help/Aboutメニューが初期化後に有効であること
- Controller要求が正しいview入口へ届くこと
- Helpテキストが読み取り専用かつスクロール可能であること
- About値が編集できず、`not_available` / `not_loaded`がそのまま表示されること
- Aboutのアプリversionがresolver生値へ既存formatterを一度だけ適用して表示され、取得不能時は`not_available`のまま表示されること
- About最下部のhrefが`https://x.com/kanna3939`に固定され、表示時にはブラウザを起動せず、クリックイベント時だけ既定ブラウザ起動処理へ渡されること
- Light / Dark / Systemで背景・文字・TextCtrlが視認できること
- Busy中に開け、閉じた後もBusy・解析・保存状態が変わらないこと
- dialog close後の遅延callbackが破棄されること
- dialog close時にjobが論理的に`cancelled`へ遷移し、collector終了後もcallbackやsnapshotが閉じたdialogへ反映されないこと
- wx App / Frame / Controllerのteardownが既存helper契約を満たすこと

### 11.3 Helpテキスト・package

- JSON Helpテキストが空でなく、必須見出し、対応ファイル形式、利用場面、現行GUIラベルを含むこと
- source実行時のJSON読み込みが成功し、JSONの内容がHelp表示へ反映されること
- Helpテキストがユーザー配置の外部文書に依存せず、PyInstaller `datas`でJSONが`assets`へ同梱されること
- specにJSON以外のHelp文書の不要なdatas追加がなく、既存の不要モジュール除外、FFmpeg同梱、version fileを変更しないこと

### 11.4 手動・配布確認

自動テストだけでは次を保証しないため、実装後に別枠で確認する。

- Python source実行でHelp/Aboutが開くこと
- `dist`のEXEでspec同梱JSONのHelpテキストが表示されること
- Light / Dark / System各テーマで視認できること
- Whisper未読み込み時と解析後のAbout表示差
- FFmpeg未検出時、GPU取得不能時にもAboutが開くこと
- 既存の解析、Preview、VMD保存、MMD一括出力への影響がないこと

EXEビルド成功、EXE起動、Help/About手動確認、MMDでの見た目確認は別々の証拠として記録する。

## 12. 受け入れ条件

- [ ] B5-AC01: Help/Aboutメニューがグレーアウトせず、既存Busy状態にかかわらず開ける。
- [ ] B5-AC02: JSON Help本文が用途、利用場面、対応ファイル形式、現行機能を説明している。
- [ ] B5-AC03: Helpが読み取り専用・スクロール可能なポップアップテキストウィンドウへJSON本文を表示する。
- [ ] B5-AC04: Help表示がユーザー配置の外部文書に依存せず、sourceとEXEでspec同梱JSONの同じ内容を表示する。
- [ ] B5-AC05: Aboutがアプリversion、Whisper状態/version、FFmpeg version、CPU、物理メモリ、GPU製品名を表示する。
- [ ] B5-AC05a: Aboutの最下部に、表示ラベルまたはURLとして`https://x.com/kanna3939`への作者連絡用リンクが表示され、クリック時だけ既定ブラウザへ遷移する。
- [ ] B5-AC06: Whisper未読み込みは自動importせず、`not_loaded`または定義済み未取得状態で表示する。
- [ ] B5-AC07: FFmpeg未検出、GPU情報取得失敗、各種timeoutがAbout全体の表示失敗にならない。
- [ ] B5-AC08: About表示時にネットワーク通信、モデル取得、音声解析、設定変更、通常のFFmpeg処理、debug artifact生成が発生しない。FFmpegは`-version`問い合わせだけを許可し、作者リンクはクリック時だけブラウザ遷移する。
- [ ] B5-AC09: Light / Dark / SystemテーマでHelp/Aboutの背景、文字、TextCtrl、ボタンが視認できる。
- [ ] B5-AC10: ダイアログを閉じた後、入力、解析、Preview、Writer、保存可否、Undo / Redo、Busy状態が不変である。
- [ ] B5-AC11: source実行とPyInstaller onefileの両方で、ユーザー配置の外部Helpファイルなしにspec同梱JSONを表示できる。
- [ ] B5-AC12: 新規依存、版数変更、旧Qt/PySide6復活、既存MS28契約変更がない。
- [ ] B5-AC13: B5専用テスト、関連wx回帰、必要な全体回帰、`compileall`、`git diff --check`が成功する。
- [ ] B5-AC14: 実装後のEXE起動確認とHelp/About手動確認を、source自動テストと分離して記録する。

## 13. リスクと対策

| リスク | 対策 |
| --- | --- |
| GPU照会が環境差で失敗する | 取得不能を正常な部分失敗として`not_available`へ収束させる |
| FFmpeg version問い合わせがUIを止める | 固定引数・短いtimeout・専用worker・late callback guardを使用する |
| Whisper表示のために未配置モデルやpackageを誤って読み込む | `sys.modules`の既存runtimeだけを参照し、Aboutからimport・downloadしない |
| Helpの説明がEXEで欠落する | `assets/usage_guide.json`をspecの`datas`で`assets`へ同梱し、source / onefileのresource pathから同じJSONを読む |
| テーマ適用漏れ | ダイアログ生成直後に`ThemeManager.apply_theme()`を実行し、Light / Dark / Systemをテストする |
| Help/Aboutの遅延callbackが破棄済みdialogへ到達する | dialog identityとjob IDを照合し、close後のcallbackを破棄する |
| Helpの説明が現行GUIとずれる | 実装前にREADME、配布用説明書、現行menu/button labelと照合し、`assets/usage_guide.json`を正本として固定する |
| About表示が既存解析へ副作用を与える | collectorを読み取り専用にし、UI state、runtime user data、debug artifactへ書き込まない |
| PowerShell照会でコンソールが表示される | `shell=False`と`CREATE_NO_WINDOW`を固定し、照会失敗時は`not_available`へ収束させる |

## 14. 実装時の注意

- 既存の`request_open_help()`と`request_show_about()`のStubを置換するが、MainFrameからcoreへ直接GUI責務を流さない。
- Help/Aboutの表示情報を`MMD_AutoLipTool.ini`、`presets.json`、`profiles.json`、debug artifactへ保存しない。
- Aboutに絶対パス、ユーザー名、Whisperモデルの保存先、入力音声名などを表示しない。
- FFmpeg/GPUの外部照会は固定コマンドとし、ユーザー入力を引数へ渡さない。
- About最下部の作者リンクは`https://x.com/kanna3939`に固定し、ダイアログ表示時に自動でブラウザを開かない。
- version表示は`pyproject.toml`と既存`app_version.py`の解決経路を使い、別のversion literalを作らない。
- `not_available`、`not_loaded`、`loaded`などの状態値は、collector、snapshot、GUI表示、テストで同じ表記を使用する。
- Helpテキストの内容を実装状態より先行させない。未実装機能を使える機能として記載しない。
- 実装後は、変更ファイル、テスト終了コード、source確認、EXE確認、MMD確認、未検証範囲を分離して報告する。
