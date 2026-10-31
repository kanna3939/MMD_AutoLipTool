# MMD AutoLip Tool

Windows 向けの MikuMikuDance 用リップモーション生成ツールです。  
音声ファイル 1 件（wav / mp3 / m4a）と、必要に応じて UTF-8 のテキストファイル 1 件を読み込み、選択したモデルプロファイルの母音モーフを使った VMD を生成します。プロファイルなしでは `あ / い / う / え / お`、英字プロファイルでは `A / I / U / E / O` を使用します。

現在、GUI の wxPython への完全移行が完了しました（MS16 にて Qt/PySide6 を排除し、RightPane やプレビュー変形基盤の拡張が完了しました）。
現在のバージョン: `Ver. 1.2.0`
MS26で機能基準をCloseOut Aとして整理済みです。MS27-B4のonefile内部監査とB5のZIP・配布環境確認はPassです。B6監査では、Python 3.11 / 3.12のsource / build互換性をWindows onefile公開判定から外し、FFmpegのGitHub上の既存公開をユーザー判断で受容したため、release readinessはPassです。2026-09-18にユーザーがMS27 CloseOutを確定しました。GitHub Release、tag、push、merge、公開用source archive生成は別工程であり、未実施です。
2026-09-14にユーザーから手動確認通過・実MMDでも問題なしとの報告を受領しました。これはユーザー確認の記録であり、Codex自身のGUI・実MMD操作結果ではありません。

※ このツールはAIコーディングで作成されています。AIコーディング製ツールに不安がある方の使用は推奨しません。

## できること

- TEXT からひらがな列・母音列を生成
- TEXTなしの音声のみ入力から、Whisper書き起こしを使ってひらがな列・母音列を生成
- 音声のみ入力の書き起こし結果を確認・編集し、再解析
- wav / mp3 / m4a の読み込みと、解析用WAVを使った波形・Preview の実描画
- 処理実行時に音声タイミングを解析して母音イベント列を生成
- 対象範囲の自動母音遷移を既定で適用し、RightPaneのInfoで適用範囲と適用・非適用件数を確認
- VMD上の母音曲線が厳密に変わらないと証明できる不要なキーを自動で整理し、Infoで整理数と保持理由を確認
- MMD 用の VMD リップモーションを書き出し
- 専用の `MMD用WAV出力` から、MMD読み込み用のWAVを書き出し
- `ファイル > MMD一括出力...` から、VMD・MMD用WAV・診断レポートを専用フォルダへ一括出力
- 波形表示と Preview の同期表示、および再生中の追従スクロール
- Preview上の母音イベント選択と、RightPaneからのイベント単位補正
- 個別補正のセッション内Undo / Redo（最大50操作）
- 明示された長音（`ー`）の `hold / decay` 表現。`decay` は長音終端で0へ減衰します
- 組み込みプリセットとユーザープリセット（`presets.json`）による生成設定の再利用
- モデルプロファイル（`profiles.json`）による母音名セット、上限値、長音・閉口設定、標準プリセットの再利用
- Whisperモデル（`small` / `medium` / `turbo`）の選択、明示的な `Download & Verify`、適用後の再解析
- 処理実行中の二重実行防止 / 分析中止 / 長時間解析警告
- `ファイル > 新規作業...` から、設定・履歴を保持したまま現在の作業を初期化
- TEXT / 音声ファイルの最近使ったファイル履歴
- VMD 保存先フォルダの記憶と設定の保存・復元
- デバッグモード中のローカル操作経過記録（任意・既定OFF）

## 動作環境

- OS: Windows 11
- Python: 3.11 以上
- GUI: wxPython (旧 PySide6 系は凍結)

開発・ビルドは Windows PowerShell を前提にしています。

## 入力と出力

### 入力

- TEXT: UTF-8 テキストファイル（任意。音声のみ入力では不要）
- 音声: wav / mp3 / m4a ファイル

### 出力

- VMD: MikuMikuDance 用リップモーションファイル
- MMD用WAV: 専用ボタンから出力する MMD 読み込み用 WAV
- MMD一括出力: 専用フォルダへ再生成する VMD・MMD用WAV・診断レポート

### 現在の前提

- 1 回の処理で扱う音声は1件です。TEXTあり入力ではTEXTを1件使用し、音声のみ入力ではTEXTを使用しません
- 音声解析と波形表示には、内部で生成した解析用WAVを使用します
- MMD用WAVは VMD 保存時の自動同時出力ではなく、個別には専用の `MMD用WAV出力` から保存します。一括出力では現在の状態からVMD・MMD用WAV・診断レポートをまとめて再生成します
- 一括出力の既定フォルダ名は `<audio_stem>_MMD` です。親フォルダとフォルダ名はダイアログで変更できます
- 一括出力は一時フォルダで3成果物を生成・検証してから確定します。同名の出力先がある場合は別名を指定し、既存フォルダのmerge・置換は行いません。失敗やキャンセル時も既存出力を保護します
- プロファイルなしの既定モーフは `あ / い / う / え / お` です。組み込みの英字モデルプロファイルを適用すると `A / I / U / E / O` を使用します
- 開口モーフ最大値の既定値は `0.9` です。有効な明示設定またはモデルプロファイルを適用した場合は、その設定値が出力に反映されます
- 自動母音遷移は対応する入力・区間で通常処理時に適用されます。対象外や保護された区間は既存の出力を維持し、適用範囲と適用・非適用の件数はRightPaneの `Info` に表示されます
- 自動キー整理は、元の母音曲線と保存されるVMDの数値がともに厳密一致すると確認できるキーだけを省きます。必要なキー、保護対象、出所や義務が確認できないキーは保持します。キーの省略は見た目の品質向上を意味しません。Infoに「対象外」と表示された場合は出力を変更しません
- モデルプロファイルは設定ファイルと同じ場所の `profiles.json` に保存され、最大100件です。プロファイルが適用中のときは、プロファイルの値を直接変更せず、名前変更だけが許可されます
- Whisperモデルは `small` / `medium` / `turbo` から選択し、既定値は `small` です。候補を選択しただけでは download、active modelの変更、解析は開始しません
- 未配置のWhisperモデルは、`Whisperモデル` タブの `Download & Verify` を明示的に実行して、公式URLから取得し、manifestのexact sizeとSHA256を検証します。検証済みの候補だけを `選択モデルを適用` で適用できます
- Whisperモデルの重みは配布版の実行用ZIPへ同梱せず、既定では実行ファイルに隣接する `models` フォルダへ保存します。保存先は `保存先を変更` からローカルの保存先へ変更できます。解析時の自動download、音声の外部送信、background通信は行いません
- 生成結果は自動処理による補助出力です。最終的な見え方は MMD 側で確認してください

### デバッグ操作ログ

`設定/表示 > デバッグモード` をONにすると、操作順、設定変更、処理結果をローカルへ記録します。初期状態はOFFで、アプリ再起動後もOFFです。ログは解析traceとは別の `debug/operations/` にJSONL形式で追記され、ソース実行時はリポジトリ直下、配布exeではexeの隣の `debug` フォルダを使います。

入力内容や音声データ、絶対パスは操作ログへ保存しません。記録項目は許可した状態値・ID・ファイル名などに限定します。1セッションの上限は16 MiBです。OFF中は新しい操作を記録せず、ONへ戻すと同じログの別区間へ記録します。保存に失敗した場合や記録が不完全な場合はGUIの状態表示で分かり、解析や保存など通常の操作は継続できます。

## 使い方

1. アプリを起動します。
2. TEXTあり入力では、`TEXT読み込み` で台詞テキストを選択します。音声のみ入力では、この操作を省略します。
3. `音声読み込み` で音声ファイルを選択します。
4. `処理実行` を押して解析を行います。
5. 音声のみ入力では、表示された書き起こし結果を確認します。修正した場合は `適用` 後にもう一度 `処理実行` を押します。
6. 波形表示と Preview を確認します。
7. 必要であれば `開口保持` と `閉口スムース` を調整します。解析後の数値変更は編集表示へ反映されます。Previewを確認して `変更を適用` を押すと出力へ反映されます。未適用の間はVMD保存・一括出力・診断レポート保存ができません。長音はRightPaneの `プリセット` から `標準（長音維持）` または `長音減衰` を選び、`選択したプリセットを適用` を押します。選択だけでは現在の出力へ反映されません。
8. ユーザープリセットを作成・更新・削除すると、実行ファイルと同じ場所の `presets.json` に保存されます。読み込みや保存に失敗した場合も組み込みプリセットは利用できますが、ユーザープリセットの変更は停止します。
9. `モデルプロファイル` タブでプロファイルを選択し、`選択したモデルプロファイルを適用` を押します。プロファイルなしへ戻すと、既定の日本語5母音へ戻ります。作成・更新・削除は同タブから行い、適用中のプロファイルは名前変更以外の変更がロックされます。
10. 母音イベントを個別に補正する場合は、Preview上の表示曲線をクリックし、RightPaneの `選択イベント` で値を編集します。同じ母音の連続した形状でも、選択されたイベントだけが編集対象です。必要に応じて通常shapeの `制限を解除` をONにすると、後続異母音への延長と3母音以上の重なりを設定できます。同母音shapeとのrequired-zero境界と音声の終端は越えられません。解除OFFで終了offsetが通常範囲外に残る場合、値はdraftに保持されて範囲エラーになり、範囲内へ戻すか解除を再度ONにするまで `変更を適用` は使えません。変更は編集表示に留まり、`変更を適用` を押した後に出力へ反映されます。`Ctrl+Z` / `Ctrl+Y` または `編集` メニューからUndo / Redoできます。
11. RightPaneの `Info` と `Warning` で入力・解析・生成・保存可否と診断内容を確認します。
12. `VMD保存` から `.vmd` ファイルを書き出します。
    保存先を指定すると進捗ウィンドウに処理段階が表示されます。確定前はキャンセルできます。ファイル確定後の検証中はキャンセルできず、結果が出るまで待ちます。
13. 診断内容をファイルへ残す場合は、`ファイル > 診断レポート保存...` から `<音声名>_report.txt` を保存します。
14. MMDで使う音声WAVが必要な場合は、`MMD用WAV出力` から `.wav` ファイルを書き出します。出力完了後はファイル名とフルパスを表示するダイアログが開き、`OK` で閉じます。この操作では解析やPreviewを再生成しません。
15. VMD・MMD用WAV・診断レポートをまとめて渡す場合は、`ファイル > MMD一括出力...` を選びます。親フォルダとフォルダ名を確認・編集すると、既定では `<audio_stem>_MMD` の専用フォルダへ次の3ファイルを出力します。
    - `<audio_stem>_lip.vmd`
    - `<audio_stem>_mmd.wav`
    - `<audio_stem>_report.txt`
    同名の出力先がある場合は別のフォルダ名を指定してください。既存フォルダのmerge・置換は行いません。
16. 次の素材を扱う場合は、`ファイル > 新規作業...`（`Ctrl+N`）を選びます。確認後、現在の入力・書き起こし・解析結果・表示を初期化します。適用中のモデルプロファイル、生成設定、テーマ、最近使ったファイル、保存先履歴は保持されます。

### Whisperモデルを切り替える場合

1. `Whisperモデル` タブで `small`、`medium`、`turbo` のいずれかを候補として選びます。候補の選択だけでは、download、active modelの変更、解析は始まりません。
2. 保存状態が `未配置` または `未完了` の場合は、`Download & Verify` を押します。明示確認後だけforegroundで取得し、公式URL、exact size、SHA256を検証します。途中でキャンセルした場合は、未完了の一時ファイルを解析へ使用しません。
3. 保存状態が `確認済み` になったら、`選択モデルを適用` を押します。適用成功後にactive modelが切り替わり、入力が読み込まれている場合はそのモデルで再解析が始まります。
4. 解析中にWhisperモデルを自動取得することはありません。モデルがない、壊れている、読み込めない場合は安全に失敗を表示し、音声を外部へ送信しません。

補足:

- 処理実行前は VMD 保存できません
- 音声のみ入力で書き起こし編集を適用した後は、再解析が完了するまで VMD 保存できません
- 書き起こしやタイミングを取得できない場合は、表示された内容に従って音声を確認し、再解析してください
- `ERROR` 診断がある場合は VMD 保存できません。`WARNING` 診断がある場合は、同じ解析・設定状態につき初回保存時だけ確認します
- 生成設定の変更は出力だけを再計算し、解析結果の再取得は要求しません。長音modeの優先順位は、terminal eventの明示override、適用中の生成設定、既定値（hold）の順です
- `decay` は長音終端で値が0になります。実際の口の見え方と音声との同期は、VMDとWAVをMMDへ読み込んで確認してください
- 解析中止を要求した直後は処理終了までBusy状態を維持します。変更前の有効な解析結果を再利用できる場合は、個別補正とUndo / Redo履歴も復元します
- 再解析に失敗しても変更前の結果を安全に再利用できる場合は、旧Previewと個別補正を確認用に復元します。ただしERRORを表示し、VMD保存はできません
- 解析失敗後の再試行をキャンセルした場合も、既存ERRORとVMD保存禁止を維持します
- 診断レポートはVMD保存不可の状態でも、元音声が読み込まれていれば保存できます
- VMD保存時は最後にVMDを正常保存したフォルダを再利用します。MMD用WAVの初期フォルダは、最後にMMD用WAVを正常保存したフォルダ、最後にVMDを正常保存したフォルダ、元音声のフォルダの順で選びます。診断レポートの初期フォルダは元音声のフォルダです
- MMD一括出力の親フォルダは、同じsessionで確定した親フォルダ、最後にMMD用WAVを正常保存したフォルダ、最後にVMDを正常保存したフォルダ、元音声のフォルダの順で初期化します。親フォルダやfolder名はINIへ保存しません
- MMD一括出力は現在の有効な編集状態から3成果物を再生成し、個別保存済みファイルを流用しません。実MMDでのVMD / WAV読込・再生・リップ同期は別途確認してください
- 処理中は操作の一部がロックされます
- `新規作業...` は処理中には実行できません。元のTEXT・音声、保存済みVMD・MMD用WAV・診断レポート、解析用WAVキャッシュは削除せず、最近使ったファイル・テーマ・各種パラメータ・保存先履歴を保持します

## 実行方法

仮想環境を作成して依存関係をインストールします。

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

アプリを起動します。

```powershell
.\.venv\Scripts\python.exe .\src\main.py
```

## ビルド方法

PyInstaller の `onefile` 構成で Windows 実行ファイルを作成します。

### 事前準備

現在使用する FFmpeg / ffprobe の `bin` 内容を、リポジトリ直下の `FFmpeg\bin\` に手動配置してください。

最低限、次の実行ファイルが必要です。

- `FFmpeg\bin\ffmpeg.exe`
- `FFmpeg\bin\ffprobe.exe`

### ビルド実行

```powershell
.\build.ps1
```

クリーンビルド:

```powershell
.\build.ps1 -Clean
```

起動スモーク確認付きビルド:

```powershell
powershell -ExecutionPolicy Bypass -File .\build.ps1 -Clean -SmokeLaunch
```

### ビルド出力

- ビルド定義: `MMD_AutoLipTool.spec`
- 出力形式: `onefile`
- 出力先: `dist\MMD_AutoLipTool.exe`
- FFmpeg 配置先: 実行ファイル内部にバンドルされます

## テスト

正式な開発検証にはPowerShell 7の共通runnerを使います。runnerは `.venv` のPythonでpytestを実行し、`C:\tmp\MMD_AutoLipTool\test-runs\` にログと結果summaryを保存します。テスト作業領域をrunごとに分け、`MMD_AutoLipTool.ini`、`profiles.json`、`presets.json` の実行前後をhashで照合します。

pytest終了時に作業領域内に残るVMDは、cleanup前にGit除外の `MMD Files/VMD Files/<run-id>/` へ相対配置を保ってコピーし、SHA-256を照合します。必要な保管フォルダはrunnerが作成します。summaryの `vmd_archive` と保管先の `archive-manifest.json` にpath・件数・hash・実行条件を記録します。テスト中に上書き・削除された中間VMDは保管対象外です。異常系テストの不正VMDも含まれるため、保管成功をVMD品質合格とは扱いません。保管失敗時は非ゼロ終了とし、元のworkを残します。pytestが失敗した場合もVMDの保管を試み、pytest終了値とwork保持を維持します。

```powershell
pwsh -NoProfile -File .\tools\run-tests.ps1 -CheckEnvironment
```

対象を限定するときは `tests/` 内のファイル、ディレクトリ、pytest node IDを指定します。引数なしで全件テストへ切り替わることはありません。

```powershell
pwsh -NoProfile -File .\tools\run-tests.ps1 -TestPaths tests/test_app_version.py
pwsh -NoProfile -File .\tools\run-tests.ps1 -CollectOnly -TestPaths tests/test_app_version.py
pwsh -NoProfile -File .\tools\run-tests.ps1 -FullSuite
```

開発用pytestの版は `requirements-dev.txt` に宣言しています。既存runtime依存は `requirements.txt` を参照し、既存 `.venv` の一括再作成・syncは行いません。VS CodeのTasksからも同じrunnerを実行できます。Python拡張のTestingビューはテスト探索や個別デバッグの補助経路で、runnerの一時領域分離・データ照合・ログ保存を経由しないため、正式な回帰検証結果とは分けて扱います。

新しい仮想環境を作成した場合に限り、runtimeと開発用依存を次のように導入します。

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt -r requirements-dev.txt
```

既存の `.venv` には先に `pwsh -NoProfile -File .\tools\run-tests.ps1 -CheckEnvironment` を実行し、`requirements.txt` と `requirements-dev.txt` に対する導入済み依存の差分を確認してください。確認だけのために既存環境へinstallやsyncは行いません。この環境整備作業でも、現在のvenvへ依存を導入していません。

## 配布とライセンス

このリポジトリのソースコードは [MIT License](LICENSE) で提供します。

配布時は、少なくとも次のファイルを同梱してください。

- [LICENSE](LICENSE)
- [NOTICE](NOTICE)
- [THIRD_PARTY_LICENSES.md](THIRD_PARTY_LICENSES.md)

FFmpeg を含むサードパーティライブラリの概要と配布時の確認先は [THIRD_PARTY_LICENSES.md](THIRD_PARTY_LICENSES.md) を参照してください。  
平易な免責と配布時注意事項は [NOTICE](NOTICE) を参照してください。

配布前には、実行用ZIPだけでなく GitHub が自動生成する Source code ZIP / tar.gz に含まれるファイルも確認してください。
現在の開発状態では `FFmpeg\bin\` の実体が Git 追跡対象に含まれるため、Source code アーカイブ側も FFmpeg 同梱物としてライセンス通知確認が必要です。

MS27-B3の確認では、現在のFFmpeg/ffprobeは
`N-123549-g70537ec8e6-20260318`で、`--enable-gpl --enable-version3`
および`--enable-shared`を含む構成です。FFmpegのFATE履歴では、対応する
upstream revision `70537ec8e6`が2026-03-18に記録されています。
<https://fatebeta.ffmpeg.org/history/x86_64-archlinux-gcc-threads-misc?begin=350>

取得時点の公式Download入口は<https://ffmpeg.org/download.html>、公式の
license / legal参照は<https://ffmpeg.org/legal.html>です。

revision固定のlicense参照は
<https://raw.githubusercontent.com/FFmpeg/FFmpeg/70537ec8e6/LICENSE.md>です。
ローカルのビルド形式はBtbNの`win64` / `gpl-shared`系列と強く整合しますが、
正確なWindows配布archiveまでは独立確認できていません。取得元は、ユーザー報告に
基づき、取得時点のFFmpeg公式Downloadページを起点としたものとして記録します。
公式ページはsource codeを提供し、Windowsのcompiled buildは外部提供元を案内します。
license参照は公式サイトの現行legal情報を採用し、license revisionとbinary revisionの
厳密な一致は本プロジェクトのG-LICENSE条件としません。G-LICENSEはこの方針に基づき
Passで、候補#08ではlicense原文・通知のZIP配置を確認済みです。2026-09-18に、ユーザーは
GitHub上の既存公開を規約上問題なしと判断し、Codexは`origin/main`がFFmpeg実体・通知文書を
追跡し、候補branchの`FFmpeg/bin`と差分がないことを確認しました。Codexは法的適合を独自に
保証しませんが、このユーザー判断によりMS27のrelease readinessはPassです。公開配布の完了や
最終公開許可を意味しません。

## 免責

本ソフトウェアは `AS IS` で提供されます。  
作者は、本ソフトウェアの使用または使用不能から生じる損害について責任を負いません。  
重要な制作データに使う場合は、生成結果の確認とバックアップを行ってください。

## リポジトリ内の主なファイル

- `src/main.py`: アプリ起動エントリーポイント
- `build.ps1`: Windows 向けビルドスクリプト
- `MMD_AutoLipTool.spec`: PyInstaller 設定
- `FFmpeg\bin\`: 手動配置する FFmpeg / ffprobe の `bin` 内容
- `docs/`: 仕様・マイルストーン・変更履歴文書

## 開発状況

本 README はエンドユーザー向けの案内を優先しています。  
実装マイルストーン、詳細仕様、開発ログは `docs/` 配下の文書を参照してください。

- `docs/Specification_Prompt_v4.md`
- `docs/MS16_and_Beyond_Milestone_Map_for_Antigravity.md`
- `docs/repo_milestone.md`
- `docs/Version_Control.md`
# MMD_AutoLipTool-dev
