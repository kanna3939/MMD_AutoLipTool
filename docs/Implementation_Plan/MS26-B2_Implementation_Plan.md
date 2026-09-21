# MS26-B2 Implementation Plan

## 1. 文書情報

- 対象: MS26-B2 自動横断回帰・状態整合
- 作成日: 2026-09-08
- 正本: [MS26 Block Breakdown](MS26_Block_Breakdown.md) MS26-B2、§9、§11
- 前提: [MS26-B1計画](MS26-B1_Implementation_Plan.md) §16、§16.2のbaseline / contract gateおよび実装後チェック通過
- 計画時branch / HEAD: `feature/MS26-implementation` / `20ec31f Record MS26-B1 baseline and post-implementation review`。開始時working treeはclean。
- 状態: 2026-09-09にB2実装、main統合レビュー指摘6件の限定補修、必須自動回帰、実装前チェック相当の計画・契約照合を完了。test-only duration gateと横断回帰は補修後process exit `0`で通過した。初回失敗と中間失敗は§15.5に保持し、4件の既存symlink権限skipは理由と受入影響を§15.2に記録した。B3実MMD・B4再検証 / Closeout・MS27は未実施。
- ユーザー判断A: duration差0.05秒以内は自動回帰の合格条件に限定する。個別MMD用WAV保存・一括出力に保存時duration検証を追加しない。
- 本計画の作成は実装・stage・commit・push等の許可ではない。

## 2. 背景

B1ではMS20〜MS25の契約と既存test入口を対応付けたが、現行HEADでの横断回帰は未実行である。旧MS25のtest totals、ユーザーGUI報告、STEREO固定対象テストは歴史証拠として保持し、B2のpassへ転用しない。

`convert_to_analysis_wav`と`export_mmd_wav`は、結果の`duration_sec`へいずれも入力probeの値を返す。この2値を比較しても、実際に生成されたWAVの長さ保持は証明できない。既存MS17-B7テストにはfake runnerが生成する短いWAVによる形式・呼出し契約の確認があるが、実FFmpegによる両WAVのduration差を証明するものではない。

B1 ledger `MS26-B2-002`を、実ファイルの独立測定とテスト側の不合格条件で解消する。ユーザー判断Aにより、保存時のvalidator、結果DTO、GUI、delivery transactionへduration gateを接続しない。

## 3. 目的

1. MS17-B7個別保存、MS19〜MS24の機能境界、MS25一括出力を同じ検証対象状態で回帰する。
2. 同一入力から生成したanalysis WAVとMMD用WAVを実測し、duration差が0.05秒以内であることを自動テストで確認する。
3. 比較不能・超過・測定対象の取り違えがテスト側で確実に不合格になることを確認する。
4. 自動証拠とB3の手動GUI・実MMD証拠を分離し、B4の再検証へ追跡可能な記録を残す。

## 4. In Scope

- 既存の責務別test群とfull pytest、compileall、diff checkの順次実行。
- duration測定・比較用のtest-only helper、境界値test、実FFmpegによる自動統合testの追加。
- テスト時の一時音声生成、実probe、実analysis/MMD WAV変換、生成ファイルの独立read-back。
- 回帰で実証された既存契約違反だけの最小補修。原因・対象・影響を記録し、補修後の再検証を必須とする。
- B1 §16 ledgerのB2行への実測記録、B2計画・Block Breakdown・Indexの実到達状態同期。

## 5. Out of Scope

- 保存時duration検証、新しい保存拒否条件、duration用のproduction error code、DTO/APIのduration意味変更。
- duration helperの`src/`配置、GUI/worker/deliveryへの測定処理の接続、保存前の追加変換。
- STEREO固定、sample rate、codec、音声開始位置の仕様変更。許容差を0.033秒等へ変更しない。
- 依存、lock file、PyInstaller設定、バイナリ、ライセンス、配布物の変更・生成、MS27作業。
- runtime `presets.json` / `profiles.json` / `MMD_AutoLipTool.ini`の直接編集・コピー・stage。
- 実MMD素材の持ち込み、Whisper model取得、ネットワーク通信、cloud ASR、手動GUI/MMD受入。
- B3/B4開始、MS26 Closeout、stage / commit / branch変更 / merge / push / tag / release。

## 6. 前提条件

- B1 gate通過と判断Aは確定済み。B3のWindows build、MMD、model、音声、TEXT、Whisper、preset/profile等は未提供のままでよく、B2計画・自動回帰の開始条件にしない。
- 使用環境はローカルWindows開発環境と既存`.venv`。B1実測はPython 3.14.3であり、実装開始時にPython/依存/FFmpegのidentityを再記録する。Python 3.11 / 3.12互換性は今回の完了証拠に含めない。
- `pyproject.toml`はPython >=3.11、wxPython 4.2.5、matplotlib 3.10.8、numpy 2.4.3、openai-whisper 20250625、pyopenjtalk 0.4.1。環境再構築や依存更新は行わない。
- FFmpeg/ffprobeは既存`FFmpeg/bin/`優先、次にPATHという既存locatorを使用する。実行path/versionと必要encoderの利用可否を記録し、自動downloadしない。
- 必須の実FFmpeg testでtool/encoderがない場合は環境不備としてB2 gateを未通過にする。mockへ置換してpass、理由のないskip、codecの自動切替をしない。

## 7. 対象ファイル

| 区分 | 対象 | 扱い |
| --- | --- | --- |
| 新規予定 | `tests/ms26_wav_duration_helpers.py` | test-onlyのPCM測定・pair検査。計画時点で未作成 |
| 新規予定 | `tests/test_ms26_b2_wav_duration.py` | helperのpositive / negative / 境界値。未作成 |
| 新規予定 | `tests/test_ms26_b2_wav_duration_integration.py` | 実FFmpeg変換結果の比較。未作成 |
| 既存確認 | `src/core/audio_convert.py`, `mmd_wav_export.py`, `audio_probe.py`, `ffmpeg_runner.py`, `ffprobe_runner.py`, `ffmpeg_locator.py` | 既存変換/probe/探索契約。判断Aのためduration対応では変更しない |
| 既存確認 | `src/core/pipeline.py`, `output_diagnostics.py`, `diagnostic_report.py`, `delivery_package.py`, `delivery_artifacts.py` | effective output、snapshot、source identity、transaction契約 |
| 既存確認 | `src/gui_wx/app_controller.py`, `ui_state.py`, `audio_worker.py`, `worker_state.py`, `output_diagnostics_adapter.py`, `main_frame.py`, `right_pane.py` | Busy / cancel / close / late result / 個別保存の回帰境界 |
| 既存確認 | `src/vmd_writer/writer.py`, `validator.py` | 30fps、resolved morph names、read-back |
| 既存回帰 | B1計画§7.3と本計画§11のtest群、`tests/conftest.py` | test入口を保持。conftestの全体設定は原則変更不要 |
| 文書 | 本計画、B1計画§16、Block Breakdown、MS20 Index | 計画/実測/未検証を分離して同期 |
| 正文参照 | Pipeline / GUI State / Error Handling / VMD Output / MMD Audio WAV仕様、README、配布用readme | 保存時挙動を変えないため原則編集不要 |

他のproduction/testファイルを変更する場合は、回帰で発見したfindingと既存契約を根拠に限定する。保存時duration検証や依存変更が必要になった場合は本計画を越えるため、ユーザーへ質問して停止する。

## 8. 実装方針

### 8.1 test-onlyのduration oracle

- 標準ライブラリ`wave`で生成されたPCM WAVを読み、`nframes / framerate`でdurationを得る。probe値、result DTOのduration、ファイル全体のbyte数から推定しない。
- frames/rateは正の値、非圧縮PCM、期待sample width 2 byte、analysis=1ch / MMD=2ch、rate=44100 Hzを検査する。宣言frames分のdataを実際に読み、途中切れ・frame整列不良・空dataを拒否する。
- `Fraction(nframes, framerate)`で比較し、`abs(analysis_duration - mmd_duration) <= Fraction(1, 20)`を合格条件とする。丸め・追加epsilonで超過を許容しない。
- helperは失敗時にテスト用の例外/assertionと、対象role、frames/rate、差分、理由を返す。production `AudioErrorCode`へ写像しない。negative testはその失敗を期待してpassするのであり、不正WAVの保存成功を意味しない。
- callerは同じ実入力のprobeから両変換を行い、各resultのsource_pathがその入力の解決済みpathと一致すること、出力2pathが別物であることを検査する。input identityを生成前後で比較し、入力の差し替えも検出する。
- helperのsource/path guardをnegative testで確認する。source identityだけで任意の同長WAVの由来を証明できるとは主張しない。実統合testの同一入力→2つの実変換という生成経路と併せて証拠とする。

### 8.2 一時fixtureと実変換

- `tmp_path`配下へ標準ライブラリで決定的な短いPCM音声を生成する。チャンネル別の識別可能なtoneと先頭/終端の非無音区間を持たせ、全無音だけに依存しない。音声品質/リップ同期の受入fixtureではない。
- 必須入力はWAV mono/stereo/3ch、MP3 mono/stereo、M4A(AAC) mono/stereo。WAVは44100/48000 Hzの両方、圧縮形式は48000 Hzのsourceから生成し、resample経路を含める。
- 短い非整数秒長（例1.37秒）と数秒長（例5.11秒）を使用する。全長15分の負荷試験は必須にしない。
- MP3/M4Aの生成は既存FFmpegを引数list・shell=False・有限timeoutで実行し、exitを検査する。全生成物はtmp_path内のみ。追加依存・保存済みユーザー音声・実Whisper modelは不要。
- 生成した各入力へ`probe_audio_file`を実行し、同じprobeで`convert_to_analysis_wav(cache_dir=tmp_path配下)`と`export_mmd_wav(output_path=tmp_path配下)`を呼ぶ。runnerをmockしない。
- 生成された両WAVをhelperで独立測定する。元のPCM fixture長との比較を圧縮入力の厳密な合否条件にせず、同じ圧縮入力から生成されたanalysis/MMD WAV間を比較する。
- 通常runnerとGUI/deliveryで使うcancellable runnerの両経路で少なくともWAV stereo 48000 HzとM4A stereoを確認する。既存CancelToken/runnerの呼出し形を使い、UIを起動しない。取消し・cleanup等自体は既存MS25回帰へ対応付ける。
- 取得不能や超過はテストを不合格にする。アプリの保存処理がその異常を検知・拒否したという証拠にはしない。

### 8.3 保存・状態契約の保持

VMDはcurrent EffectiveShapePlan、MMD WAVはoriginal source、reportは同じimmutable snapshotから生成する。Preview / writer / diagnostics / reportのeffective meaning、Japanese `あ / い / う / え / お`とLatin `A / I / U / E / O`、Whisper selected/active/loaded/analysis identityを保持する。

一括出力はstagingで全成功後に確定し、同名directoryのmerge/replace/delete/automatic renameをしない。個別保存導線、Busy/cancel/close/late result、cleanup failureの既存契約を弱めない。保存時のduration値やvalidatorが変わっていないこともdiffで確認する。

## 9. 詳細ステップ

1. **B2-01 baseline**: live HEAD/branch/tree、Python、依存、FFmpeg/ffprobeを記録。B1 gate・判断Aを確認する。旧test結果を今回のpassにしない。
2. **B2-02 既存回帰**: §11のMS17-B7→MS25→MS19〜MS24を順次実行。不合格を分類し、今回の対象外の環境/仕様判断が必要なら報告する。
3. **B2-03 duration helper**: test-only helperとunit casesを追加し、まずhelperのtestを実行する。
4. **B2-04 実変換**: 一時入力matrixと実FFmpeg integrationを追加し、actual WAVの長さを測定する。mockだけのpassでB1 findingを閉じない。
5. **B2-05 補修・横断照合**: 実証された契約違反にだけ最小補修。Aの範囲を越える保存時拒否の追加はしない。修正test→影響群→full gateを再実行する。
6. **B2-06 full gates**: pipeline/VMD、full pytest、compileall、diff checkを実施。全required groupの結果を同じ検証対象状態へ揃える。
7. **B2-07 証拠・状態同期**: B1 §16へB2実測を記録。全必須条件を満たした場合だけB2 auto-regression-passed。B3/B4を開始せず、実装後チェックに渡す。

## 10. 状態遷移 / データ契約

`B1 gate passed → B2 plan created → 実装前チェック → B2実装依頼 → targeted regression / test追加 → full gates → B2証拠記録 → 実装後チェック`

- 本計画作成時点はplan createdのみ。B2 test passや実装前チェック完了を宣言しない。
- 検証identityはHEADだけでなく、未コミット差分・未追跡testを含むworking treeの内容を識別できるdiff/ファイルhash一覧とする。commitは検証の前提にしない。
- code/test/GUI/契約変更後は影響行をstale扱いとし、変更後状態で再実行する。B2実行者が失効と再実行を記録し、B4が最終照合する。文書のみの状態同期は意味不変の根拠を付けて分離する。
- B1 §16の既存`MS26-B2-001`は全体回帰、`MS26-B2-002`はduration findingの集約行とする。個々のコマンド/再実行は新しい一意IDを割り当て、前の失敗記録を上書きして消さない。
- source、executor、HEAD/tree identity、環境/tool identity、fixture条件、command、pass/fail/skip/exit、証拠所在、制限を記録する。duration行には両WAVのframes/rate/duration、差分を含める。
- 実FFmpegによるrequired matrixとnegative oracle testsが揃って初めてduration findingをresolvedとする。保存時検証の追加は解消条件ではない。

## 11. テスト方針

以下はB2実装時の実行計画であり、策定時には実行しない。各コマンドを単独で実行する。

### 11.1 既存責務別gate

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_ms17_b7_mmd_wav_export.py tests/test_ms17_b7_mmd_wav_failure_cleanup.py tests/test_ms17_b7_mmd_wav_save_dialog.py tests/test_ms17_b7_mmd_wav_overwrite_confirm.py tests/test_ms17_b7_mmd_wav_button_state.py
.\.venv\Scripts\python.exe -m pytest tests -k "ms25"
.\.venv\Scripts\python.exe -m pytest tests -k "ms19 or ms20 or ms21 or ms22 or ms23 or ms24"
```

MS25の13ファイルはB1 §7.3に列挙済み。MS19〜MS24群はfile名のmilestone名を持つwx testも含める。collection件数/対象を確認し、0件や想定群の欠落をpassにしない。時間制約で分割する場合も対象の和集合とskip/exitを記録する。

### 11.2 duration required gate

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_ms26_b2_wav_duration.py
.\.venv\Scripts\python.exe -m pytest tests/test_ms26_b2_wav_duration_integration.py
```

必須unit cases:

- 同長、差が閾値未満、ちょうど0.05秒、1 sampleだけ閾値超過。正負両方向の差。
- 44100 Hzの2205 samples差はpass、2206 samples差は失敗。同じsample数でもrateが不正な場合は拒否。
- missing/unreadable/壊れたheader/空data/途中切れ/非PCM/不正rate・channel・sample width。
- 同一出力pathの二重比較、source identity不一致、analysis/MMD role逆転。
- 両result.duration_secが同一の値でも、WAV実体のduration差が0.05秒を超える場合は不合格。metadata由来の偽passを防ぐ。

負例の期待例外をpytestが捕捉したケースはtest passでよい。ただし必須integrationの生成失敗/比較不能を例外捕捉・skipして合格させない。§8.2 matrixは全件実測し、欠落はB2未完了とする。

### 11.3 共通回帰・full gate

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_pipeline_and_vmd.py
.\.venv\Scripts\python.exe -m pytest tests -k "vmd_writer"
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe -m compileall -q src tests
git diff --check
```

すべてprocess exit code 0を要求する。既存skipも件数・理由・受入影響を残す。新規duration required casesは対象Windows環境でskip不可。symlink権限等の既存skipは、旧HEADと同じという理由だけで許容せず、必須Windows collision/fault gateを欠いていないか確認する。

未追跡ファイルは各ファイルへ`git -c core.autocrlf=false diff --no-index --check -- NUL <path>`を実行する。診断なしのexit 1は差分ありとして扱い、通常のpytest非0とは区別する。通常設定で表示されるCRLF変換warningはwhitespace診断と区別する。検証のためにstageしない。

## 12. 受け入れ条件

- MS17-B7、MS25、MS19〜MS24、pipeline/VMD、full pytest、compileall、diff checkが記録付きで通過している。
- TEXT/voice_only、preset/profile/morph set、effective output、Whisper identity、個別保存・一括出力の既存testを削除・弱体化していない。
- 実変換matrixの両WAVから独立測定し、差0.05秒以内を確認した。source DTO値の自己比較で代替していない。
- 超過・比較不能・取り違えをhelperのnegative testsが検出し、閾値境界が決定的である。
- duration追加はtests内だけで、保存処理・validator・DTO・GUI・error codeは判断Aに従い不変である。
- 補修があればfinding、最小変更理由、再検証が追跡できる。スコープ超過は未承認で実施していない。
- user data/依存/lock/build/外部素材に変更がない。生成fixtureは一時領域だけである。
- B1 §16へ実測とskip/失敗/制限を記録し、B3素材未確定・手動未実施・MS27 deferredを維持する。

## 13. リスクと対策

| リスク | 対策 |
| --- | --- |
| metadata同士の比較で偽pass | frames/rateを実ファイルから独立取得し、metadata一致・実体不一致の負例を持つ |
| WAV headerだけ読んで途中切れを見逃す | data実読と宣言frames分の長さを確認する |
| codec遅延やresample差 | 同じ圧縮入力から作った2出力を比較し、閾値を緩和せず不合格を記録する |
| test-only gateが保存時保護と誤記される | 判断Aを全状態文書へ反映し、保存時validationとは明確に分離する |
| tool不在・encoder不足 | required gate未通過として報告。download・依存追加・無言skipをしない |
| wx終了時非0・skipの混入 | pass数だけでなくprocess exit/skip理由を判定する |
| 旧結果または異なるtreeを混合 | HEADと差分identityを束縛し、変更後は影響群/full gateを再検証する |
| 一時fixtureによる実MMD受入の誤認 | B2は自動契約のみ、B3のload/play/morph/timing/visualは別証拠とする |

## 14. Codex 実装時の注意

- 本書は計画であり、実装は別途の依頼後に開始する。計画策定でpytest/compileallや音声生成を実行しない。
- コマンドは一つずつ実行し、パイプ・連結・並列を使わない。サブエージェントは新たな明示許可なしに起動しない。
- 失敗を修正するために保存時duration拒否を追加しない。判断Aを越える必要が判明したらユーザーへ質問する。
- fixtureにはmanaged persistenceとtmp_pathを使い、runtime JSON/INIや保存済み成果物を流用しない。
- 完了報告は確認ファイル、変更ファイル、実装内容、全command/exit、test/skip、P1/P2/P3、仕様逸脱、残課題、次工程を分ける。GUI/MMD未実施とGit操作未実施を明記する。

## 15. B2実装・自動検証記録（2026-09-09）

### 15.1 実装前照合と変更境界

- 実装・テスト実行者: サブエージェントCurie、Agent ID `01a08405-19f5-7b11-a814-62570eea666b`。統合レビュー・最終文書補正は親のメインエージェントが担当した。branch `feature/MS26-implementation`、baseline HEAD `ff57305`。初回開始時はclean、レビュー補修開始時は文書4件と未追跡test3件だった。
- `.codex/config.toml` の config v2 は `multi_agent_v2.min_wait_timeout_ms=300000`、`default_wait_timeout_ms=600000`、`max_wait_timeout_ms=1800000`。親メインが使用した実行API v1では `timeout_ms=600000` を明示した。v2設定の自動適用を確認したという意味ではない。Curie作業中はシェルをCurieだけが実行し、終了後に親メインが照合した。設定変更、モデルoverride、download、network通信は行っていない。
- B2計画全文、B1 §16、Block Breakdown、MS20 Index、対象production code / test入口を照合した。判断Aどおり、duration測定は `tests/` 内のtest-only helperへ限定し、保存validator、result DTO、GUI / worker、error code、delivery transaction、runtime JSON / INIは変更していない。
- 追加ファイルは `tests/ms26_wav_duration_helpers.py`、`tests/test_ms26_b2_wav_duration.py`、`tests/test_ms26_b2_wav_duration_integration.py` の3件だけである。mainレビュー後もproduction codeの変更は不要で、既存契約違反のproduction補修は発生しなかった。

### 15.2 コマンド結果

各コマンドは単独実行した。`pass`件数とprocess exit codeを分離して記録する。`B2-Cxx`はmainレビュー前の初回実装・回帰記録、`B2-Rxx`はmainレビュー指摘補修後の再検証記録であり、同一IDを再利用しない。

共通prefixは `PYTHON = .\.venv\Scripts\python.exe`、`PYTEST = .\.venv\Scripts\python.exe -m pytest` とし、実行時はprefixを展開した完全な単独コマンドを使用した。PowerShellの連結・パイプ・並列実行は行っていない。

初回記録のcommand IDは次の対応である。行は既存の初回結果を保持し、補修前の失敗も削除しない。

| ID | command / result |
| --- | --- |
| `B2-C01`〜`B2-C05` | Python version / executable / major imports / repository FFmpeg version / repository ffprobe version。各exit `0` |
| `B2-C06` | `.\.venv\Scripts\python.exe -m pytest tests/test_ms17_b7_mmd_wav_export.py tests/test_ms17_b7_mmd_wav_failure_cleanup.py tests/test_ms17_b7_mmd_wav_save_dialog.py tests/test_ms17_b7_mmd_wav_overwrite_confirm.py tests/test_ms17_b7_mmd_wav_button_state.py`。14 passed、0 skipped、exit `0` |
| `B2-C07` | `.\.venv\Scripts\python.exe -m pytest tests -k "ms25"`。160 passed、2 skipped、883 deselected、exit `0` |
| `B2-C08` | `.\.venv\Scripts\python.exe -m pytest tests -k "ms19 or ms20 or ms21 or ms22 or ms23 or ms24"`。497 passed、0 skipped、548 deselected、exit `0` |
| `B2-C09` | `.\.venv\Scripts\python.exe -m pytest tests/test_ms26_b2_wav_duration.py`。22 passed、0 skipped、exit `0` |
| `B2-C10` | `.\.venv\Scripts\python.exe -m pytest -s tests/test_ms26_b2_wav_duration_integration.py`。1 passed、0 skipped、20/20 matrix、exit `0` |
| `B2-C11` | `.\.venv\Scripts\python.exe -m pytest tests/test_pipeline_and_vmd.py`。13 passed、0 skipped、exit `0` |
| `B2-C12` | `.\.venv\Scripts\python.exe -m pytest tests -k "vmd_writer"`。98 passed、0 skipped、970 deselected、exit `0` |
| `B2-C13` | `.\.venv\Scripts\python.exe -m pytest tests`。1064 passed、4 skipped、exit `0` |
| `B2-C14` | `.\.venv\Scripts\python.exe -m pytest -rs tests/test_ms25_b2_windows_paths.py tests/test_whisper_model_store.py`。47 passed、4 skipped、exit `0` |
| `B2-C15` | `.\.venv\Scripts\python.exe -m compileall -q src tests`。no diagnostics、exit `0` |

補修前・中間の失敗履歴:

| ID | command / result |
| --- | --- |
| `B2-R01` | `.\.venv\Scripts\python.exe -m pytest tests/test_ms26_b2_wav_duration.py`。partial-tail negative追加直後、24 collected、22 passed、2 failed、exit `1`。mono declared data=3 / stereo declared data=5を`wave.readframes(frames)`だけでは検出できなかった |
| `B2-R02` | 同じunit command。helper補修直後、24 collected、22 passed、2 failed、exit `1`。実装は不完全frame tailを検出したが、期待regexだけが旧`frame alignment`のままだった |

補修後の再検証結果:

| ID | command / result |
| --- | --- |
| `B2-R03` | `.\.venv\Scripts\python.exe -m pytest tests/test_ms26_b2_wav_duration.py`。25 passed、0 skipped、exit `0` |
| `B2-R04` | `.\.venv\Scripts\python.exe -m pytest -s tests/test_ms26_b2_wav_duration_integration.py`。1 passed、0 skipped、24/24 matrix cases measured、exit `0`。locator `repo_local`、FFmpeg/ffprobe resolved path・versionを出力 |
| `B2-R05` | `.\.venv\Scripts\python.exe -m pytest tests`。1067 passed、4 skipped、exit `0`。4 skipは既存symlink生成のWindows `WinError 1314`。終了直後にwhisper availability daemonの`Exception in thread whisper-availability-1:`見出しが出力されたが、pytest process exitは`0`であり、今回のtests/docs変更では該当production pathを変更していない |
| `B2-R06` | `.\.venv\Scripts\python.exe -m compileall -q src tests`。補修後に実行、no diagnostics、exit `0` |
| `B2-R07` | `git diff --check`。補修後tracked diffにdiagnosticなし、exit `0` |
| `B2-R08` | `git -c core.autocrlf=false diff --no-index --check -- NUL tests/ms26_wav_duration_helpers.py`。diagnosticなし、untracked fileの差分ありを示す規定exit `1`。通常設定ではCRLF変換warningのみ |
| `B2-R09` | `git -c core.autocrlf=false diff --no-index --check -- NUL tests/test_ms26_b2_wav_duration.py`。diagnosticなし、untracked fileの差分ありを示す規定exit `1`。通常設定ではCRLF変換warningのみ |
| `B2-R10` | `git -c core.autocrlf=false diff --no-index --check -- NUL tests/test_ms26_b2_wav_duration_integration.py`。diagnosticなし、untracked fileの差分ありを示す規定exit `1`。通常設定ではCRLF変換warningのみ |
| `B2-R11` | `Get-FileHash -Algorithm SHA256 -LiteralPath 'tests/ms26_wav_duration_helpers.py','tests/test_ms26_b2_wav_duration.py','tests/test_ms26_b2_wav_duration_integration.py','docs/Implementation_Plan/MS26-B1_Implementation_Plan.md','docs/Implementation_Plan/MS26-B2_Implementation_Plan.md','docs/Implementation_Plan/MS26_Block_Breakdown.md','docs/MS20_and_Beyond_Index.md'`。7対象pathの最終値をこのcommand outputと最終報告へ記録 |

| command | result | exit |
| --- | --- | ---: |
| `.\.venv\Scripts\python.exe --version` | Python 3.14.3 | 0 |
| `.\.venv\Scripts\python.exe -c "import sys; print(sys.executable)"` | repo `.venv` executable | 0 |
| `.\.venv\Scripts\python.exe -c "import wx, matplotlib, numpy, whisper, pyopenjtalk; print('major imports ok')"` | major imports ok | 0 |
| `.\FFmpeg\bin\ffmpeg.exe -version` | `N-123549-g70537ec8e6-20260318` | 0 |
| `.\FFmpeg\bin\ffprobe.exe -version` | `N-123549-g70537ec8e6-20260318` | 0 |
| `pytest` MS17-B7 five files | 14 passed, 0 skipped | 0 |
| `pytest tests -k "ms25"` | 160 passed, 2 skipped, 883 deselected | 0 |
| `pytest tests -k "ms19 or ms20 or ms21 or ms22 or ms23 or ms24"` | 497 passed, 0 skipped, 548 deselected | 0 |
| `pytest tests/test_ms26_b2_wav_duration.py` | 22 passed, 0 skipped | 0 |
| `pytest -s tests/test_ms26_b2_wav_duration_integration.py` | 1 passed, 0 skipped; 20/20 matrix cases measured | 0 |
| `pytest tests/test_pipeline_and_vmd.py` | 13 passed, 0 skipped | 0 |
| `pytest tests -k "vmd_writer"` | 98 passed, 0 skipped, 970 deselected | 0 |
| `pytest` full suite | 1064 passed, 4 skipped | 0 |
| `pytest -rs tests/test_ms25_b2_windows_paths.py tests/test_whisper_model_store.py` | 47 passed, 4 skipped | 0 |
| `python -m compileall -q src tests` | no diagnostics | 0 |

Full suiteの4 skipは、`tests/test_ms25_b2_windows_paths.py` 2件と `tests/test_whisper_model_store.py` 2件のsymlink生成で、いずれもWindows `WinError 1314`（作成権限不足）による既存環境制約である。MS25 B6の実filesystem collision / cleanup fault gateはskipなしで通過しており、B2の必須受入を欠落させるskipではない。新規duration testにskipはない。

### 15.3 実FFmpeg duration matrix

以下は、同一sourceから実FFmpegで生成したanalysis WAV / MMD用WAVを、result DTOの `duration_sec` に依存せず `wave` の実 `frames / rate` から測定した値である。全出力はanalysis=mono、MMD=stereo、44100 Hz、差分判定は `<= 0.05` 秒である。20条件を通常runnerで測定し、WAV stereo 48000 Hz 2条件とM4A stereo 2条件をcancellable runnerでも再測定したため、測定caseは合計24件である。

| case | runner | analysis frames/rate/duration | MMD frames/rate/duration | difference |
| --- | --- | --- | --- | ---: |
| WAV 1ch / 44100 / 1.37s | normal | 60417 / 44100 / 1.370000000 | 60417 / 44100 / 1.370000000 | 0.000000000 |
| WAV 1ch / 44100 / 5.11s | normal | 225351 / 44100 / 5.110000000 | 225351 / 44100 / 5.110000000 | 0.000000000 |
| WAV 2ch / 44100 / 1.37s | normal | 60417 / 44100 / 1.370000000 | 60417 / 44100 / 1.370000000 | 0.000000000 |
| WAV 2ch / 44100 / 5.11s | normal | 225351 / 44100 / 5.110000000 | 225351 / 44100 / 5.110000000 | 0.000000000 |
| WAV 3ch / 44100 / 1.37s | normal | 60417 / 44100 / 1.370000000 | 60417 / 44100 / 1.370000000 | 0.000000000 |
| WAV 3ch / 44100 / 5.11s | normal | 225351 / 44100 / 5.110000000 | 225351 / 44100 / 5.110000000 | 0.000000000 |
| WAV 1ch / 48000 / 1.37s | normal | 60417 / 44100 / 1.370000000 | 60417 / 44100 / 1.370000000 | 0.000000000 |
| WAV 1ch / 48000 / 5.11s | normal | 225351 / 44100 / 5.110000000 | 225351 / 44100 / 5.110000000 | 0.000000000 |
| WAV 2ch / 48000 / 1.37s | normal | 60417 / 44100 / 1.370000000 | 60417 / 44100 / 1.370000000 | 0.000000000 |
| WAV 2ch / 48000 / 5.11s | normal | 225351 / 44100 / 5.110000000 | 225351 / 44100 / 5.110000000 | 0.000000000 |
| WAV 3ch / 48000 / 1.37s | normal | 60417 / 44100 / 1.370000000 | 60417 / 44100 / 1.370000000 | 0.000000000 |
| WAV 3ch / 48000 / 5.11s | normal | 225351 / 44100 / 5.110000000 | 225351 / 44100 / 5.110000000 | 0.000000000 |
| MP3 1ch / 48000 / 1.37s | normal | 60417 / 44100 / 1.370000000 | 60417 / 44100 / 1.370000000 | 0.000000000 |
| MP3 1ch / 48000 / 5.11s | normal | 225351 / 44100 / 5.110000000 | 225351 / 44100 / 5.110000000 | 0.000000000 |
| MP3 2ch / 48000 / 1.37s | normal | 60417 / 44100 / 1.370000000 | 60417 / 44100 / 1.370000000 | 0.000000000 |
| MP3 2ch / 48000 / 5.11s | normal | 225351 / 44100 / 5.110000000 | 225351 / 44100 / 5.110000000 | 0.000000000 |
| M4A 1ch / 48000 / 1.37s | normal | 61152 / 44100 / 1.386666667 | 61152 / 44100 / 1.386666667 | 0.000000000 |
| M4A 1ch / 48000 / 5.11s | normal | 225792 / 44100 / 5.120000000 | 225792 / 44100 / 5.120000000 | 0.000000000 |
| M4A 2ch / 48000 / 1.37s | normal | 61152 / 44100 / 1.386666667 | 61152 / 44100 / 1.386666667 | 0.000000000 |
| M4A 2ch / 48000 / 5.11s | normal | 225792 / 44100 / 5.120000000 | 225792 / 44100 / 5.120000000 | 0.000000000 |
| WAV 2ch / 48000 / 1.37s | cancellable | 60417 / 44100 / 1.370000000 | 60417 / 44100 / 1.370000000 | 0.000000000 |
| WAV 2ch / 48000 / 5.11s | cancellable | 225351 / 44100 / 5.110000000 | 225351 / 44100 / 5.110000000 | 0.000000000 |
| M4A 2ch / 48000 / 1.37s | cancellable | 61152 / 44100 / 1.386666667 | 61152 / 44100 / 1.386666667 | 0.000000000 |
| M4A 2ch / 48000 / 5.11s | cancellable | 225792 / 44100 / 5.120000000 | 225792 / 44100 / 5.120000000 | 0.000000000 |

M4Aのsource由来の実測長がcodecのため1.386666667秒 / 5.120000000秒となったが、同一sourceからのanalysis / MMD間差は全件0である。MP3/M4A encoder不足、変換失敗、比較不能、閾値超過のskipは発生していない。

locatorは既存 `locate_ffmpeg_tools()` を使用し、実測sourceは `repo_local`。解決pathは `D:\Kanna_Works\MMD_AppWork\MMD_AutoLipTool-dev\MMD_AutoLipTool_Antigravity\FFmpeg\bin\ffmpeg.exe` / `ffprobe.exe`、両方のversionは `N-123549-g70537ec8e6-20260318` である。integration testの探索実装に固定repo pathは使用していない。`PATH` fallbackは既存locatorの契約として保持され、今回の実測ではrepo-localが優先された。

### 15.4 受入判定・未検証境界

- `MS26-B2-001` automated cross-boundary regression: mainレビュー補修後も passed。`MS26-B2-002` test-only duration finding: negative oracle、実FFmpeg matrix、source identity、独立read-backが揃い、B2範囲では resolved。
- mainレビュー指摘6件は、P2-1（宣言data sizeの不完全frame tail見逃し）、P2-2（probe前後のsource hash不足）、P2-3（normal runnerのWAV 48000 / M4A stereo不足）、P3-1（固定FFmpeg pathとtool identity不足）、P3-2（実行者・wait設定の記録誤差）、P3-3（hash一覧・command ID・cross-reference・diff証拠不足）として記録し、すべて§15.5の限定補修と再検証で解消した。初回・中間失敗は§15.2から削除していない。
- 実装済み: test-only helper、unit negative / boundary cases、実FFmpeg integration matrix、既存runner経路の検証。
- 不変: `src/` production code、保存validator、DTO、GUI / worker、error code、個別保存・一括出力、runtime JSON / INI、dependency / lock / build / package。
- 未検証: Windows 11 GUI手動確認、実MMDのVMD / WAV load・play・morph・timing・visual、Python 3.11 / 3.12、Whisper実model解析、MS26-B4 revalidation / Closeout、MS27 package / release readiness。
- Git操作: stage、commit、branch変更、merge、push、tag、releaseは未実施。次工程はメインによる最終diffレビュー後のユーザー判断であり、B3 / B4へ自動移行しない。

### 15.5 main統合レビュー指摘と補修再検証（2026-09-09）

| finding ID | priority | 指摘 | 限定補修 / 解消根拠 |
| --- | --- | --- | --- |
| `MS26-B2-RF-001` | P2 | `wave.readframes(frames)`はRIFF data sizeのblock-align未満の余剰tailをfloor divisionで隠す | helperでRIFF `data` declared sizeとblock alignを独立確認し、mono 3 bytes / stereo 5 bytesのnegativeを追加。`B2-R01`が補修前の再現記録、`B2-R03`が補修後unit証拠 |
| `MS26-B2-RF-002` | P2 | probe前と2変換後の入力bytes identity比較がなく、入力差替えを検出できない | SHA-256をprobe前に取得し、probe直後・analysis変換後・MMD変換後に同一値を確認。source replacement negativeをunitへ追加 |
| `MS26-B2-RF-003` | P2 | WAV stereo 48000 Hz / M4A stereoがcancellable-onlyで、normal runner経路が欠落 | 20通常runner条件へ4条件を重複追加し、normal 20 + cancellable 4 = 24測定caseとして両経路を記録 |
| `MS26-B2-RF-004` | P3 | integrationがrepo内FFmpeg固定pathを使用し、locator source / resolved path / versionを記録しない | `locate_ffmpeg_tools()`のrepo優先・PATH fallbackを使用し、resolved source/path/versionを出力・§15.3へ記録 |
| `MS26-B2-RF-005` | P3 | B1/B2の実行者をCodex mainと誤記し、config v2 waitと実行API v1 waitを区別していない | 実装・テストはサブエージェントCurie、統合レビューは親メインと区別。config v2のmin/default/maxと、親が指定したAPI v1 `timeout_ms=600000`を明記。残っていた未起動の誤記は親メインが最終補正 |
| `MS26-B2-RF-006` | P3 | hash identity、固有command ID、正確なcommand / common prefix、diff evidence、B1 ledger参照が不足 | §15.2の`B2-Cxx` / `B2-Rxx`、§15.5、§16.4、7対象pathのhash対象一覧、B1 ledgerのB2参照を追加・修正 |

補修の実行履歴は次のとおりである。`B2-R01`はpartial-tail negativeを先に実行した再現、`B2-R02`はhelper補修後に期待regexだけが不一致だった中間失敗、`B2-R03`はunit 25件の補修後pass、`B2-R04`はintegration 24/24の補修後pass、`B2-R05`〜`B2-R11`はfull pytest・compileall・tracked / untracked diff check・final hashの補修後証拠である。

最終working tree identityの対象pathは次の7件で、値は全編集・検証完了後に実行する`B2-R11`のSHA-256出力を証拠とする。

1. `tests/ms26_wav_duration_helpers.py`
2. `tests/test_ms26_b2_wav_duration.py`
3. `tests/test_ms26_b2_wav_duration_integration.py`
4. `docs/Implementation_Plan/MS26-B1_Implementation_Plan.md`
5. `docs/Implementation_Plan/MS26-B2_Implementation_Plan.md`
6. `docs/Implementation_Plan/MS26_Block_Breakdown.md`
7. `docs/MS20_and_Beyond_Index.md`

### 15.6 親メインの最終照合

親メインは3 testファイルと4文書の差分を確認し、RF-001〜006の補修を照合した。最終編集は実行者・台帳の列構造・表の連続性・証拠参照の文書補正のみで、テストおよびproduction codeは再検証後から不変である。既存責務別gateの対象コード・testは変更しておらず初回結果を保持し、追加helperの影響はB2-R03/R04とfull gate B2-R05で再検証した。

再検証済みtestのSHA-256（Curie取得値、親メイン照合対象）:

| path | SHA-256 |
| --- | --- |
| `tests/ms26_wav_duration_helpers.py` | `3E739DC6D3C448081E96D1D6A1F0CB87A72D026E227B3416B5991AE606058C7E` |
| `tests/test_ms26_b2_wav_duration.py` | `C209C37232949D80D0AD02BD944C2EABC60F6D504BFCD557047926E53D12DD9D` |
| `tests/test_ms26_b2_wav_duration_integration.py` | `AB81BCDBC213620EA50915C05052FA762202903B0702B5193C7B513DAADBEE90` |

B2-R11の文書hashは親メイン補正前の値である。文書のみの補正はruntime/test証拠を失効させず、最終tracked diff checkとtest hash照合を親メインが別途行う。B2-R05のdaemon例外見出しは観測事実として残すが、原因や既存性はこの作業では確定していない。exit 0と例外なしを同一視しない。
