# MS25 Block Breakdown

## 1. 文書情報

- 文書名: MS25 Block Breakdown
- 対象マイルストーン: MS25 MMD Delivery Package Export
- 作成日: 2026-08-28
- 状態: MS25-B1〜B6実装済み、MS25-B7回帰・自動検証・文書同期済み。MS25 Closeout Aを判定済み。実MMD確認、Python 3.11 / 3.12、MS27配布確認は未検証またはdeferred
- 対象ブランチ: `feature/MS25-implementation`
- 現在のベースコミット: `61a2182 Finalize MS24 Closeout A`
- 前提となる完了状態: MS24 Closeout A
- 承認済みの成果物命名:
  - `<audio_stem>_lip.vmd`
  - `<audio_stem>_mmd.wav`
  - `<audio_stem>_report.txt`
  - 既定directory名: `<audio_stem>_MMD`
- 本文書の権限: MS25の責務分割、状態契約、出力契約、テスト方針、受け入れ条件を定義する。実装、テスト追加、GUI変更、設定変更、依存関係変更、stage、commit、pushは本文書の作成では行わない
- 現在状態（2026-09-04）: B5のproduction code、test code、GUI変更は`bb9c60d Complete MS25-B5 delivery package GUI integration`としてcommit済みである。B5専用・関連回帰は`29 passed`、全pytestは`1015 passed, 4 skipped`でprocess exit code `0`。B6のproduction code、test code、GUI変更は`5300905 Implement MS25-B6 delivery recovery hardening`としてcommit済みである。B6専用testは`26 passed`、B6直接回帰は`134 passed, 2 skipped`、指定cross-boundary回帰は`94 passed`、全pytestは`1041 passed, 4 skipped`で、いずれもprocess exit code `0`。B6のWindows実filesystem junction collisionとsharing violationはskipなしで確認済みで、ユーザー報告の手動GUI確認も通過している。B7は検証HEAD `0b25c5c Document MS25-B7 implementation plan`で、B6 required gate `26 passed`、MS25 aggregate `160 passed, 2 skipped`、cross-boundary `322 passed`、全pytest `1041 passed, 4 skipped`、`compileall -q src tests`をprocess exit code `0`で確認した。4 skipはsymlink作成権限のないWindows環境（WinError 1314）に限定され、required Windows fault gateにはない。B7でREADME、配布用readme、4正文仕様を照合し、必要事項が反映済みのため変更不要と判定した。B7文書同期とMS25 Closeout A判定を完了し、実MMD確認、Python 3.11 / 3.12、MS27配布確認は後続またはdeferredである。B6計画書の初版は`9841de4 Document MS25-B6 implementation plan`として作成済みである。
- レビュー来歴: 初回策定時にSol Highサブエージェントへ読み取り専用の短縮独立調査を委任したが、その時点では最終回答を回収できなかった。策定後に同じ監査目的でSol High / reasoning highの完全監査を実施し、P1 / P2 / P3指摘を受領した。本改訂は、その完全監査結果をメインエージェントが現行リポジトリと再照合し、計画契約へ反映したものである。その後、ユーザー指示によりサブエージェントは終了済みである

## 2. 参照した正本文書と現行ベースライン

### 2.1 正本文書

- `docs/MS17_and_Beyond_Index.md`
- `docs/MS20_and_Beyond_Index.md`
- `docs/MS20_and_Beyond_Roadmap.md` §12〜§15
- `docs/Implementation_Plan/MS24_Block_Breakdown.md`
- `docs/Implementation_Plan/MS24-B7_Implementation_Plan.md`
- `docs/Pipeline_Data_Contract_Specification.md`
- `docs/Error_Handling_Specification.md`
- `docs/VMD_Output_Specification.md`
- `docs/GUI_State_Theme_Specification.md`
- `README.md`
- `readme_mmdautolip.txt`

### 2.2 現行実装の確認対象

- `src/core/pipeline.py`
- `src/core/diagnostic_report.py`
- `src/core/output_diagnostics.py`
- `src/core/mmd_wav_export.py`
- `src/core/audio_convert.py`
- `src/core/settings_store.py`
- `src/gui_wx/app_controller.py`
- `src/gui_wx/main_frame.py`
- `src/gui_wx/right_pane.py`
- `src/gui_wx/ui_state.py`
- `src/gui_wx/output_diagnostics_adapter.py`
- `src/gui_wx/audio_worker.py`
- `src/gui_wx/worker_state.py`
- `src/vmd_writer/writer.py`
- `pyproject.toml`

### 2.3 現行ベースラインの事実

- 個別のVMD保存、MMD用WAV出力、診断レポート保存はそれぞれ存在し、MS25-B5実装により3成果物を専用directoryへまとめる一括出力導線も接続済みである。
- VMD保存は`prepare_current_effective_output()`が返す現在の`EffectiveShapePlan`と、現在のsaveability / fingerprintを基準にする。既に保存されたVMDを再利用する導線はない。
- `write_morph_frames_vmd()`は指定された出力ファイルへ直接書き込む。既存の最終directoryを保護するには、最終destinationとは別のstaging directoryへ書く必要がある。
- `export_mmd_wav()`は入力音声の`probe_result.source_path`を使い、内部解析WAVとは別のMMD用WAVを生成する。MS25でもこのaudio role分離を維持する。
- `write_diagnostic_report()`は既存レポートを一時ファイル経由で置換し、書込み失敗時に既存レポートを保護する。MS25では同じ診断snapshotをstaging内のレポートへ渡す。
- `OutputDiagnosticsSnapshot`には、現在の入力、timing plan、実効writer状態、preset、profile、resolved morph set、Whisper diagnostics summary、projection generation、fingerprintが含まれる。
- MS24で、Whisperのselected / active / loaded / analysis identity、package version、gate status、failure分類、diagnostic snapshotの共通投影が実装済みである。MS25はWhisperモデル選択契約を再実装しない。
- `ms21-effective-output-v1` fingerprintは既存契約として維持され、Whisper管理診断情報をfingerprintへ混入させない。MS25のfilesystem commit可否は、開始時fingerprintとcommit直前にcurrent stateから再構築したfingerprintの一致で判定する。`projection_generation`はUI投影とlate-result discard専用であり、filesystem commit可否の根拠には使わない。
- 現行の個別保存先設定はVMD、MMD用WAV等の役割別であり、MS25専用の親directory設定keyはない。MS25では新しいINI設定keyを追加せず、batch parent directoryをsession-onlyとする。
- `docs/MS20_and_Beyond_Index.md`の冒頭の現在地表記とMS25-B5実装記録をcurrent stateの正本として扱う。本文の過去履歴行は時系列記録として保持し、現在状態と混同しない。
- `presets.json`、`profiles.json`、`MMD_AutoLipTool.ini`はruntime user dataであり、本文書の策定中およびMS25実装時に直接編集、コピー、stageしない。

## 3. MS25の目的

現在の編集結果と入力音声から、MMD利用者がそのまま受け渡し・確認できる次の3成果物を、一つの専用directoryへ一括生成する。

1. 編集反映済みのVMD
2. MMD仕様のWAV
3. 現在の解析条件と診断状態を記録したレポート

3成果物の生成、検証、確定をtransactionとして扱い、commit完了前に承認済みのfinal directory名で成果物を公開せず、既存destinationを変更しない。finalと同じ親directoryに置く不透明なtemporary staging directoryはOSやExplorerから見える可能性があるが、成功成果物として扱わない。

## 4. In Scope

- 現在の有効な`EffectiveShapePlan`からのVMD再生成
- 現在選択されている入力音声からのMMD用WAV再生成
- 現在の診断snapshotからのレポート再生成
- 親directoryの選択
- 編集可能なdelivery directory名の入力
- 音声stemに基づく既定directory名`<audio_stem>_MMD`
- 承認済みの3成果物ファイル名での出力
- temporary / staging directoryでの3成果物生成と検証
- production用VMD read-back validatorによる生成結果検証
- 3成果物がすべて成功した場合だけ最終directoryへ確定する処理
- directory、file、symlink、reparse pointを含む同名destinationの一律衝突検出、既存出力の保護、別名要求
- 生成・検証・cancel・commit失敗時のstaging cleanup
- 入力音声のresolved path / size / `mtime_ns` identity固定と、MMD用WAV生成前後の変化検出
- 個別VMD保存、個別MMD用WAV出力、個別診断レポート保存との共存
- レポートへのpreset、model profile、resolved morph name set、Whisper model identityの記録維持
- wxPythonのBusy、cancel、late-result discard、saveability gateとの統合
- MS25実装後のREADME / MMD利用者向け説明の同期
- MS25対象の自動テスト、既存MS20〜MS24境界回帰、必要な静的確認

## 5. Out of Scope

- `.autolip`等のセッションファイル
- MMDプロジェクトファイルの管理
- MMD本体のdirectory構成管理
- ZIPの必須化、ZIP出力
- 保存後のMMD自動起動
- MS24 Whisperモデル選択契約の再実装
- cloud ASR、音声外部送信、background通信
- Qt / PySide6の復活
- 実MMDでのVMD、WAV、リップ同期確認（MS26）
- PyInstaller onefile、ZIP、最終artifact、package / release readiness（MS27）
- 依存関係の追加または更新
- 既存directoryとのmerge、既存directoryの置換、既存ファイルの上書き
- 個別保存済みVMD、個別出力済みWAV、個別保存済みレポートの流用
- `presets.json`、`profiles.json`、`MMD_AutoLipTool.ini`の直接操作
- push、tag、release

## 6. Block分割

### MS25-B1: 出力契約・現在状態gate

責務:

- 3成果物の固定ファイル名、既定directory名、audio role、出力順序を定義する。
- 一括出力開始時に、現在の有効な`EffectiveShapePlan`、`OutputDiagnosticsSnapshot`、入力音声probeとsource identity、MMD WAV仕様、必要なFFmpeg解決結果、開始時save-state fingerprintを一つのimmutable開始contextとして固定する。
- VMDのsaveability、current timing plan、pending / rebuild状態、入力音声の有効性、診断ERROR状態を確認する。
- 診断WARNING時は、既存の個別VMD保存と同じfingerprint単位の確認を一括出力にも適用する。ユーザーが拒否した場合はdestination選択、Busy遷移、worker開始を行わない。診断ERRORで一括出力を拒否しても、既存のstandalone report保存まで禁止しない。
- 既存の長時間処理確認を一括出力にも適用する。入力音声が300秒を超える場合は、destination選択後かつBusy / worker開始前に一度だけ確認し、拒否時はworkerを開始しない。経過時間timerとworker開始後の再確認は追加しない。
- 現在状態から再生成することを契約化し、既存個別出力を入力にしない。
- `ms21-effective-output-v1` fingerprintの意味を変更せず、Whisper管理診断情報をfingerprintへ追加しない。
- `projection_generation`を開始contextに記録しても用途はUI投影とlate-result discardに限定し、filesystem commit guardには使用しない。commit直前にcurrent stateからfingerprintを再構築し、開始時fingerprintとの不一致をstaleとして拒否する。

完了条件:

- 成功条件と開始時の拒否条件が、coreとGUIの双方から参照できる形で定義されている。
- VMD、MMD用WAV、レポートの入力sourceがそれぞれ明示されている。
- reportとVMDが同じ開始contextに由来することをテストで確認できる。
- Busy遷移やdiagnostics再投影だけではcommit guardがstaleにならず、effective output変更時はstaleになることをテストで確認できる。
- WARNING確認の承認前にworkerが開始されず、拒否時に出力・Busy・個別保存履歴が変化しない。

### MS25-B2: Delivery Package core orchestration

責務:

- 親directory、`audio_stem`、編集可能なdirectory名をWindows向け規則で検証する。
- 親directoryの直下にstaging directoryを作成し、同一volume上で最終directoryへ確定できる構成にする。
- staging内へVMD、MMD用WAV、レポートを生成し、各ファイルを検証する。
- directory、file、symlink、reparse pointを含め、final pathに既存entryが一つでもあれば処理開始前のcollisionとして拒否する。empty directoryも例外にしない。
- 3件すべての生成・検証と入力音声identity再確認が成功した後、coreは`awaiting_commit_guard`へ入り、注入されたpre-commit guardからjob IDと開始fingerprintに結び付いたcommit authorizationを得る。authorization取得後だけ、既存destinationを置換しないno-clobber directory renameでstagingをfinalへ確定する。事前検査後にdestinationが作成された場合のrename失敗もcollisionとする。
- GUIの個別保存処理から独立したcore orchestration、delivery専用cancel token、terminal result型を持つ。
- no-clobber renameの開始をcommit線形化点とする。線形化点より前に受理したcancelはcommitせずcleanupへ進み、線形化点の開始後またはcommit成功後に到着したcancelは成功済みcommitをcancelへ上書きせず、finalを削除しない。

完了条件:

- core単体でGUIなしに成功、生成失敗、検証失敗、cancel、destination衝突を再現できる。
- final destination entryが存在しない場合、stagingからfinalへの確定が一度のno-clobber commitとして行われる。
- final directoryへ生成途中のファイルを直接書き込まない。
- terminal resultが`committed`、`final_path`、`staging_path`、primary status / error、cleanup statusを曖昧なく表現し、cancelとcommit成功を同時に報告しない。
- core単体テストではpre-commit guardを注入でき、GUI stateへ依存せずauthorization成功・stale・cancelを再現できる。

### MS25-B3: 3成果物生成アダプター

責務:

- VMDは現在の`EffectiveShapePlan`、resolved ordered morph names、adjustment stateを使ってstagingへ生成する。
- MMD用WAVは入力音声の`probe_result.source_path`から生成し、内部解析WAVを代用しない。
- レポートは同じ開始時点の`OutputDiagnosticsSnapshot`からstagingへ生成する。
- 既存のVMD writer、MMD WAV exporter、diagnostic report writerの責務を再利用し、各writerの既存validationとcleanupを損なわない。
- VMD生成後はproduction用read-back validatorで、VMD headerとmodel field、bone frame count `0`、期待morph record count、各recordのmorph名・frame index・value、末尾のcamera / light / self-shadow / IK count `0`、truncation、期待外の末尾byteがないことを確認する。validatorはtest helperへ依存させず、`src/vmd_writer/validator.py`を新規候補とする。
- MMD用WAV生成の直前と検証後にsource identityを再取得し、開始contextのresolved path / size / `mtime_ns`と一致しなければ`source_audio_changed`として失敗させる。
- 生成後に、ファイル存在、非空サイズ、VMD / WAV / UTF-8レポートの形式を確認する。

完了条件:

- 成果物名が常に承認済みの3名へ固定される。
- VMDのフレーム内容が個別保存済みファイルではなく現在の有効状態に一致する。
- WAVのchannel、sample rate、sample formatが`MMD_WAV_SPEC`に一致する。
- レポートのpreset / profile / morph set / Whisper identityが開始snapshotと一致する。
- VMD read-backが期待recordと一致せず、truncatedまたは余分な末尾dataがある場合はcommitされない。
- WAV生成前後に入力音声identityが変化した場合はcommitされない。

### MS25-B4: 診断・identity・レポート契約

責務:

- MS24の`WhisperDiagnosticsSummary`をそのままレポートへ伝播し、selected / active / loaded / analysis identityを混同しない。
- preset、model profile、resolved morph name set、Whisper model name / identity、package version / gate status、projection generationの既存記録を維持する。
- profile未使用と既定日本語morph setを省略しない。active preset、profile identity（未使用時は`no_profile`等の明示値）、resolved morph set identity / ordered names、Whisper selected / active / loaded / analysis identityを、すべての一括出力レポートへ必ず記録する。このため`src/core/diagnostic_report.py`をMS25の変更候補とする。
- package専用のmanifestや新しいfingerprint schemaを追加せず、既存レポートの意味を保つ。
- raw exception、traceback、credential、URL、不要な絶対一時pathを通常のユーザー向け出力へ漏らさない。
- 生成開始時刻と診断snapshotの対応を固定し、3成果物間の診断時点をずらさない。

完了条件:

- レポートがVMDの生成元と同じsnapshotの記録であることを確認できる。
- Whisperのsemantic / runtime identityと管理用diagnosticsが既存契約どおり分離される。
- レポート生成失敗時にworkspaceの診断状態が壊れない。
- profile未使用かつ既定morph setの場合でも、preset / profile / morph set / Whisper identityの各欄が存在する。

### MS25-B5: GUI・worker・状態統合

責務:

- MMD一括出力の起動導線と、親directory選択・編集可能なfolder名入力のUIを追加する。
- folder名の既定値を`<audio_stem>_MMD`とし、利用者が編集できるようにする。
- destinationの候補、入力状態、saveability、必要な音声probe / FFmpeg状態を起動前に検証する。
- 診断WARNINGの場合は既存の個別VMD保存と同じfingerprint単位の確認をdestination dialogより前に行う。拒否時はworkerを開始せず、ERROR時の一括出力拒否をstandalone report保存へ波及させない。
- destination dialog終了後にstart gateとfingerprintを再確認する。WARNING確認済みfingerprintと開始contextのfingerprintが異なる場合は、新しいfingerprintに対してgate / WARNING確認をやり直し、確認なしにworkerを開始しない。
- 入力音声が300秒を超える場合は、destination dialog後かつBusy / worker開始前に既存の長時間処理確認を一度だけ行う。確認拒否時はworkerとfilesystem処理を開始せず、経過時間timerやworker開始後の再確認は追加しない。
- `DELIVERY_PACKAGE`等の明示的なworker kindとdelivery専用terminal resultを追加し、MMD WAV単独出力および既存PROBE / ANALYSIS_WAV / MMD_WAV terminal契約と分離する。汎用`AudioWorker`を再利用する場合も、task完了後のcancel flagだけでcommit済み結果をcancelへ上書きしない専用分岐を持つ。
- Busy中は一括出力、個別保存、workspace reset等の競合操作をロックし、delivery terminal resultと必要なcleanup完了を受けるまでbusyを解除しない。
- job id、worker kind、UI投影用`projection_generation`を使い、古い結果や終了後のlate resultがcurrent UI stateを変更しないようにする。これらはfilesystem commit可否には使用しない。
- workerが`awaiting_commit_guard`へ到達したら、`wx.CallAfter`等でUI threadへ照会し、UI thread上でcurrent stateからsave-state fingerprintを再構築する。開始fingerprint、current fingerprint、active job ID、worker kindが一致する場合だけcommit authorizationを返す。worker threadから`MainFrame`や可変GUI stateを直接読まない。照会中もBusyを維持し、cancel / closeを受けた場合はauthorizationを発行しない。
- window close時、commit線形化点前ならcancelを要求してterminal / cleanup完了までwindow破棄を待つ。commit線形化点開始後はcommit terminalを待ち、成功済みfinalをcancel cleanup対象にしない。待機中は重複closeと新規操作を拒否する。
- batch parent directoryを新しいINI設定へ自動保存しない。既定値は既存の入力音声親directoryまたは既存の出力先情報から安全に導出し、実装時に既存導出規則を再確認する。
- 一括出力の成功、失敗、cancelのいずれでも、個別VMD保存先、個別MMD WAV保存先、個別report保存先の履歴を更新しない。batch parent directoryはsession-onlyとする。

完了条件:

- GUIから一括出力を起動でき、成功・失敗・cancelがBusy終了まで一貫して投影される。
- 個別VMD保存、個別MMD用WAV出力、個別レポート保存が従来どおり使用できる。
- UI threadがVMD生成、FFmpeg処理、レポート書込みを同期実行しない。
- close中もworker terminalとfilesystem結果が食い違わず、window破棄後に新しいfinal commitが発生しない。

実装・検証状況（2026-09-03）:

- 一括出力menu、destination dialog、delivery専用worker、Busy / cancel / close lifecycleを実装済みである。
- B5および関連worker / GUI回帰は`29 passed`、全pytestは`1015 passed, 4 skipped`でprocess exit code `0`。`compileall -q src tests`と`git diff --check`もexit code `0`である。
- ユーザーから、提示したB5手動GUIテスト通過の報告を受領した。これはユーザー確認として扱い、Codex自身のGUI実行結果とは扱わない。
- false `delivery_busy` を起こすgeneric worker stateとworker referenceの不整合をP3として修正し、同種のstart guard回帰を追加確認した。
- B6のWindows fault matrix、B7のfull cross-boundary regression / closeout、実MMD確認、MS27のpackage / release readinessは後続である。

### MS25-B6: transaction・衝突・失敗復旧

責務:

- final pathにdirectory、file、symlink、reparse pointのいずれかが存在すれば、empty / non-emptyを区別せずcollisionとして拒否し、別名を要求する。壊れたsymlink等を見落とす`Path.exists()`だけに依存せず、`lexists`相当とWindows reparse point判定を含める。
- dialog確定後からfinal commitまでに同名destinationが作られた場合も、no-clobber renameの失敗をcollisionとして扱い、既存destinationを保護する。事前`exists()`確認だけを排他制御とみなさない。
- VMD、WAV、レポートの各生成失敗、形式validation失敗、cancel、permission / locked / invalid path、final commit失敗を分類する。
- OS faultは例外型・`winerror`・`errno`・cause chainで分類し、`PermissionError`等は`output_permission_denied`、分類対象外のcommit I/Oは`delivery_commit_failed`へ収束させる。既存B2 commit回帰の期待値同期と分類対象外I/Oの回帰はB6実装時に明示する。
- commit線形化点前の失敗または受理済みcancelではstagingだけをbest effort cleanupし、final directoryを作成しない。既存の個別出力や既存packageを削除・置換しない。
- cleanup自体が失敗した場合はprimary failure / cancelを保持したままcleanup statusを`partial_output_cleanup_failed`として併記し、成功扱いにしない。cleanup例外をcancelへ吸収しない。
- commit直前にGUI adapterがUI thread上のcurrent stateからsave-state fingerprintを再構築し、job IDに紐付けたcommit authorizationをcoreへ返す。開始fingerprintと不一致、job無効化、cancel / close受理済みならauthorizationを発行せずstaleまたはcancelとしてcommitを拒否する。`projection_generation`の変化だけでは拒否しない。
- commit線形化点開始後にcancelが到着した場合、renameの成否をterminal resultへ反映してから終了する。commit成功なら`committed=true`でfinalを保持し、commit失敗なら`committed=false`でstaging cleanupへ進む。
- packageの生成順、validation順、source identity確認、cancel受理境界、commit線形化点、cleanup順を固定し、部分成果物の残存をテスト可能にする。

完了条件:

- intentional failureのすべてで既存出力がbyte-for-byteで維持される。
- final directoryには成功時だけ3ファイルが現れ、失敗時にpartial final directoryが残らない。
- empty / non-empty / file / symlink / reparse point collision、TOCTOU、commit前・commit中・commit後cancel、cleanup failure、window closeがテストで再現される。
- B6専用のWindows collision、failure recovery、GUI recoveryテストを追加し、B6の必須gateで実行できる。B7はこのテスト群を実行したうえで、full cross-boundary回帰と文書同期を担当する。

実装・検証状況（2026-09-04）:

- staging identity再確認、OS fault分類、no-clobber commit再検査、cleanup例外のterminal化、delivery close状態のreconciliationを実装した。
- B6専用test 3ファイルは`26 passed`、B6直接回帰は`134 passed, 2 skipped`、指定cross-boundary回帰は`94 passed`、全pytestは`1041 passed, 4 skipped`で、いずれもprocess exit code `0`である。
- Windows実filesystemのjunction collisionとsharing violationを各1件、skipなしで確認した。`compileall -q src tests`と`git diff --check`もprocess exit code `0`である。
- ユーザーから提示したB6手動GUI確認の通過・問題なしの報告を受領した。これはユーザー確認の範囲に限定して記録し、Codex自身のGUI実行結果とは扱わない。
- B6のstage / commitは`5300905`で完了している。B7のfull regression / closeout、README等の最終文書同期、実MMD確認、MS27配布確認は未完了または後続である。

### MS25-B7: 回帰・利用者向け文書・Closeout準備

責務:

- B6で追加したMS25専用のcore / GUI / failure recoveryテストと既存のcross-boundary回帰を実行する。B7でcoverage不足が判明した場合はfinding化し、B7内でtest codeを追加・変更せず、別repair plan / repair implementationへ分離する。
- MS20〜MS24のdiagnostics、effective output、VMD、MMD WAV、worker terminal、textless pipeline回帰を、§11.4に列挙した既存testファイル単位で実行する。
- `README.md`と`readme_mmdautolip.txt`の一括出力の利用方法、3ファイルの意味、folder名変更、collision、失敗時の保護、MMD確認の留保を現行挙動と照合する。必要事項が反映済みなら変更しない。
- `docs/Pipeline_Data_Contract_Specification.md`、`docs/GUI_State_Theme_Specification.md`、`docs/Error_Handling_Specification.md`、`docs/VMD_Output_Specification.md`の開始context、fingerprint guard、delivery terminal、collision / cancel / cleanup、VMD read-back契約を現行code / testと照合する。
- roadmap / index / milestone状態の表記を、実装済み・検証済み・未検証に合わせて更新する。READMEと各正文書の同期確認は実装と検証が完了した後に行う。
- MS26の実MMD確認、MS27のpackage / release readinessへ引き継ぐ未検証事項を整理する。

完了条件:

- 自動検証、diff監査、文書同期が実際の到達状態と一致する。
- 実MMD、Python 3.11 / 3.12、PyInstaller最終artifactなど、未実施の確認を検証済みと記載しない。

## 7. 依存順と責務境界

推奨実装順は次のとおりとする。

```text
B1 出力契約・状態gate
  -> B2 core orchestration
      -> B3 成果物生成アダプター
          -> B4 diagnostics / report contract
              -> B5 GUI / worker integration
                  -> B6 transaction / failure recovery hardening
                      -> B7 regression / docs / closeout
```

- B1は既存の`EffectiveShapePlan`、`OutputDiagnosticsSnapshot`、`projection_generation`、save-state fingerprintの意味を変更しない。fingerprintはfilesystem commit guard、`projection_generation`はUI投影 / late-result専用とする。
- B2はfilesystem transaction、注入可能なpre-commit guard、no-clobber最終確定、commit線形化点、delivery terminal resultを所有する。GUIはstaging pathやcommit順序を直接操作しない。
- B3は各成果物の生成とproduction validation、入力音声identity再確認を所有する。VMD、MMD用WAV、レポートの入力roleを混ぜない。
- B4は診断identityとレポート表現を所有する。Whisper選択・loader・解析そのものはMS24の責務である。profile未使用や既定morph setも明示記録する。
- B5はdialog、WARNING確認、Busy、worker callback、UI thread上のpre-commit fingerprint再構築とauthorization、window close、current-state projection、個別保存履歴の非変更を所有する。長時間処理はUI threadで実行しない。
- B6は既存出力保護、全種類のdestination collision、TOCTOU、cleanup、cancel / commit線形化、shutdown復帰を横断して検証する。
- B7は回帰と利用者文書を所有する。MS26 / MS27の作業を前倒ししない。

## 8. データ契約

### 8.1 開始context

一括出力開始時に、少なくとも次の値を一つのimmutableな処理contextへ束ねる。

- 入力音声のresolved source path、probe結果、size、`mtime_ns`、取得可能な場合のfile identity
- 現在の`EffectiveShapePlan`
- 現在の`OutputDiagnosticsSnapshot`
- UI投影 / late-result discard用の`projection_generation`
- 開始時のsave-state fingerprint
- VMD writer parametersとresolved ordered morph names
- MMD WAV仕様と解決済みFFmpeg path
- 出力親directoryと検証済みfolder name
- 成果物の固定ファイル名
- レポート生成時刻

coreが全成果物の検証後に`awaiting_commit_guard`へ入った時点で、GUI adapterはUI thread上のcurrent stateからsave-state fingerprintを再構築し、開始時fingerprintと比較する。worker threadは可変GUI stateを直接読まない。一致し、active job ID / worker kindも有効で、cancel / closeが受理されていない場合だけjobに結び付いたcommit authorizationを返す。不一致ならstale resultとしてcommitを拒否する。Busy遷移、表示更新、diagnostics再投影による`projection_generation`変化だけではcommitを拒否しない。`projection_generation`はjob id / worker kindとともにlate callbackのUI反映判定だけに使う。

入力音声identityはMMD用WAV生成の直前と生成・検証後に再取得する。resolved path、size、`mtime_ns`、取得できるfile identityのいずれかが開始contextと異なる場合は`source_audio_changed`としてcommitしない。MS25では全入力音声のcontent hash計算は要求せず、同一size・同一`mtime_ns`・同一file identityを意図的に維持したbyte置換までは検出保証しない。この保証範囲を利用者向け成功説明へ過大表示しない。

### 8.2 出力directory

- 親directoryは存在し、書込み可能でなければならない。
- folder nameは編集可能だが、空文字、path separator、`.`、`..`、control character、Windowsで使用できない文字、末尾の空白・`.`、`CON` / `PRN` / `AUX` / `NUL` / `COM1`〜`COM9` / `LPT1`〜`LPT9`等の予約device nameを、大文字小文字や拡張子風suffixにかかわらず受け付けない。
- `audio_stem`とfolder nameはUnicodeを保持し、ASCII化、置換文字付与、切り詰め、suffix付与などの暗黙renameを行わない。無効な場合はユーザーに名前の修正を要求する。
- `<audio_stem>_lip.vmd`等のsuffixと拡張子を付けた各file component、folder component、親directoryと結合したstaging / final / 成果物pathが、MS25の固定path長契約を超えないことを開始前に検証する。契約は、Windowsの通常filesystem APIでの互換性を優先し、各componentをUTF-16 code unit 255以下、絶対staging / final / 成果物pathをNUL終端を含めずUTF-16 code unit 240以下とする。staging名生成時の最大suffixもこの上限へ含める。超過時は`output_path_invalid`として暗黙短縮せず拒否する。
- final directory名は親directory直下に限定する。ユーザー入力を複数階層のpathとして解釈しない。
- staging directoryは同じ親directoryに作成し、別volumeへのcopy後deleteをcommit手段にしない。
- final pathにdirectory、file、symlink、reparse pointを含むentryが存在すれば、empty / non-emptyを区別せずcollisionとして拒否する。事前判定は壊れたsymlinkを見落とさない`lexists`相当とWindows reparse point判定を含める。stagingからfinalへの確定も既存entryを置換しないno-clobber renameを用い、commit時競合をcollisionへ正規化する。
- final directoryの内部には成功時に次の3ファイルだけを置く。

```text
<audio_stem>_MMD/
  <audio_stem>_lip.vmd
  <audio_stem>_mmd.wav
  <audio_stem>_report.txt
```

- ZIP、session file、manifest、追加cacheは作成しない。

### 8.3 既定名とstem

- `audio_stem`はMMD用WAVの元となる入力音声ファイル名から拡張子を除いたstemとする。
- 入力音声がない状態ではMMD Delivery Packageを開始できない。
- stemは§8.2と同じWindows component検証を通す。安全でない場合は`output_path_invalid`としてfolder nameと成果物名を生成せず、勝手な別stemへの変更は行わない。

### 8.4 生成元の対応

| 成果物 | 生成元 | 使用禁止の代替入力 |
| --- | --- | --- |
| `<audio_stem>_lip.vmd` | 現在の`EffectiveShapePlan`、writer parameters、resolved morph names | 個別保存済みVMD、古いtiming plan、表示用値だけの再構成 |
| `<audio_stem>_mmd.wav` | 入力音声の`probe_result.source_path`、MMD WAV exporter | 内部解析WAV、既存個別MMD WAV |
| `<audio_stem>_report.txt` | 同じ開始時点の`OutputDiagnosticsSnapshot` | 古いreport、個別保存済みreport、別解析のsnapshot |

### 8.5 レポートidentity

既存レポートの項目を維持し、少なくとも次を記録する。

- active preset ID / name（未選択状態が既存契約上あり得る場合も明示値を出す）
- model profile ID / name / baseline / resolution（profile未使用時は`no_profile`等の明示値を出す）
- resolved morph set ID / name / ordered morph names（既定日本語morph setでも省略しない）
- Whisper selected / active / loaded / analysis identity
- Whisper manifest、package version、gate status、failure分類
- generation / adjustment / saveability / diagnosticsの現在状態

package専用のfile hash、package manifest、最終directoryのabsolute pathは、既存diagnostic reportの責務を変更するためMS25では追加しない。必要になった場合は別の契約変更として扱う。

### 8.6 Delivery terminal result

core orchestrationは、GUIのcancel flagやcallback種別からfilesystem結果を推測させず、少なくとも次を持つ一つのterminal resultを返す。

- `committed`: final directoryへのno-clobber commitが成功したか
- `final_path`: commit成功時のfinal path。未commit時は`None`とし、未確定のpathを成功結果として扱わない
- `staging_path`: cleanup対象またはcleanup失敗時に残存し得るstaging path。通常のユーザー通知では不要な絶対pathを露出しない
- primary status / error: `success`、`cancelled_before_commit`、collision、stale、source変更、生成 / validation / commit失敗等
- cleanup status: `not_required`、`completed`、`partial_output_cleanup_failed`
- commit phase: `before_commit`、`awaiting_commit_guard`、`commit_started`、`committed`等、cancelとcommitの前後関係を判定できる値

primary failureとcleanup failureは別fieldで保持する。cancel中にcleanupが失敗してもprimary statusだけで成功・完全cleanupと誤認させない。`committed=true`のresultをcancel callbackへ変換せず、finalをcleanup対象にしない。

## 9. 状態遷移

```text
Idle
  -> Candidate fingerprint + Start gate / WARNING confirmation
     - invalid / ERROR / WARNING rejected: safe rejection, no dialog, no worker, no output mutation
     - valid / WARNING accepted: Package dialog
  -> Destination gate
     - invalid / existing entry collision: dialog remains or safe rejection, no worker, no output mutation
  -> Start gate / fingerprint revalidation
     - changed: return to WARNING confirmation for the new fingerprint, no worker
     - valid and unchanged: immutable start context + Busy + delivery worker started
  -> Staging
  -> VMD generated and validated
  -> Source audio identity pre-check
  -> MMD WAV generated and validated
  -> Source audio identity post-check
  -> Report generated and validated
  -> Awaiting commit guard
     - UI thread rebuilds current fingerprint and validates active job
     - stale / cancelled / closing: no authorization, staging cleanup
     - valid: job-bound commit authorization
  -> Cancel acceptance closes
  -> No-clobber final directory commit (linearization point)
     - committed: Success terminal (`committed=true`)
     - failed: Failure terminal after staging cleanup (`committed=false`)
```

staging作成前のgate rejection、WARNING拒否、dialog cancel、事前collisionではcleanup対象を作らず、Busyにも遷移しない。staging作成後かつcommit線形化点前の次の経路は、すべてstaging cleanupへ進み、final directoryを作成しない。

- VMD generation / validation failure
- MMD WAV generation / validation failure
- source audio identity change
- report generation / validation failure
- commit前に受理されたuser cancel
- save-state fingerprint stale
- final commit failure

commit線形化点開始後のcancelはrenameの成否を変更しない。commit成功ならsuccess terminalを返してfinalを保持し、commit失敗ならfailure terminalとstaging cleanup結果を返す。cancel要求だけを理由にterminal結果を`cancelled`へ上書きしない。

Busy解除は、success、safe failure、cancelおよび必要なcleanupを含むdelivery terminal resultをUIが受け取った後とする。cleanup失敗でもterminal resultは返すが、成功表示にはしない。終了済みjobからのlate resultはjob id / worker kind / UI投影generationでcurrent UI stateへ反映しない。ただしlate-result discardはworkerのfilesystem処理を止める契約ではないため、window closeはterminal到達までwindow破棄を待つ。

## 10. 失敗・復旧契約

| 失敗分類 | 必須動作 | 既存出力 |
| --- | --- | --- |
| `output_path_invalid` / permission | 開始またはstaging作成を拒否し、安全な通知を表示 | 変更しない |
| existing destination collision | empty / non-empty directory、file、symlink、reparse pointを区別せず別名を要求し、処理を開始しない | byte-for-byteで維持 |
| WARNING confirmation rejected | destination dialog、Busy、workerを開始しない。standalone report保存は既存gateに従い引き続き可能 | 変更しない |
| VMD生成 / validation | staging cleanup、successを返さない | 変更しない |
| MMD WAV生成 / validation | staging cleanup、VMDだけを最終化しない | 変更しない |
| `source_audio_changed` | WAV生成前または検証後のsource identity不一致としてcommit拒否、staging cleanup | 変更しない |
| report生成 / validation | staging cleanup、3件を最終化しない | 変更しない |
| cancel before commit | cancel受理、commit禁止、staging cleanup後に`cancelled_before_commit` terminal | 変更しない |
| cancel during / after commit | renameの成否を優先してterminal化。成功済みfinalをcancel扱いで削除しない | commit成功時は新規finalを保持。既存destinationは変更しない |
| save-state fingerprint stale / commit guard invalid | UI threadで再構築したfingerprint不一致、job無効化、cancel / close受理済みとしてauthorizationを発行せず、staging cleanup | 変更しない |
| final commit collision / locked | no-clobber commit失敗として扱い、collisionまたはcommit errorへ分類後にstaging cleanup | 既存を変更しない |
| cleanup failure | primary status / errorを保持し、cleanup statusへ`partial_output_cleanup_failed`を記録して成功扱いにしない | final既存は変更しない |
| window close before commit | cancel要求後、delivery terminal / cleanup完了までwindow破棄を待つ | 変更しない |
| window close during / after commit | commit terminalを待ち、成功済みfinalを保持してから終了する | commit結果どおり |

- `os.replace`等の既存writer内atomic replaceは、各staging fileの内部保護として使えるが、既存final directoryを置換するためには使わない。
- final commitには、既存entryを上書き・merge・削除しないno-clobber directory renameを使用する。事前の存在検査とcommit時の原子的な拒否の両方を持ち、事前検査だけでTOCTOU安全とみなさない。
- final directoryの作成後に個別ファイルを追加する方式は、部分finalを利用者へ見せるため採用しない。
- cleanup失敗時の詳細は診断・ログ側に分離し、raw exception、traceback、credential、不要な一時pathを通常通知へ出さない。
- input identityの保証はresolved path / size / `mtime_ns` / 取得可能なfile identityまでとし、content hashを計算しないことによる検出限界をbyte-for-byte完全保証と表現しない。

## 11. テスト方針

### 11.1 B1〜B4 core

- 既定directory名と3成果物名の決定的な生成
- Windows不正`audio_stem` / folder name、空文字、control character、path traversal、予約device nameと拡張子風suffix、末尾空白・`.`、component長255 UTF-16 code unit超過または絶対path長240 UTF-16 code unit超過の拒否
- 有効な日本語・Unicode名の保持と、暗黙rename / ASCII化 / 切り詰めを行わないこと
- input audio、analysis WAV、MMD WAVのrole分離
- 現在のeffective shape planからのVMD再生成
- 個別保存済みファイルを変更してもpackage内容へ影響しないこと
- report snapshotとVMD生成contextの一致
- profile未使用・既定morph setを含むpreset / profile / morph set / Whisper identityの必須レポート伝播
- VMD production read-back validatorによるheader、bone count、morph records、末尾section count、truncation、余分な末尾byteの検出
- MMD WAVの44.1kHz、stereo、PCM signed 16-bit検証
- 入力音声のresolved path / size / `mtime_ns` / file identityを開始contextへ固定し、WAV生成前後の変化を`source_audio_changed`として拒否すること
- stagingへの書込みとfinal directoryへの直接書込みが分離されること
- Busy / diagnostics再投影による`projection_generation`変化だけではstaleにならず、commit直前に再構築したsave-state fingerprintの不一致ではcommitされないこと
- 300秒超入力の一括出力で、destination選択後・Busy / worker開始前に長時間処理確認が一度だけ行われ、拒否時にworkerが開始されないこと

### 11.2 B5 GUI / worker

- MMD一括出力actionのenable / disable条件
- diagnostics WARNING時のfingerprint単位確認、拒否時にdialog / Busy / workerを開始しないこと、ERROR拒否がstandalone report保存へ波及しないこと
- dialog中にfingerprintが変化した場合、新しいfingerprintに対するgate / WARNING再確認なしにworkerを開始しないこと
- parent directory pickerとeditable folder nameの既定値
- invalid name、cancel、destination collision時の無出力
- Busy中の競合操作ロック
- success / error / cancel / cleanup failureのdelivery terminal projection
- `committed=true`がtask完了後のcancel flagでcancelへ上書きされないこと
- job id、worker kind、UI投影generationによるlate-result discardと、それらをfilesystem commit guardに使用しないこと
- `awaiting_commit_guard`でUI threadがcurrent fingerprintを再構築し、workerがGUI stateを直接読まず、authorization成功・stale・cancel / closeをdeadlockなく処理すること
- window closeをstaging、commit直前、commit中、commit後に要求し、terminal / cleanup前にwindow破棄されず、破棄後にfinal commitが発生しないこと
- 300秒超入力の確認承認・拒否と、確認がBusy / worker開始前に一度だけ行われること
- 個別VMD保存、個別MMD WAV出力、個別report保存の既存回帰
- 一括出力のsuccess / failure / cancelが個別保存履歴を変更せず、batch parent directoryがINIへ追加保存されないこと

### 11.3 B6 transaction / recovery

- empty / non-empty existing directory、file、symlink、reparse pointの一律collisionと既存entry保護
- dialog後、事前存在検査後、no-clobber rename直前に同名destinationを作るTOCTOU競合
- VMDだけ失敗、WAVだけ失敗、reportだけ失敗
- 各validation失敗
- VMD / WAV / report各phase、commit直前、commit開始後、commit成功後のcancel境界
- final commit失敗
- staging cleanup成功、primary failure中のcleanup失敗、cancel中のcleanup失敗
- terminal resultの`committed` / `final_path` / `staging_path` / primary status / cleanup status / commit phase整合性
- 失敗時にfinal partial directoryが残らないこと
- 既存個別出力と既存packageをmerge / replaceしないこと

### 11.4 B7回帰ゲート

実装後、次の順で実行する。既存回帰の最低対象は、抽象的な機能名だけで済ませず次のtestファイルを明示する。

1. MS25-B6専用テスト
   - `tests/test_ms25_b6_windows_collision_faults.py`
   - `tests/test_ms25_b6_delivery_failure_recovery.py`
   - `tests/test_ms25_b6_delivery_gui_recovery.py`
2. 次の既存関連回帰
   - `tests/test_ms20_b5_warning_save_policy.py`
   - `tests/test_ms20_b6_diagnostic_report.py`
   - `tests/test_ms20_b6_report_save_flow.py`
   - `tests/test_ms21_b5_adjusted_vmd_save.py`
   - `tests/test_ms21_b5_effective_output_identity.py`
   - `tests/test_ms23_b6_model_profile_lifecycle.py`
   - `tests/test_ms24_whisper_diagnostics.py`
   - `tests/test_ms17_b7_mmd_wav_export.py`
   - `tests/test_ms17_b7_mmd_wav_failure_cleanup.py`
   - `tests/test_ms17_b8_late_worker_result_discard.py`
   - `tests/test_ms21_b7_audio_worker_terminal.py`
   - `tests/test_wx_ms14_b5_export.py`
   - `tests/test_ms19_b8_workspace_reset.py`
3. VMD writer系`tests/test_vmd_writer_*.py`、`tests/test_pipeline_and_vmd.py`、MS20〜MS24のcross-boundary回帰
4. 全pytest（必須）
5. `compileall -q src tests`
6. tracked差分に対する`git diff --check`。未追跡文書がある場合は、各ファイルに対してstageせず`git diff --no-index --check -- NUL <path>`も実行する。`--no-index`は空デバイスとの差分のためexit code `1`が正常であり、whitespace診断出力がないことを合格条件とする。

各コマンドはpass表示だけでなくprocess exit codeを記録する。実MMD確認、Python 3.11 / 3.12、PyInstaller onefileはMS25の自動回帰合格とは別に未検証として扱う。

## 12. 受け入れ条件

2026-09-04のB7実施時点では、B1〜B6の実装、B6必須Windows fault gate、MS25 aggregate、cross-boundary回帰、全pytest、compileall、文書同期、P1 / P2 / P3 finding再確認までを到達状態として反映する。B5 / B6の手動GUI確認はユーザー報告を範囲限定で再利用し、B7でfresh GUIは実施していない。実MMD確認、Python 3.11 / 3.12、MS27配布確認は引き続き未検証またはdeferredである。

### 機能（B1〜B5検証対象）

- [x] 親directoryを選択でき、folder nameを編集できる。
- [x] 既定folder nameが`<audio_stem>_MMD`になる。
- [x] 成功時のfinal directoryに、承認済みの3ファイルがちょうど1つずつ存在する。
- [x] VMDは一括出力開始時点の編集済みcurrent stateから再生成される。
- [x] MMD用WAVは入力音声からMMD仕様で再生成される。
- [x] VMDはproduction read-back validatorで期待morph recordsと末尾sectionを検証され、truncationや余分な末尾dataがある場合はcommitされない。
- [x] MMD用WAV生成前後に入力音声identityを確認し、resolved path / size / `mtime_ns` / file identityが変化した場合はcommitされない。
- [x] レポートは同じcurrent snapshotを使い、profile未使用・既定morph setの場合もpreset / profile / morph set / Whisper identityを省略せず記録する。
- [x] 個別VMD保存、個別MMD WAV出力、個別レポート保存が引き続き利用できる。
- [x] 一括出力のsuccess / failure / cancelが個別保存履歴とruntime INIを変更しない。
- [x] `audio_stem`とfolder nameのUnicodeを保持し、Windows不正名、component長255 UTF-16 code unit超過、絶対path長240 UTF-16 code unit超過を暗黙renameせず`output_path_invalid`で拒否する。

### transaction・安全性

- [x] 3成果物すべての生成・検証成功前に、承認済みfinal directory名で成果物を公開しない。stagingは成功成果物として扱わない。
- [x] empty / non-empty directory、file、symlink、reparse pointを含む同名destinationを変更せず、別名が要求される。
- [x] commit時はno-clobber directory renameを用い、事前検査後のTOCTOU collisionでも既存destinationを変更しない。
- [x] dialog後のcollision、cancel、各生成失敗、validation失敗、commit失敗で既存出力が保護される。
- [x] 失敗時にpartial final directoryが残らない。
- [x] cleanup失敗がprimary statusとは別のcleanup statusとして保持され、cancelへ吸収されず成功扱いにならない。
- [x] commit前cancelはcommitを禁止し、commit開始中 / 成功後cancelはrename結果を上書きせず、成功済みfinalを削除しない。
- [x] delivery terminal resultが`committed`、`final_path`、`staging_path`、primary status / error、cleanup status、commit phaseを一貫して返す。
- [x] window close時はdelivery terminal / cleanupまで破棄を待ち、window破棄後にfinal commitが発生しない。
- [x] `awaiting_commit_guard`でUI threadがcurrent stateからsave-state fingerprintを再構築し、開始時と異なるpackage、無効job、cancel / close受理済みjobにはauthorizationを発行しない。workerはGUI stateを直接読まない。
- [x] `projection_generation`変化だけではcommitを拒否しない。
- [x] UI投影generationはjob id / worker kindとともにlate-result discardだけへ使用される。
- [x] diagnostics WARNING拒否時はdialog、Busy、workerを開始せず、standalone report保存は既存契約どおり維持される。
- [x] raw exception、traceback、credential、background通信が追加されない。

### 回帰・文書

- [x] §11.4で列挙したMS20〜MS24の既存診断、VMD、WAV、worker、GUI state回帰が通過した。B7 cross-boundaryは4群合計`322 passed`、process exit code `0`である。B6時点の指定cross-boundary `94 passed`は履歴baselineとして分離した。
- [x] README、`readme_mmdautolip.txt`、Pipeline / GUI State / Error Handling / VMD Outputの各正文仕様を実装済み挙動へ照合した。必要事項は既に反映済みで、変更不要と判定した。B7ではIndex、Roadmap、Block Breakdown、B6 plan、B7 plan、milestone、Version Controlを実績へ同期した。
- [x] 実MMD確認、Python 3.11 / 3.12、MS27 package / release readinessを未検証として明記する。

## 13. リスクと対策

以下は実装時に監視・検証する残存リスクであり、Sol High監査で指摘されたP1 / P2 / P3の未解消を意味しない。各リスクには対応する契約、テスト、実装開始前ゲートを設定済みである。

| ID | リスク | 判定 | 対策 |
| --- | --- | --- | --- |
| MS25-R1 | VMD、WAV、reportのいずれかをfinal directoryへ先に書き、承認済みfinal名でpartial outputを公開する | P1候補 | 同一親directoryのstagingへ全件生成・検証し、最後にdirectory単位でcommitする。stagingは成功成果物として扱わない |
| MS25-R2 | 個別保存済みVMDまたは解析WAVを流用し、現在状態やMMD音声roleと不一致になる | P1候補 | 開始contextから3件を再生成し、成果物ごとの生成元をcoreテストで固定する |
| MS25-R3 | 既存packageをmerge / replaceしてユーザー出力を破壊する | P1候補 | 既存final directoryをcommit対象にせず、collision時は別名要求とする |
| MS25-R4 | dialog後のTOCTOUで、別processの同名destinationを壊す | P1候補 | 事前再検査に加え、既存entryを置換しないno-clobber renameをcommit線形化点とし、失敗をcollisionへ正規化する |
| MS25-R5 | reportとVMDが別snapshotになり、記録された設定と成果物が不一致になる | P2候補 | immutable開始contextと開始fingerprintを束ね、`awaiting_commit_guard`でUI threadがcurrent fingerprintを再構築してjob-bound authorizationを返す。UI投影generationはcommit guardにしない |
| MS25-R6 | Whisperのmanagement diagnosticsをfingerprintへ混入し、MS21保存契約が変わる | P2候補 | 既存fingerprint schemaを維持し、Whisper情報はreport snapshotへ限定する |
| MS25-R7 | cancel、late callback、window closeがBusy / filesystem結果を壊し、commit済みpackageをcancel扱いにする | P1候補 | no-clobber renameを線形化点とするdelivery専用terminal resultを使い、closeはterminal / cleanupまで待つ。UI generationはlate-result専用とする |
| MS25-R8 | cleanup failureをcancelへ吸収し、temporary filesの所在や安全性が不明になる | P2候補 | primary statusとcleanup statusを分離し、`partial_output_cleanup_failed`を成功扱いしない。詳細はsafe diagnosticsへ分離する |
| MS25-R9 | empty directory、file、symlink、reparse pointの扱いが揺れ、既存entryを置換する | P1候補 | 種類や空否を問わず既存destinationをcollisionとして拒否し、削除・置換・mergeしない |
| MS25-R10 | 新しい親directory設定を追加し、runtime INIや設定migrationへ範囲が拡大する | P3候補 | MS25では新規設定keyを追加せず、既存path導出またはsession-only入力とする |
| MS25-R11 | READMEが個別出力だけを説明し、batchのcollision / 保護動作を誤認させる | P3（解消） | READMEと`readme_mmdautolip.txt`を実装・検証結果へ同期した |
| MS25-R12 | MS20 indexの古いcurrent-state表記がMS25の完了判定と混同される | P3（解消） | live Git、Roadmap、Closeout結果を優先し、MS25-B5実装後にindexを同期した |
| MS25-R13 | 入力音声が解析後に差し替わり、VMDとWAVのsourceが不一致になる | P1候補 | 開始contextへsource identityを固定し、WAV生成前後に再確認する。content hash非採用の検出限界を明記する |
| MS25-R14 | VMD writer成功だけで破損・truncated VMDをcommitする | P1候補 | production read-back validatorでheader、morph records、末尾section、EOFを検証する |
| MS25-R15 | profile未使用・既定morph setがreportから省略され、利用条件を再現できない | P2候補 | `diagnostic_report.py`を変更し、未使用 / 既定identityも明示記録する |
| MS25-R16 | 不正または長すぎるWindows名を暗黙変換し、承認済み命名と実出力がずれる | P2候補 | Unicodeを保持した専用validationを行い、予約名・control文字・長さ超過は暗黙renameせず拒否する |

## 14. 実装開始前の確認ゲート（計画作成時の記録）

本文書作成後、production codeへ着手する前に再確認した計画時のゲートである。B5実装後の現在状態は文書冒頭とMS25-B5 Implementation Planの実装結果を参照する。

- [ ] `src/core`へ追加するorchestration moduleと既存writerの境界が確定している。
- [ ] `DELIVERY_PACKAGE` kind、delivery専用terminal result、commit線形化点、cancel / cleanup / window closeの境界が既存worker契約と分離されている。
- [ ] start contextに入力音声identityと開始fingerprintを含め、`awaiting_commit_guard`でUI threadがcurrent fingerprintを再構築し、job-bound authorizationを返す。workerはGUI stateを直接読まず、`projection_generation`はUI / late-result専用である。
- [ ] final pathに種類・空否を問わず既存entryがあればcollisionとし、commitにno-clobber renameを使う契約が確定している。
- [ ] diagnostics WARNING確認をdestination dialog / Busy / workerより前に行い、standalone report保存と区別する契約が確定している。
- [ ] VMD production read-back validatorの配置、解析項目、失敗分類が確定している。
- [ ] profile未使用・既定morph setを含むreport必須identityと`diagnostic_report.py`変更範囲が確定している。
- [ ] `audio_stem` / folder name / component / path長のWindows validationと暗黙rename禁止が確定している。
- [ ] source identityはresolved path / size / `mtime_ns` / file identityまで保証し、content hashを要求しない検出限界が記録されている。
- [ ] 一括出力が個別保存履歴を変更せず、batch parent directoryをsession-onlyとすることが確定している。
- [ ] package専用のreport field、hash、manifestを追加しない方針を確認している。
- [ ] 新規依存関係が不要であることを確認している。
- [x] `README.md` / `readme_mmdautolip.txt` / Pipeline / GUI State / Error Handling / VMD Output仕様の同期は実装・検証後に実施した。

### 14.1 確定判断

- empty existing directoryを含むdirectory、file、symlink、reparse pointはすべて「既存destination」として扱い、別名を要求する。この判断は確定済みであり、削除・置換・mergeは行わない。commit時もno-clobber renameで競合を拒否する。
- path長はMS25の固定契約として、各componentをUTF-16 code unit 255以下、絶対staging / final / 成果物pathをNUL終端を含めずUTF-16 code unit 240以下とする。使用APIやOS設定によるlong-path有効性に依存せず、超過時は`output_path_invalid`で拒否する。
- reportは既存のdiagnostic report形式を使用し、package専用manifest、hash、追加ファイルは作らない。MS25の目的は3成果物の一括出力であり、診断reportの契約拡張や配布manifestの導入はMS27または別変更へ分離する。
- batch parent directoryは新規INI keyへ保存せず、dialog入力または既存の安全なpath導出に限定する。これによりruntime user dataと設定migrationの範囲を増やさない。
- 入力音声のcontent hashは計算せず、resolved path / size / `mtime_ns` / 取得可能なfile identityの前後比較をMS25の保証範囲とする。完全なbyte identity保証ではないことを明記する。

### 14.2 監査指摘の解消状況

| 指摘 | 解消した契約・確認箇所 |
| --- | --- |
| P1-1 projection generationの自己失効 | §8.1、§9、§10、§11.1で、commit guardをsave-state fingerprintへ限定し、`projection_generation`をUI / late-result専用へ分離 |
| P1-2 cancel・commit・cleanup・shutdownの競合 | §8.6、§9、§10、§11.2〜§11.3で、commit線形化点、delivery terminal result、window close、cleanup failureを定義 |
| P2-1 destination collision / TOCTOU | §8.2、§9、§10、§11.3で、entry種別・空否を問わないcollisionとno-clobber commitを定義 |
| P2-2 WARNING確認 | §6 B1 / B5、§9、§10、§11.2で、destination dialog・Busy・worker開始前のfingerprint確認を定義 |
| P2-3 report identity省略 | §6 B3 / B4、§8.5、§11.1、§12で、profile未使用・既定morph setを含む必須記録を定義 |
| P2-4 入力音声identity | §8.1、§8.4、§10、§11.1で、WAV生成前後のidentity再確認とcontent hash非採用の限界を定義 |
| P2-5 VMD read-back | §6 B3、§11.1、§12、§15.1〜§15.2でproduction validatorと検証項目を定義 |
| P2-6 Windows命名・path長 | §8.2〜§8.3、§11.1、§12、§14でUnicode保持、無効名拒否、component 255 / 絶対path 240 UTF-16 code unit上限を固定 |
| P2-7 正文書同期 | §6 B7、§12、§15.3でPipeline / GUI / Error / VMD仕様を同期対象へ追加 |
| P3-1〜P3-4 | §1、§9〜§11、§13で個別履歴非変更、staging可視性、具体的回帰対象、レビュー来歴を明記 |

## 15. MS25で変更候補となるファイル

### 15.1 production code候補

- `src/core/delivery_package.py`（新規）: 開始context、source identity、名前・destination検証、staging、3成果物生成、no-clobber commit線形化、delivery terminal result、cleanup
- `src/core/__init__.py`: core公開APIとしてexportする場合のみ変更
- `src/core/diagnostic_report.py`: profile未使用・既定morph setを含むpreset / profile / morph / Whisper identityの必須記録
- `src/vmd_writer/validator.py`（新規）: production VMD read-back validation
- `src/gui_wx/worker_state.py`: package専用worker kind、必要なdelivery terminal stateを追加する場合に変更
- `src/gui_wx/audio_worker.py`: 汎用workerを再利用する場合のdelivery専用cancel / terminal分岐。commit済みresultをcancelへ上書きしない
- `src/gui_wx/app_controller.py`: WARNING確認、batch起動、開始context、worker、terminal callback、window close、success / failure projection、個別保存履歴非変更
- `src/gui_wx/main_frame.py`: 一括出力導線、destination dialog、Busy表示、通知、close待機
- `src/gui_wx/ui_state.py`: batch Busy / result stateが既存stateだけで表せない場合に最小限変更

### 15.2 test候補

- `tests/test_ms25_b6_windows_collision_faults.py`（B6で新規）
- `tests/test_ms25_b6_delivery_failure_recovery.py`（B6で新規）
- `tests/test_ms25_b6_delivery_gui_recovery.py`（B6で新規）
- `tests/test_ms25_b3_vmd_readback_validation.py`（既存。B7で回帰）
- `tests/test_ms25_b4_delivery_report_identity.py`（既存。B7で回帰）
- §11.4で列挙した既存のVMD writer、MMD WAV、diagnostic report、worker、GUI state関連テスト（B7では回帰確認のみ。追加修正が必要な場合は別repairへ分離）

### 15.3 文書候補

- `README.md`
- `readme_mmdautolip.txt`
- `docs/Pipeline_Data_Contract_Specification.md`
- `docs/GUI_State_Theme_Specification.md`
- `docs/Error_Handling_Specification.md`
- `docs/VMD_Output_Specification.md`
- `docs/MS20_and_Beyond_Index.md`
- `docs/MS20_and_Beyond_Roadmap.md`
- `docs/repo_milestone.md`、`docs/Version_Control.md`（実装・closeoutの記録が必要な場合）

### 15.4 変更禁止対象

- `presets.json`
- `profiles.json`
- `MMD_AutoLipTool.ini`
- MS24 Whisper model selection実装の再設計
- PyInstaller spec、build script、license文書（MS25で依存・配布内容を変更しない限り変更しない）

## 16. 次工程への引き継ぎ

1. `MS25-B1`の開始context、source identity、WARNING gate、fingerprint commit guardを、現行`EffectiveShapePlan` / diagnostics snapshotの実装へ再照合した。
2. `MS25-B2`でno-clobber directory rename、commit線形化点、delivery terminal resultの実装を固定した。
3. `MS25-B3`でproduction VMD read-back validatorとsource audio identity前後確認を実装した。
4. core orchestrationを実装し、GUIを介さないtransaction / failure / cancel / cleanup testsを通した。
5. GUI / workerを接続し、WARNING、Busy、late-result、window close、個別保存導線と履歴非変更を回帰した。
6. B5実装・自動検証・ユーザー報告による手動GUI確認を完了し、README / 配布用readme / Pipeline / GUI / Error / VMD仕様、Index、Roadmapへ状態を同期した。B7のfull cross-boundary regression / closeoutは残課題である。
7. MS26では実MMDへ渡した3成果物の読み込み・再生・リップ同期を確認する。
8. MS27ではPyInstaller onefile、ZIP、最終artifact、package / release readinessを別工程として確認する。
