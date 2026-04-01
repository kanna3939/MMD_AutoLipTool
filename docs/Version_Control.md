# Version Control Log

## Entry 2026-04-02 / Session: release-v0380-ms12-packaging-sync

- Date: 2026-04-02
- Session: release-v0380-ms12-packaging-sync
- Summary:
  - リポジトリ全体の current version を `Ver 0.3.8.0` として同期した。
  - MS12-5 までの build / packaging / release-side documentation 整備を、`0.3.8.0` の repository-facing state として確定対象にした。
  - 手動配置された FFmpeg 実バイナリと未追跡文書をコミット対象へ含める前提で整理した。
- Modified Files:
  - `pyproject.toml`: プロジェクト version を `0.3.8.0` に更新。
  - `README.md`: current version 表記を `Ver. 0.3.8.0` に更新。
  - `docs/Specification_Prompt_v3.md`: 対応リリースを `Ver 0.3.8.0` に更新。
  - `docs/MS12_Implementation_Roadmap.md`: Baseline Version を `Ver 0.3.8.0` に更新。
  - `docs/MS11_MS12_Roadmap_and_Scope_Split.md`: Baseline / status note / recommended order の current version を `Ver 0.3.8.0` に更新。
  - `docs/MS11-10_Implementation_Plan.md`: current sync version を `Ver 0.3.8.0` に更新。
  - `docs/MS12-4_Implementation_Plan.md`: `pyproject.toml` 参照 version を `0.3.8.0` に更新。
  - `tests/test_app_version.py`: current project version に追従。
  - `tests/test_main_startup_splash.py`: splash version text expectation を `Ver. 0.3.8.0` に更新。
  - `tests/test_main_window_version_info.py`: Help version expectation を `0.3.8.0` に更新。
  - `docs/repo_milestone.md`: 本同期メモを追加。
  - `docs/Version_Control.md`: 本エントリを追加。
- Added Files:
  - なし
- Notes:
  - 過去ログに残る `0.3.7.1` 記述は履歴として保持し、current version 記述のみ `0.3.8.0` に更新した。
  - ローカル実行生成物の ini / pyc は current release state には含めない。
- Verification:
  - `rg -n "0\\.3\\.8\\.0|Ver 0\\.3\\.8\\.0|Ver\\. 0\\.3\\.8\\.0" README.md pyproject.toml tests docs`

## Entry 2026-04-02 / Session: ms12-5-implement-ffmpeg-bundling-cleanup

- Date: 2026-04-02
- Session: ms12-5-implement-ffmpeg-bundling-cleanup
- Summary:
  - `MS12-5: distribution dependency bundling cleanup` を onedir 前提で実装した。
  - 公式配布ビルド `FFmpeg v8.1` の `bin` 手動配置を build 契約として固定し、`build.ps1` / `MMD_AutoLipTool.spec` / release-side docs を同期した。
  - `LICENSE` / `NOTICE` / `THIRD_PARTY_LICENSES.md` を build 出力へ同梱する方針を `.spec` に反映した。
- Modified Files:
  - `.gitignore`: `FFmpeg\bin\` 手動配置ルールと `.gitkeep` の例外を追加。
  - `build.ps1`: `FFmpeg\bin\` / `ffmpeg.exe` / `ffprobe.exe` の事前チェックを追加。
  - `MMD_AutoLipTool.spec`: `LICENSE` / `NOTICE` / `THIRD_PARTY_LICENSES.md` の datas 追加、`FFmpeg\bin\` の bundling 追加、`.gitkeep` 除外を反映。
  - `README.md`: FFmpeg v8.1 手動配置を含む onedir build 手順へ更新。
  - `NOTICE`: 現在の FFmpeg bundling 前提を追記。
  - `THIRD_PARTY_LICENSES.md`: FFmpeg v8.1 の採用前提、配置先、配布先、確認観点を追記。
  - `docs/MS12_Implementation_Roadmap.md`: MS12-5 の採択済み FFmpeg 方針へ同期。
  - `docs/MS11_MS12_Roadmap_and_Scope_Split.md`: MS12-5 の説明を採用済み FFmpeg bundling 前提へ同期。
  - `docs/Specification_Prompt_v3.md`: build / 配布方針へ FFmpeg v8.1 手動配置と配布物同梱物を追記。
  - `docs/repo_milestone.md`: MS12-5 実装メモを追加。
  - `docs/Version_Control.md`: 本エントリを追加。
- Added Files:
  - `FFmpeg/bin/.gitkeep`
  - `docs/MS12-5_Implementation_Plan.md`
- Notes:
  - 現時点では実リポジトリに FFmpeg 実バイナリを置いていないため、build 実行そのものは未実施。
  - 今回の主目的は、FFmpeg v8.1 を使う onedir build 契約と release-side 文書整合の固定である。
- Verification:
  - `rg -n "FFmpeg|v8.1|LICENSE|NOTICE|THIRD_PARTY_LICENSES|gitkeep" .gitignore build.ps1 MMD_AutoLipTool.spec README.md NOTICE THIRD_PARTY_LICENSES.md docs/MS12_Implementation_Roadmap.md docs/MS11_MS12_Roadmap_and_Scope_Split.md docs/Specification_Prompt_v3.md`
  - `.\.venv\Scripts\python.exe -c "compile(open('MMD_AutoLipTool.spec', encoding='utf-8').read(), 'MMD_AutoLipTool.spec', 'exec'); print('spec ok')"`
  - `powershell -Command "[void][scriptblock]::Create((Get-Content build.ps1 -Raw)); 'build script ok'"`

## Entry 2026-04-02 / Session: ms12-5-plan-doc

- Date: 2026-04-02
- Session: ms12-5-plan-doc
- Summary:
  - `MS12-5: distribution dependency bundling cleanup` の個別実装 plan を追加した。
  - 現行 build / spec / notice / third-party docs を前提に、配布依存方針と文書同期方針を整理した。
  - FFmpeg bundling 採用可否が実装内容を大きく左右するため、ここをユーザー判断項目として分離した。
- Modified Files:
  - `docs/repo_milestone.md`: MS12-5 実装 plan 整理メモを追加。
  - `docs/Version_Control.md`: 本エントリを追加。
- Added Files:
  - `docs/MS12-5_Implementation_Plan.md`
- Notes:
  - 今回は実装 plan 文書化のみで、コード変更や build 定義変更は行っていない。
  - 後続判断として、FFmpeg bundling は採用する前提へ進める。
  - 配置方法は手動配置を採る。
  - 手動配置先は exe ルート下 `FFmpeg`、配布物単位は `bin` のみ、版数記録は関連ドキュメント全てへ反映する方針を採る。
  - 次段は、この前提で MS12-5 実装へ入る。
- Verification:
  - `rg -n "MS12-5|FFmpeg|bundling|build|NOTICE|THIRD_PARTY_LICENSES|保留課題" docs/MS12-5_Implementation_Plan.md docs/repo_milestone.md docs/Version_Control.md`

## Entry 2026-04-02 / Session: ms12-4-implement-splash-version

- Date: 2026-04-02
- Session: ms12-4-implement-splash-version
- Summary:
  - `MS12-4: splash version display` を実装した。
  - `app_version.py` を追加して app version source を共通化し、splash と Help の両方が同じ version 解決経路を使うようにした。
  - splash へ `Ver. x.y.z` 形式の文字重ねを追加し、最小回帰テストを整備した。
- Modified Files:
  - `src/main.py`: splash version 文字重ねと共通 version helper 利用を追加。
  - `src/gui/main_window.py`: Help version 表示を共通 helper 参照へ切り替え。
  - `tests/test_main_startup_splash.py`: splash version 表示テストを追加。
  - `docs/repo_milestone.md`: MS12-4 実装メモを追加。
  - `docs/Version_Control.md`: 本エントリを追加。
- Added Files:
  - `src/app_version.py`
  - `tests/test_app_version.py`
  - `tests/test_main_window_version_info.py`
- Notes:
  - splash 上の表記は `Ver. x.y.z`、位置はロゴ下の中央下寄り空白帯に寄せた。
  - dependency version は従来どおり Help ダイアログのみで表示している。
- Verification:
  - `.\\.venv\\Scripts\\python.exe -m pytest tests/test_app_version.py tests/test_main_startup_splash.py tests/test_main_window_version_info.py tests/test_main_window_processing_responsiveness.py`

## Entry 2026-04-02 / Session: ms12-4-plan-doc

- Date: 2026-04-02
- Session: ms12-4-plan-doc
- Summary:
  - `MS12-4: splash version display` の個別実装 plan を追加した。
  - `main.py` の splash 導線と `main_window.py` の Help version 表示を前提に、app version source を単一化して両者から共有する方針を整理した。
  - version 表記形式と splash 上の表示位置は保留課題として切り分けた。
- Modified Files:
  - `docs/repo_milestone.md`: MS12-4 実装 plan 整理メモを追加。
  - `docs/Version_Control.md`: 本エントリを追加。
- Added Files:
  - `docs/MS12-4_Implementation_Plan.md`
- Notes:
  - 今回は実装 plan 文書化のみで、コード変更やテスト追加は行っていない。
  - 次段は、この plan を基準に MS12-4 実装へ入る前提とする。
  - 後続判断として、表記は `Ver. x.y.z`、表示位置はロゴ下の中央下寄り空白帯を採る。
- Verification:
  - `rg -n "MS12-4|version source|splash|Help|保留課題|完了条件" docs/MS12-4_Implementation_Plan.md docs/repo_milestone.md docs/Version_Control.md`

## Entry 2026-04-02 / Session: ms12-3-implement-splash-timing

- Date: 2026-04-02
- Session: ms12-3-implement-splash-timing
- Summary:
  - `MS12-3: splash timing improvement` を実装した。
  - `main.py` に splash の生成・表示・finish helper を追加し、起動が速い環境でも短時間は splash が表示される最小表示時間付き finish 予約を導入した。
  - splash asset 無しの fallback と finish 予約を固定する最小テストを追加した。
- Modified Files:
  - `src/main.py`: splash helper、最小表示時間計算、finish 予約導線を追加。
  - `docs/repo_milestone.md`: MS12-3 実装メモを追加。
  - `docs/Version_Control.md`: 本エントリを追加。
- Added Files:
  - `tests/test_main_startup_splash.py`
- Notes:
  - 今回は splash timing のみを対象とし、version 表示や splash デザイン変更は含めていない。
  - 最小表示時間は短めの固定値で導入し、実機確認で調整する前提を維持している。
- Verification:
  - `.\\.venv\\Scripts\\python.exe -m pytest tests/test_main_startup_splash.py tests/test_main_window_processing_responsiveness.py tests/test_main_window_vmd_output_dir.py`

## Entry 2026-04-02 / Session: ms12-3-plan-doc

- Date: 2026-04-02
- Session: ms12-3-plan-doc
- Summary:
  - `MS12-3: splash timing improvement` の個別実装 plan を追加した。
  - `main.py` の現行起動順を前提に、splash 表示順、settings load と main window 構築待ちの吸収位置、finish タイミングを整理した。
  - 最小表示時間や finish 遅延のような見た目判断は保留課題として切り分けた。
- Modified Files:
  - `docs/repo_milestone.md`: MS12-3 実装 plan 整理メモを追加。
  - `docs/Version_Control.md`: 本エントリを追加。
- Added Files:
  - `docs/MS12-3_Implementation_Plan.md`
- Notes:
  - 今回は実装 plan 文書化のみで、コード変更やテスト追加は行っていない。
  - 次段は、この plan を基準に MS12-3 実装へ入る前提とする。
  - 後続判断として、起動が速い環境でも splash を一瞬だけでも表示させる方向を採る。
- Verification:
  - `rg -n "MS12-3|splash|finish|最小表示時間|保留課題|完了条件" docs/MS12-3_Implementation_Plan.md docs/repo_milestone.md docs/Version_Control.md`

## Entry 2026-04-02 / Session: ms12-2-implement-processing-worker

- Date: 2026-04-02
- Session: ms12-2-implement-processing-worker
- Summary:
  - `MS12-2: processing-time UI responsiveness improvement` を実装した。
  - `main_window.py` に最小の `QThread + QObject worker` 導線を追加し、`build_vowel_timing_plan(...)` の実行を UI スレッド外へ切り出した。
  - 成功時の timing plan 反映、waveform / preview 更新、失敗時の warning / 復帰を UI 側 handler に整理し、最小回帰テストを追加した。
- Modified Files:
  - `src/gui/main_window.py`: processing worker、成功 / 失敗 handler、UI 側 apply / reset 導線を追加。
  - `docs/repo_milestone.md`: MS12-2 実装メモを追加。
  - `docs/Version_Control.md`: 本エントリを追加。
- Added Files:
  - `docs/MS12-2_Implementation_Plan.md`
  - `tests/test_main_window_processing_responsiveness.py`
- Notes:
  - 今回は processing responsiveness の最小導線のみで、キャンセル機能や詳細 progress 表示は追加していない。
  - dialog modality と completion sound の契約は既存挙動を維持している。
- Verification:
  - `.\\.venv\\Scripts\\python.exe -m pytest tests/test_main_window_processing_responsiveness.py tests/test_main_window_vmd_output_dir.py tests/test_main_window_closing_softness.py`

## Entry 2026-04-02 / Session: ms12-2-plan-doc

- Date: 2026-04-02
- Session: ms12-2-plan-doc
- Summary:
  - `MS12-2: processing-time UI responsiveness improvement` の個別実装 plan を追加した。
  - 現行の `_run_processing()` / `_refresh_waveform_morph_labels()` / `_begin_processing_session()` 周辺の責務を踏まえ、worker 境界と UI 側に残す更新責務を整理した。
  - 未確定事項は今回も問い合わせず、worker 方式、payload 形、dialog modality などを保留課題として文書へ残した。
- Modified Files:
  - `docs/repo_milestone.md`: MS12-2 実装 plan 整理メモを追加。
  - `docs/Version_Control.md`: 本エントリを追加。
- Added Files:
  - `docs/MS12-2_Implementation_Plan.md`
- Notes:
  - 今回は実装 plan 文書化のみで、コード変更やテスト追加は行っていない。
  - 次段は、この plan を基準に MS12-2 実装へ入る前提とする。
- Verification:
  - `rg -n "MS12-2|worker|_run_processing|_refresh_waveform_morph_labels|保留課題|完了条件" docs/MS12-2_Implementation_Plan.md docs/repo_milestone.md docs/Version_Control.md`

## Entry 2026-04-02 / Session: ms12-1-implement-vmd-output-dir-memory

- Date: 2026-04-02
- Session: ms12-1-implement-vmd-output-dir-memory
- Summary:
  - `MS12-1: VMD保存先フォルダの記憶と永続化` を実装した。
  - settings に `last_vmd_output_dir` を追加し、VMD 保存ダイアログの初期フォルダと保存成功時の更新を接続した。
  - cancel / export failure では remembered dir を更新しない最小回帰テストを追加した。
- Modified Files:
  - `src/gui/main_window.py`: VMD 保存先 remembered dir の読込、初期フォルダ反映、成功時更新と保存を追加。
  - `src/gui/settings_store.py`: `last_vmd_output_dir` の default / normalize / save / load を追加。
  - `tests/test_settings_store.py`: 新 settings key の round-trip / invalid fallback を追加。
  - `docs/repo_milestone.md`: MS12-1 実装メモを追加。
  - `docs/Version_Control.md`: 本エントリを追加。
- Added Files:
  - `tests/test_main_window_vmd_output_dir.py`
- Notes:
  - 保存対象はフォルダのみで、保存ファイル名や VMD recent history はまだ扱っていない。
  - settings save failure 時の warning 契約は既存実装に従っている。
- Verification:
  - `.\\.venv\\Scripts\\python.exe -m pytest tests/test_settings_store.py tests/test_main_window_vmd_output_dir.py`

## Entry 2026-04-02 / Session: ms12-1-plan-doc

- Date: 2026-04-02
- Session: ms12-1-plan-doc
- Summary:
  - `MS12-1: VMD保存先フォルダの記憶と永続化` の個別実装 plan を追加した。
  - 親ロードマップより一段具体化し、対象 / 非対象 / 壊さない前提 / 想定実装ステップ / テスト方針 / 保留課題を整理した。
  - 未確定事項は今回も問い合わせず、実装時判断が必要な論点として文書へ残した。
- Modified Files:
  - `docs/repo_milestone.md`: MS12-1 実装 plan 整理メモを追加。
  - `docs/Version_Control.md`: 本エントリを追加。
- Added Files:
  - `docs/MS12-1_Implementation_Plan.md`
- Notes:
  - 今回は実装 plan 文書化のみで、コード変更やテスト追加は行っていない。
  - 次段は、この plan を基準に MS12-1 実装へ入る前提とする。
- Verification:
  - `rg -n "MS12-1|保存成功時のみ|保留課題|last_vmd_output_dir|save dialog" docs/MS12-1_Implementation_Plan.md docs/repo_milestone.md docs/Version_Control.md`

## Entry 2026-04-02 / Session: ms12-roadmap-doc

- Date: 2026-04-02
- Session: ms12-roadmap-doc
- Summary:
  - MS12 全体の進め方を固定するため、`docs/MS12_Implementation_Roadmap.md` を追加した。
  - `保存先記憶 -> responsiveness -> splash timing -> splash version -> packaging` の順で、主対象ファイル、非対象、完了条件、リスク、未確定事項を整理した。
  - ユーザー判断が必要になりうる項目は、今回は問い合わせず保留課題として文書へ残した。
- Modified Files:
  - `docs/repo_milestone.md`: MS12 実装ロードマップ整理メモを追加。
  - `docs/Version_Control.md`: 本エントリを追加。
- Added Files:
  - `docs/MS12_Implementation_Roadmap.md`
- Notes:
  - 今回はロードマップ文書化のみで、コード実装は行っていない。
  - 個別の実装 plan は、次段で MS12-1 から順に切り出す前提とする。
- Verification:
  - `rg -n "MS12-1|MS12-2|MS12-3|MS12-4|MS12-5|未確定事項|保留課題|最初の自然な最小単位" docs/MS12_Implementation_Roadmap.md docs/repo_milestone.md docs/Version_Control.md`

## Entry 2026-04-02 / Session: ms12-output-folder-requirement-sync

- Date: 2026-04-02
- Session: ms12-output-folder-requirement-sync
- Summary:
  - MS12 の先頭要件として、`VMD保存先フォルダの記憶と永続化` を追加した。
  - 既存の MS12-1 だった processing-time responsiveness は 1 段後ろへ移し、MS12 の推奨順を `保存先記憶 -> responsiveness -> splash timing -> splash version -> packaging` に更新した。
  - 仕様書側にも、VMD 保存ダイアログ初期フォルダの再利用と永続化を後続対象として追記した。
- Modified Files:
  - `docs/MS11_MS12_Roadmap_and_Scope_Split.md`: MS12-1 を新設し、後続番号と実行順を更新。
  - `docs/Specification_Prompt_v3.md`: 出力仕様とテスト方針へ VMD 保存先フォルダ記憶の後続要件を追記。
  - `docs/repo_milestone.md`: MS12 要件整理メモを追加。
  - `docs/Version_Control.md`: 本エントリを追加。
- Added Files:
  - なし
- Notes:
  - 今回は要件整理のみで、コード実装は行っていない。
  - 既存の save validation / overwrite confirm / output semantics は変更していない。
- Verification:
  - `rg -n "MS12-1|MS12-2|MS12-3|MS12-4|MS12-5|save destination folder|VMD保存先フォルダ" docs/MS11_MS12_Roadmap_and_Scope_Split.md docs/Specification_Prompt_v3.md docs/repo_milestone.md docs/Version_Control.md`

## Entry 2026-04-02 / Session: ms11-10-doc-sync-v0371

- Date: 2026-04-02
- Session: ms11-10-doc-sync-v0371
- Summary:
  - MS11-10 相当の総まとめ文書を、MS11-9FIX7 まで反映した `Ver 0.3.7.1` 基準へ更新した。
  - `docs/MS11-10_Implementation_Plan.md` を、MS11 final consistency sync から MS11 closeout / FIX7 反映済みの総まとめ文書へ更新した。
  - README / 仕様書 / roadmap / milestone / version log の版数と現在地記述を揃え、コミット直前に見返せる文書状態へ整えた。
- Modified Files:
  - `README.md`: 版数を `Ver 0.3.7.1` に更新し、MS11-10 総まとめの直近更新を追記。
  - `pyproject.toml`: プロジェクトバージョンを `0.3.7.1` に更新。
  - `docs/MS11-10_Implementation_Plan.md`: FIX7 まで反映した closeout 文書へ更新。
  - `docs/MS11_MS12_Roadmap_and_Scope_Split.md`: Baseline Version と MS11-10 status note を `Ver 0.3.7.1` 基準へ更新。
  - `docs/Specification_Prompt_v3.md`: 対応リリースを `Ver 0.3.7.1` に更新し、FIX7 までの実装同期注記を追記。
  - `docs/repo_milestone.md`: `Ver 0.3.7.1 / MS11-10 closeout sync メモ` を追加。
  - `docs/Version_Control.md`: 本エントリを追加。
- Added Files:
  - なし
- Notes:
  - 今回はコミット前準備として文書整備と版数同期のみを行い、追加コード実装は含まない。
  - MS11 系の主残テーマは same-vowel 微調整、observation 契約整理、closing smoothing の自然さ確認である。
- Verification:
  - `rg -n "0\\.3\\.7\\.1|Ver 0\\.3\\.7\\.1|MS11-10|MS11-9FIX7|Test11_9S2|Test11_9S3|Test11_9S4" README.md pyproject.toml docs/MS11-10_Implementation_Plan.md docs/MS11_MS12_Roadmap_and_Scope_Split.md docs/Specification_Prompt_v3.md docs/repo_milestone.md docs/Version_Control.md`

## Entry 2026-04-02 / Session: ms11-9fix7-tail-contract-sync

- Date: 2026-04-02
- Session: ms11-9fix7-tail-contract-sync
- Summary:
  - MS11-9FIX7 の closing smoothing 契約整理を、関連文書へ横断同期した。
  - FIX7 により `closing_hold_frames` / `closing_softness_frames` の smoothing を family ごとの局所契約から、
    末尾 tail の共通 post-process 契約へ寄せた現在地を文書へ反映した。
  - `Test11_9S1.vmd` / `Test11_9S2.vmd` / `Test11_9S3.vmd` / `Test11_9S4.vmd` 比較により、
    短縮ではなく末尾追加として出ている確認結果を MS11-9 系全体へ同期した。
- Modified Files:
  - `docs/MS11-9FIX7_Implementation_Plan.md`: FIX7 実装反映メモ、repo 内テスト結果、`S1-S4` 実出力確認を追記。
  - `docs/MS11-9_Remaining_Issues.md`: FIX7 を MS11-9 系反映項目へ追加し、closing smoothing を自然さ評価フェーズとして整理。
  - `docs/MS11-9_Summary_and_Handoff.md`: FIX7 を横断要約へ追加し、closing smoothing の現在地を明記。
  - `docs/MS11-9_Observation_Handoff_Contract_Memo.md`: closing smoothing を tail 契約整理テーマとして追記。
  - `docs/repo_milestone.md`: MS11-9FIX7 closing smoothing 契約整理メモを追加。
  - `docs/Version_Control.md`: 本エントリを追加。
- Added Files:
  - なし
- Notes:
  - 今回は文書同期のみで、追加コード実装は行っていない。
  - FIX7 後の主題は「短縮バグの再発有無」ではなく、closing smoothing の効き方の自然さ確認である。
- Verification:
  - `rg -n "MS11-9FIX7|Test11_9S2|Test11_9S3|Test11_9S4|closing smoothing|tail post-process" docs/MS11-9FIX7_Implementation_Plan.md docs/MS11-9_Remaining_Issues.md docs/MS11-9_Summary_and_Handoff.md docs/MS11-9_Observation_Handoff_Contract_Memo.md docs/repo_milestone.md docs/Version_Control.md`

## Entry 2026-04-02 / Session: ms11-10-doc-sync-v0370

- Date: 2026-04-02
- Session: ms11-10-doc-sync-v0370
- Summary:
  - MS11-10 相当として、MS11 系の最終整合ドキュメント同期を `Ver 0.3.7.0` 基準で実施した。
  - `docs/MS11-10_Implementation_Plan.md` を追加し、MS11 final consistency sync の対象・完了条件・スコープ外を明文化した。
  - MS11-9 系は `docs/MS11-9_Summary_and_Handoff.md` を横断入口に据え、same-vowel 継続・cross-vowel 保留・top-end クローズの現在地を版数同期文書へ反映した。
- Modified Files:
  - `README.md`: 版数を `Ver 0.3.7.0` に更新し、MS11-10 相当の直近更新を追記。
  - `pyproject.toml`: プロジェクトバージョンを `0.3.7.0` に更新。
  - `docs/MS11_MS12_Roadmap_and_Scope_Split.md`: Baseline Version を `Ver 0.3.7.0` に更新し、MS11-10 の status note を追加。
  - `docs/Specification_Prompt_v3.md`: 対応リリースを `Ver 0.3.7.0` に更新し、MS11-10 文書参照を追加。
  - `docs/repo_milestone.md`: `Ver 0.3.7.0 / MS11-10 文書同期メモ` を追加。
  - `docs/Version_Control.md`: 本エントリを追加。
- Added Files:
  - `docs/MS11-10_Implementation_Plan.md`
- Notes:
  - 今回はコミット前準備として文書整備と版数同期のみを行い、追加コード実装は含まない。
  - MS11 系の主残テーマは same-vowel 微調整と observation 契約整理であり、MS12 は別ラインのまま維持する。
- Verification:
  - `rg -n "0\\.3\\.7\\.0|Ver 0\\.3\\.7\\.0|MS11-10|MS11-9_Summary_and_Handoff" README.md pyproject.toml docs`

## Entry 2026-04-01 / Session: ms11-9-closeout-and-summary

- Date: 2026-04-01
- Session: ms11-9-closeout-and-summary
- Summary:
  - MS11-9G を MMD 側確認込みで一旦クローズ扱いとし、MS11-9 系全体の現在地を文書横断で同期した。
  - `docs/MS11-9_Summary_and_Handoff.md` を新規追加し、MS11-9 から MS11-9G までの変遷、レイヤ責務、実出力確認、残課題を 1 枚に集約した。
  - `Remaining_Issues` / 契約メモ / Roadmap / Specification を、same-vowel 継続・cross-vowel 保留・top-end クローズという現在地へ更新した。
- Modified Files:
  - `docs/MS11-9_Remaining_Issues.md`: MS11-9G を一旦クローズ扱いへ更新し、MS11-9 全体サマリ文書への参照を追加。
  - `docs/MS11-9_Observation_Handoff_Contract_Memo.md`: top-end shaping を保留テーマへ移行し、現在地を更新。
  - `docs/MS11_MS12_Roadmap_and_Scope_Split.md`: MS11 側の残テーマを E / F / G 後の現在地へ更新。
  - `docs/Specification_Prompt_v3.md`: MS11-9E / F / G の反映状態と未反映テーマを現状へ同期。
  - `docs/repo_milestone.md`: MS11-9 closeout and summary sync メモを追加。
  - `docs/Version_Control.md`: 本エントリを追加。
- Added Files:
  - `docs/MS11-9_Summary_and_Handoff.md`
- Notes:
  - 個別の計画書は保持しつつ、現時点の参照入口を 1 枚へ寄せた。
  - MS11-9 系の主な残テーマは same-vowel 微調整と observation 契約整理であり、cross-vowel と top-end shaping は現時点で主対象から外してよい。
- Verification:
  - `rg -n "MS11-9_Summary_and_Handoff|MS11-9G|Test11_9p|same-vowel|cross-vowel|top-end shaping" docs/MS11-9_Summary_and_Handoff.md docs/MS11-9_Remaining_Issues.md docs/MS11-9_Observation_Handoff_Contract_Memo.md docs/MS11_MS12_Roadmap_and_Scope_Split.md docs/Specification_Prompt_v3.md docs/repo_milestone.md docs/Version_Control.md`

## Entry 2026-04-01 / Session: ms11-9g-top-end-sync

- Date: 2026-04-01
- Session: ms11-9g-top-end-sync
- Summary:
  - MS11-9G の top-end shaping residual 対応を、実装・実出力確認・文書同期まで進めた。
  - `src/vmd_writer/writer.py` の `peak_end_value` 解決を局所安定化し、`tests/test_vmd_writer_intervals.py` と `tests/test_preview_transform.py` に residual top-end 回帰を追加した。
  - [Test11_9p.vmd](d:/Visual%20Works/Kanna%20Work/Voice/Test11_9p.vmd) がローカル再生成 [dist/_tmp_ms11_9g_sample_input2_upper1.vmd](d:/Kanna_Works/MMD_AppWork/MMD_AutoLipTool/MMD_AutoLipTool_Codex/dist/_tmp_ms11_9g_sample_input2_upper1.vmd) と一致したことを記録した。
- Modified Files:
  - `src/vmd_writer/writer.py`: `peak_end_value` の 1 点依存を和らげる局所安定化を追加。
  - `tests/test_vmd_writer_intervals.py`: flat-top / 急減衰 residual の writer 回帰を追加。
  - `tests/test_preview_transform.py`: 同等の Preview 回帰を追加。
  - `docs/MS11-9G_Implementation_Plan.md`: 実装・確認結果を追記。
  - `docs/MS11-9_Remaining_Issues.md`: top-end shaping の現在地を MS11-9G / `Test11_9p.vmd` 反映状態へ更新。
  - `docs/MS11-9_Observation_Handoff_Contract_Memo.md`: top-end shaping の契約整理と次段候補を追記。
  - `docs/repo_milestone.md`: MS11-9G top-end shaping residual 整理メモを追加。
  - `docs/Version_Control.md`: 本エントリを追加。
- Added Files:
  - なし
- Notes:
  - 今回の変更は candidate family を増やさず、writer-side の top-end 値配分だけで差分を出す方針を維持している。
  - 次段は、新しい classification 追加よりも MMD 上の見え方評価と必要時の微調整を主題にするのが自然である。
- Verification:
  - `.\.venv\Scripts\python.exe -m pytest tests\test_vmd_writer_intervals.py tests\test_preview_transform.py -q`
  - `$env:PYTHONPATH='src;tests'; .\.venv\Scripts\python.exe -m pytest tests\test_pipeline_peak_values.py tests\test_pipeline_and_vmd.py -q`

## Entry 2026-04-01 / Session: ms11-9f-doc-closeout

- Date: 2026-04-01
- Session: ms11-9f-doc-closeout
- Summary:
  - MS11-9F / F-2 / F-3 の cross-vowel residual refinement 到達状態を、残課題文書・契約メモ・マイルストーンへ同期した。
  - `sample_input2` の residual cross-vowel を `23 -> 10 -> 7 -> 3` まで圧縮した現在地と、`Test11_9n.vmd` / `Test11_9m.vmd` / `Test11_9o.vmd` が各段階のローカル再生成結果と一致したことを記録した。
  - MS11-9F-4 は、残件 3 件を無理に救済し切るのではなく、`idx 172 / 193` を非対象候補、`idx 6` を mixed-gap 境界 case として文書上で確定扱いにした。
- Modified Files:
  - `docs/MS11-9F-4_Implementation_Plan.md`: 文書上の確定事項を追記。
  - `docs/MS11-9_Remaining_Issues.md`: cross-vowel 現在地を F / F-2 / F-3 反映状態へ更新済み。
  - `docs/MS11-9_Observation_Handoff_Contract_Memo.md`: cross-vowel 契約整理メモを F / F-2 / F-3 到達状態へ更新済み。
  - `docs/repo_milestone.md`: MS11-9F cross-vowel residual 整理メモを追加。
  - `docs/Version_Control.md`: 本エントリを追加。
- Added Files:
  - なし
- Notes:
  - コード変更の実装本体は既存差分を正本とし、このエントリでは文書同期と F-4 の確定判断を記録する。
  - 現時点の cross-vowel 残件 3 件は、追加救済ルール導入前に「救済対象かどうか」を見直す段階とする。
- Verification:
  - `rg -n "MS11-9F|MS11-9F-2|MS11-9F-3|MS11-9F-4|23 -> 10 -> 7 -> 3|Test11_9o" docs/MS11-9F-4_Implementation_Plan.md docs/MS11-9_Remaining_Issues.md docs/MS11-9_Observation_Handoff_Contract_Memo.md docs/repo_milestone.md docs/Version_Control.md`

## Entry 2026-04-01 / Session: release-v0365-ms11-9-sync

- Date: 2026-04-01
- Session: release-v0365-ms11-9-sync
- Summary:
  - MS11-9 系の拡張実装と残課題整理を、`Ver 0.3.6.5` として関連ドキュメントへ同期した。
  - MS11-9D から MS11-9D-6 までの speech-internal lip-motion 改善を、現行 workspace の反映済み到達として整理した。
  - MS11-9 系の残課題は `docs/MS11-9_Remaining_Issues.md` を正本として切り出した。
- Modified Files:
  - `README.md`: 版数表記を `Ver 0.3.6.5` に更新し、MS11-9D〜MS11-9D-6 と残課題整理の直近更新を追記。
  - `pyproject.toml`: プロジェクトバージョンを `0.3.6.5` に更新。
  - `docs/Specification_Prompt_v3.md`: 対応リリースを `Ver 0.3.6.5` に更新し、MS11-9D〜MS11-9D-6 の反映状態と残課題参照先を同期。
  - `docs/MS11_MS12_Roadmap_and_Scope_Split.md`: Baseline Version と roadmap 見出しを `Ver 0.3.6.5` 基準へ更新。
  - `docs/MS11-9_Remaining_Issues.md`: MS11-9 系残課題の正本として追加済み文書を版同期対象へ含めた。
  - `docs/repo_milestone.md`: `Ver 0.3.6.5` 同期メモを追記。
  - `docs/Version_Control.md`: 本エントリを追加。
- Added Files:
  - なし
- Notes:
  - 今回は文書同期のみで、追加のコード変更やテスト変更は行っていない。
  - 実装の細部は既存コード差分と各 `docs/MS11-9D*_Implementation_Plan.md` を正本とする。
- Verification:
  - `rg -n "Ver 0.3.6.5|0.3.6.5|MS11-9D-6|MS11-9_Remaining_Issues" README.md pyproject.toml docs/Specification_Prompt_v3.md docs/MS11_MS12_Roadmap_and_Scope_Split.md docs/MS11-9_Remaining_Issues.md docs/repo_milestone.md docs/Version_Control.md`

## Entry 2026-04-01 / Session: ms11-9-doc-wrapup-and-sync

- Date: 2026-04-01
- Session: ms11-9-doc-wrapup-and-sync
- Summary:
  - MS11-9 系を一度区切るため、残課題の正本ドキュメントを新規追加した。
  - MS11-9D 以降の refinement chain（9D / 9D-2 / 9D-3 / 9D-4 / 9D-5 / 9D-6）の実装到達状態を roadmap / milestone / version log に同期した。
  - same-vowel / cross-vowel の speech-internal bridge、zero-run span、top-end shaping、continuity floor、same-vowel burst smoothing を反映済み前提として整理し、残課題を別文書へ切り出した。
- Modified Files:
  - `docs/MS11-9_Remaining_Issues.md`: MS11-9 系の残課題正本を新規追加。
  - `docs/MS11_MS12_Roadmap_and_Scope_Split.md`: MS11-9D-2〜MS11-9D-6 の status note と残課題参照先を同期。
  - `docs/repo_milestone.md`: MS11-9 残課題整理・文書同期メモを追加。
  - `docs/Version_Control.md`: 本エントリを追加。
- Added Files:
  - `docs/MS11-9_Remaining_Issues.md`
- Notes:
  - 今回は文書整理のみで、追加のコード変更やテスト変更は行っていない。
  - 実装計画の正本は既存の `docs/MS11-9D*_Implementation_Plan.md` 群を参照する。
  - 実装後に残った見た目課題・暫定閾値・observation 契約の混雑は `docs/MS11-9_Remaining_Issues.md` を正本とする。
- Verification:
  - `rg -n "MS11-9D-3|MS11-9D-4|MS11-9D-5|MS11-9D-6|Remaining_Issues" docs/MS11_MS12_Roadmap_and_Scope_Split.md docs/repo_milestone.md docs/Version_Control.md docs/MS11-9_Remaining_Issues.md`

## Entry 2026-04-01 / Session: ms11-9d-2-doc-prep

- Date: 2026-04-01
- Session: ms11-9d-2-doc-prep
- Summary:
  - MS11-9D-2 Cross-vowel transition bridging の実装計画を文書化した。
  - cross-vowel を same-vowel の単純拡張として扱わず、`timeline` 非改変 / `observations` 正本 / `1 frame max` / `no_peak_in_window` と `below_rel_threshold` 限定の transition bridging として整理した。
  - Preview / export 整合、GUI 非追加、same-vowel と final closing からの責務分離、最低限のテスト観点を明文化した。
- Modified Files:
  - `docs/MS11-9D-2_Implementation_Plan.md`: MS11-9D-2 の実装計画書を新規追加。
  - `docs/MS11_MS12_Roadmap_and_Scope_Split.md`: MS11-9D-2 の位置づけと planned status note を追加。
  - `docs/repo_milestone.md`: MS11-9D-2 実装前整理メモを追加。
  - `docs/Version_Control.md`: 本エントリを追加。
- Added Files:
  - `docs/MS11-9D-2_Implementation_Plan.md`
- Notes:
  - この段階では実装は行っていない。
  - cross-vowel transition の具体 overlap 配置と observation 契約の細部は、実装時の最終固定事項として残している。
- Verification:
  - `rg -n "MS11-9D-2|cross-vowel transition bridging|observations|below_rel_threshold|1 frame" docs/MS11-9D-2_Implementation_Plan.md docs/MS11_MS12_Roadmap_and_Scope_Split.md docs/repo_milestone.md docs/Version_Control.md`

## Entry 2026-04-01 / Session: ms11-9d-doc-sync

- Date: 2026-04-01
- Session: ms11-9d-doc-sync
- Summary:
  - MS11-9D 初回実装の到達状態を、roadmap / milestone / version log へ同期した。
  - same-vowel micro-gap bridging の初回スコープを、`observations` 正本 / `timeline` 非改変 / `1 frame max` / `no_peak_in_window` と `below_rel_threshold` 限定として文書へ固定した。
  - cross-vowel、広い gap、GUI 追加、RMS 再調整、無音全体再設計は引き続きスコープ外として整理した。
- Modified Files:
  - `docs/MS11_MS12_Roadmap_and_Scope_Split.md`: MS11-9D を追加し、初回実装済み status note とスコープ境界を追記。
  - `docs/repo_milestone.md`: MS11-9D 初回実装反映メモを追加。
  - `docs/Version_Control.md`: 本エントリを追加。
- Added Files:
  - なし
- Notes:
  - 今回はドキュメント同期のみで、追加のコード変更やテスト変更は行っていない。
  - 実装の正本は既存のコード差分と `docs/MS11-9D_Implementation_Plan.md` を参照する。
- Verification:
  - `rg -n "MS11-9D|micro-gap bridging|observations|below_rel_threshold|same-vowel only" docs/MS11_MS12_Roadmap_and_Scope_Split.md docs/repo_milestone.md docs/Version_Control.md docs/MS11-9D_Implementation_Plan.md`

## Entry 2026-04-01 / Session: ms11-9c-doc-sync

- Date: 2026-04-01
- Session: ms11-9c-doc-sync
- Summary:
  - MS11-9C の実装到達状態を、主要ドキュメントへ同期した。
  - `開口保持` / `Lip Hold` の GUI 導線、`hold -> 70% midpoint -> zero` の final closing semantics、`peak == 0.0` 相当イベントを clamp blocker から除外する方針を文書へ反映した。
  - `sample_input2` 実データ観測で確認された zero-peak blocker 問題と、その修正済み clamp ルールを MS11-9C の現在地として整理した。
- Modified Files:
  - `docs/MS11-9C_Implementation_Plan.md`: clamp 判定固定方針と zero-peak blocker 除外を追記し、実装済み前提へ更新。
  - `docs/MS11_MS12_Roadmap_and_Scope_Split.md`: MS11-9C status note を追加し、GUI / writer / Preview / clamp の実装到達状態を同期。
  - `docs/Specification_Prompt_v3.md`: 実装同期注記を MS11-9C 反映状態へ更新し、未反映項目から MS11-9B / MS11-9C を削除。
  - `docs/repo_milestone.md`: MS11-9C 実装反映メモを追加。
  - `docs/Version_Control.md`: 本エントリを追加。
- Added Files:
  - なし
- Notes:
  - 今回はドキュメント同期のみで、追加のコード変更は行っていない。
  - 無音判定ロジック全体の再設計や RMS 再調整は引き続き対象外として維持した。
- Verification:
  - `rg -n "MS11-9C|開口保持|Lip Hold|zero-peak|clamp blocker|70% midpoint" docs/MS11-9C_Implementation_Plan.md docs/MS11_MS12_Roadmap_and_Scope_Split.md docs/Specification_Prompt_v3.md docs/repo_milestone.md docs/Version_Control.md`

---

## Entry 2026-04-01 / Session: ms11-9c-doc-prep

- Date: 2026-04-01
- Session: ms11-9c-doc-prep
- Summary:
  - MS11-9C Lip Hold GUI exposure and final-closing hold semantics alignment の実装計画を文書化した。
  - `closing_softness_frames` の意味を維持したまま、新規 `closing_hold_frames` を追加する前提、対象 family、適用順、GUI / Preview / export 整合方針を明文化した。
  - GUI 名称を `開口保持` / `Lip Hold` に固定し、UI 並び順を `モーフ最大値` → `開口保持` → `閉口スムース` に更新した。
- Modified Files:
  - `docs/MS11-9C_Implementation_Plan.md`: MS11-9C の実装計画書を新規追加。
  - `docs/MS11_MS12_Roadmap_and_Scope_Split.md`: MS11-9C の位置づけと完了像を追加。
  - `docs/Specification_Prompt_v3.md`: 未反映項目へ MS11-9C を追加。
  - `docs/repo_milestone.md`: MS11-9C 実装前整理メモを追加。
  - `docs/Version_Control.md`: 本エントリを追加。
- Added Files:
  - `docs/MS11-9C_Implementation_Plan.md`
- Notes:
  - この段階では実装は行っていない。
  - `closing_softness_frames` の既存意味は変更せず、別 parameter 導入方針のみを記録した。
- Verification:
  - `rg -n "MS11-9C|closing_hold_frames|Lip Hold|開口保持|hold -> softness -> clamp" docs/MS11-9C_Implementation_Plan.md docs/MS11_MS12_Roadmap_and_Scope_Split.md docs/Specification_Prompt_v3.md docs/repo_milestone.md docs/Version_Control.md`

---

## Entry 2026-04-01 / Session: ms11-9b-doc-prep

- Date: 2026-04-01
- Session: ms11-9b-doc-prep
- Summary:
  - MS11-9B Closing Softness GUI exposure and preview/output handoff alignment の実装前提を文書へ固定した。
  - GUI 配置、単位表示、値仕様、単一の現在値参照経路、再解析なし Preview 更新、処理中ロック方針、最低限のテスト観点を明文化した。
- Modified Files:
  - `docs/MS11-9B_Implementation_Plan.md`: MS11-9B の実装計画書を新規追加。
  - `docs/MS11_MS12_Roadmap_and_Scope_Split.md`: MS11-9B の位置づけと完了像を追加。
  - `docs/Specification_Prompt_v3.md`: 未反映項目を MS11-9B 名義へ整理。
  - `docs/repo_milestone.md`: MS11-9B 実装前整理メモを追加。
  - `docs/Version_Control.md`: 本エントリを追加。
- Added Files:
  - `docs/MS11-9B_Implementation_Plan.md`
- Notes:
  - この段階では実装内容そのものはまだ反映していない。
  - MS11-8 / MS11-9 の既存 semantics は変更しない前提で整理した。
- Verification:
  - `rg -n "MS11-9B|閉口スムース|Closing Smooth|closing softness 入力導線|単位表示|single current-value path" docs/MS11-9B_Implementation_Plan.md docs/MS11_MS12_Roadmap_and_Scope_Split.md docs/Specification_Prompt_v3.md docs/repo_milestone.md docs/Version_Control.md`

---

## Entry 2026-04-01 / Session: ms11-9-preview-shape-alignment-doc-sync

- Date: 2026-04-01
- Session: ms11-9-preview-shape-alignment-doc-sync
- Summary:
  - MS11-9 Preview trapezoid / multi-point display alignment の実装到達状態を、主要ドキュメントへ同期した。
  - `preview_transform.py` の shape-aware 契約拡張、`preview_area.py` の polygon/path ベース描画、shared viewport / playback / plot-area alignment 維持、関連テスト更新の反映状態を文書へ明記した。
- Modified Files:
  - `docs/Specification_Prompt_v3.md`: 実装同期注記を MS11-9 反映状態へ更新し、未反映項目から Preview multi-point 表示対応を削除。
  - `docs/repo_milestone.md`: MS11-9 実装反映メモを追加し、対象・確認状態・スコープ外を整理。
  - `docs/MS11_MS12_Roadmap_and_Scope_Split.md`: MS11-9 status note を追加し、current workspace での実装到達状態を追記。
  - `docs/MS11-9_Implementation_Plan.md`: 実装反映注記を追加し、計画書の先頭で current workspace の到達状態を明記。
  - `docs/Version_Control.md`: 本エントリを追加。
- Added Files:
  - なし
- Notes:
  - 版数更新や release sync は行っていない。
  - GUI からの closing softness 入力導線、RMS 再調整、MS11-10 / MS12 は引き続き対象外として維持した。
- Verification:
  - `rg -n "MS11-9|PreviewControlPoint|polygon / path|multi-point|closing softness|Status Note" docs/Specification_Prompt_v3.md docs/repo_milestone.md docs/MS11_MS12_Roadmap_and_Scope_Split.md docs/MS11-9_Implementation_Plan.md docs/Version_Control.md`
  - `git status --short docs/Specification_Prompt_v3.md docs/repo_milestone.md docs/MS11_MS12_Roadmap_and_Scope_Split.md docs/MS11-9_Implementation_Plan.md docs/Version_Control.md`

---

## Entry 2026-04-01 / Session: ms11-8-writer-closing-softness

- Date: 2026-04-01
- Session: ms11-8-writer-closing-softness
- Summary:
  - `writer.py` を主対象として、MS11-8 の mouth-closing softness control を実装した。
  - `closing_softness_frames: int = 0` を additive frame-count concept として導入し、MS11-2 / legacy fallback / MS11-3 final closing へ限定適用した。
  - 後続 shape 開始直前での clamp、延長後 metadata の整合、および最小 pipeline handoff と回帰テスト更新を反映した。
- Modified Files:
  - `src/vmd_writer/writer.py`: `closing_softness_frames` の受け取り、shape family 別の final closing 延長、clamp、metadata 整合を追加。
  - `src/core/pipeline.py`: `generate_vmd_from_text_wav()` から writer への最小 `closing_softness_frames` handoff を追加。
  - `tests/test_vmd_writer_peak_value.py`: zero-only shape 抑止が softness ありでも維持される確認を追加。
  - `tests/test_vmd_writer_intervals.py`: `softness=0` 完全互換、MS11-2 / legacy closing 延長、clamp 確認を追加。
  - `tests/test_vmd_writer_multipoint_shape.py`: MS11-3 final closing 延長と clamp 確認を追加。
  - `tests/test_vmd_writer_zero_guard.py`: 延長後 metadata の整合確認を追加。
  - `tests/test_pipeline_and_vmd.py`: pipeline → writer の `closing_softness_frames` handoff 確認を追加。
- Added Files:
  - なし
- Notes:
  - GUI / Preview / RMS / observation redesign には広げていない。
  - `softness=0` は既存出力互換を維持し、`closing_softness_frames < 0` は不許可とした。
- Verification:
  - `$env:PYTHONPATH='src;tests'; .\.venv\Scripts\python.exe -m unittest tests.test_vmd_writer_peak_value`
  - `$env:PYTHONPATH='src;tests'; .\.venv\Scripts\python.exe -m unittest tests.test_vmd_writer_intervals`
  - `$env:PYTHONPATH='src;tests'; .\.venv\Scripts\python.exe -m unittest tests.test_vmd_writer_multipoint_shape`
  - `$env:PYTHONPATH='src;tests'; .\.venv\Scripts\python.exe -m unittest tests.test_vmd_writer_zero_guard`
  - `$env:PYTHONPATH='src;tests'; .\.venv\Scripts\python.exe -m unittest tests.test_vmd_writer_grouping`
  - `$env:PYTHONPATH='src;tests'; .\.venv\Scripts\python.exe -m unittest tests.test_pipeline_and_vmd`
  - `$env:PYTHONPATH='src;tests'; .\.venv\Scripts\python.exe -m unittest tests.test_vmd_writer_peak_value tests.test_vmd_writer_intervals tests.test_vmd_writer_multipoint_shape tests.test_vmd_writer_zero_guard tests.test_vmd_writer_grouping tests.test_pipeline_and_vmd`

---

## Entry 2026-04-01 / Session: release-v0364-ms11-7-doc-sync

- Date: 2026-04-01
- Session: release-v0364-ms11-7-doc-sync
- Summary:
  - MS11-7 の文書整備と最小テスト追加を、`Ver 0.3.6.4` として関連ドキュメントへ同期した。
  - リポジトリ全体の反映版を `Ver 0.3.6.4` として確定し、MS11-7 の到達状態を「review 実施前の準備完了」段階として明記した。
- Modified Files:
  - `README.md`: 版数表記を `Ver 0.3.6.4` に更新し、MS11-7 文書整備の直近更新を追記。
  - `pyproject.toml`: プロジェクトバージョンを `0.3.6.4` に更新。
  - `docs/Specification_Prompt_v3.md`: 対応リリースを `Ver 0.3.6.4` に更新し、MS11-7 文書整備・最小テスト反映状態を同期。
  - `docs/MS11_MS12_Roadmap_and_Scope_Split.md`: Baseline Version と MS11-7 status note を `Ver 0.3.6.4` 基準へ更新。
  - `docs/MS11-7_Implementation_Plan.md`: 前提到達版と実装反映注記を更新。
  - `docs/repo_milestone.md`: `Ver 0.3.6.4` 同期メモを追記。
  - `docs/Version_Control.md`: 本エントリを追加。
- Added Files:
  - なし
- Notes:
  - 実装詳細自体は `ms11-7-docs-and-review-template` エントリを正本とする。
  - 実データ review の実施結果と RMS 定数再調整の最終判断は、この release sync には含めていない。
- Verification:
  - `rg -n "Ver 0.3.6.4|0.3.6.4|MS11-7" README.md pyproject.toml docs/Specification_Prompt_v3.md docs/MS11_MS12_Roadmap_and_Scope_Split.md docs/MS11-7_Implementation_Plan.md docs/repo_milestone.md docs/Version_Control.md`
  - `git status --short`

---

## Entry 2026-04-01 / Session: ms11-7-docs-and-review-template

- Date: 2026-04-01
- Session: ms11-7-docs-and-review-template
- Summary:
  - MS11-7 のスコープを「実データ observation 整理 + RMS 定数再調整要否判断」へ限定したまま、文書正本と review テンプレートを整備した。
  - `peak_value = 0.0` review の主記録を Markdown に置く方針を固定し、人工データで固定する意味がある最小 observation 境界テストのみ追加した。
- Modified Files:
  - `docs/MS11-7_Implementation_Plan.md`: MS11-7 の成果物、テスト方針、関連文書の最小同期方針を補強。
  - `tests/test_pipeline_peak_values.py`: `global_peak_zero` observation で `global_peak` / `reason` / `fallback_reason` / `window_sample_count` が整合することを確認する最小テストを追加。
  - `docs/repo_milestone.md`: MS11-7 文書整備開始メモを追記。
  - `docs/Version_Control.md`: 本エントリを追加。
- Added Files:
  - `docs/MS11-7_Real_Data_Observation_Review.md`: 実データ observation review の正本テンプレートを追加。
- Notes:
  - `pipeline.py` の helper 追加、RMS 定数変更、writer / GUI 改修は行っていない。
  - 指定されていた `docs/MS11_MS12_Roadmap_and_Scope_Split.md` は現ワークツリーでは削除扱いだったため、参照時は `docs/_old/` 側の内容も補助的に確認した。
- Verification:
  - `.\.venv\Scripts\python.exe -m unittest tests.test_pipeline_peak_values`

---

## Entry 2026-03-31 / Session: release-v0363-ms11-6-sync

- Date: 2026-03-31
- Session: release-v0363-ms11-6-sync
- Summary:
  - MS11-6 の main-flow-connected observation 接続、および provided timing plan 経路の observation 方針整理を含む現作業ツリーを `Ver 0.3.6.3` として同期した。
  - `README.md` / `pyproject.toml` / `docs/Specification_Prompt_v3.md` / `docs/repo_milestone.md` / 関連 MS11 文書の版数・到達記述を更新した。
  - リポジトリ全体の反映版を `Ver 0.3.6.3` として確定した。
- Modified Files:
  - `README.md`: 版数表記を `Ver 0.3.6.3` に更新し、MS11-6 の到達状態を追記。
  - `pyproject.toml`: プロジェクトバージョンを `0.3.6.3` に更新。
  - `docs/Specification_Prompt_v3.md`: 対応リリースを `Ver 0.3.6.3` に更新し、MS11-6 反映状態を同期。
  - `docs/repo_milestone.md`: `Ver 0.3.6.3` 同期メモと MS11-6 実装反映メモを追記。
  - `docs/MS11_Remaining_Issues_and_Next_Milestones.md`: MS11-6 反映後の残課題と次段階を整理。
  - `docs/MS11-6_Implementation_Plan.md`: 実装反映注記を追記。
  - `docs/MS11_MS12_Roadmap_and_Scope_Split.md`: Baseline Version と MS11-6 完了状態を同期。
  - `docs/Version_Control.md`: 本エントリを追加。
- Added Files:
  - なし
- Notes:
  - 実装詳細自体は `ms11-6-main-flow-observation-connection-cleanup` エントリを正本とする。
  - MS11-7 の実データ observation review と RMS 定数再調整判断は今回の release sync には含めていない。
- Verification:
  - `rg -n "Ver 0.3.6.3|0.3.6.3|MS11-6|MS11-7" README.md pyproject.toml docs/Specification_Prompt_v3.md docs/repo_milestone.md docs/MS11_Remaining_Issues_and_Next_Milestones.md docs/MS11-6_Implementation_Plan.md docs/MS11_MS12_Roadmap_and_Scope_Split.md docs/Version_Control.md`
  - `git status --short`

---

## Entry 2026-03-31 / Session: ms11-6-main-flow-observation-connection-cleanup

- Date: 2026-03-31
- Session: ms11-6-main-flow-observation-connection-cleanup
- Summary:
  - `pipeline.py` を主対象として、MS11-6 の main-flow-connected observation 接続と initial/refined timeline 追跡整理を実装した。
  - `VowelTimingPlan` を optional/internal observation の最初の正本保持先とし、`timeline` を canonical writer input のまま維持した。
  - provided timing plan 経路の observation 仕様を整理し、再利用経路と duration 補完経路の挙動をテストで明文化した。
- Modified Files:
  - `src/core/pipeline.py`: `VowelTimingPlan` / `PipelineResult` へ optional observation を追加し、main flow observation 接続と provided timing plan observation 方針を反映。
  - `tests/test_pipeline_and_vmd.py`: main-flow-connected observation 取得確認と、provided timing plan 2 経路の observation 挙動確認を追加。
  - `docs/Version_Control.md`: 本エントリを追加。
- Added Files:
  - なし
- Notes:
  - `PeakValueEvaluation` は維持し、`PeakValueObservation` は higher-level observation として扱う方針を維持した。
  - `writer.py` 再設計、GUI / Preview 改修、RMS 定数再調整には広げていない。
- Verification:
  - `.\.venv\Scripts\python.exe -m unittest tests.test_pipeline_peak_values`
  - `$env:PYTHONPATH='src;tests'; .\.venv\Scripts\python.exe -m unittest tests.test_pipeline_and_vmd`
  - `.\.venv\Scripts\python.exe -m unittest tests.test_vmd_writer_peak_value`

---

## Entry 2026-03-30 / Session: release-v0362-ms11-5-sync

- Date: 2026-03-30
- Session: release-v0362-ms11-5-sync
- Summary:
  - MS11-5 第一段階の observation helper / observation record / pipeline 系テスト拡張を含む現作業ツリーを `Ver 0.3.6.2` として同期した。
  - `README.md` / `pyproject.toml` / `docs/Specification_Prompt_v3.md` / `docs/MS11-5_Implementation_Plan.md` / `docs/repo_milestone.md` の版数・同期記述を更新した。
  - リポジトリ全体の反映版を `Ver 0.3.6.2` として確定した。
- Modified Files:
  - `README.md`: 版数表記を `Ver 0.3.6.2` に更新。
  - `pyproject.toml`: プロジェクトバージョンを `0.3.6.2` に更新。
  - `docs/Specification_Prompt_v3.md`: 対応リリースを `Ver 0.3.6.2` に更新し、MS11-5 一部反映状態を同期。
  - `docs/MS11-5_Implementation_Plan.md`: 前提到達版を `Ver 0.3.6.2` に更新。
  - `docs/repo_milestone.md`: `Ver 0.3.6.2` 同期メモを追記。
  - `docs/Version_Control.md`: 本エントリを追加。
- Added Files:
  - なし
- Notes:
  - 実装詳細自体は `ms11-5-observation-helper-and-tests` エントリを正本とする。
  - 実データ観測結果の整理と RMS 定数再調整要否の判断整理は、今回の release sync には含めていない。
- Verification:
  - `rg -n "Ver 0.3.6.2|0.3.6.2" README.md pyproject.toml docs/Specification_Prompt_v3.md docs/MS11-5_Implementation_Plan.md docs/repo_milestone.md docs/Version_Control.md`
  - `git status --short`

---

## Entry 2026-03-30 / Session: ms11-5-observation-helper-and-tests

- Date: 2026-03-30
- Session: ms11-5-observation-helper-and-tests
- Summary:
  - `pipeline.py` を主対象として、MS11-5 の第一段階である observation helper / observation record / pipeline 系テスト拡張を実装した。
  - 既存 `PeakValueEvaluation` は維持したまま、event 単位で元 interval / RMS 補正後 interval / peak window / `local_peak` / `global_peak` / `peak_value` / `reason` / fallback 情報 / window sample 数をまとめて扱える `PeakValueObservation` を追加した。
  - `tests/test_pipeline_peak_values.py` を拡張し、観測値整合の観点を追加したうえで、pipeline-writer 既存導線の回帰も確認した。
- Modified Files:
  - `src/core/pipeline.py`: `PeakValueObservation` と `_build_peak_value_observations()` を追加し、既存 peak 評価結果を再利用する観測 helper を実装。
  - `tests/test_pipeline_peak_values.py`: 元 interval / 補正後 interval、halo 窓、fallback 観測、initial timeline 長不一致のテストを追加。
  - `docs/Specification_Prompt_v3.md`: MS11-5 一部反映状態を同期。
  - `docs/repo_milestone.md`: MS11-5 観測支援 実装反映メモを追記。
  - `docs/MS11-5_Implementation_Plan.md`: 観測契約方針と第一段階の到達状態を同期。
  - `docs/MS11_Remaining_Issues_and_Next_Milestones.md`: MS11-5 の現時点到達と残課題を更新。
  - `docs/Version_Control.md`: 本エントリを追加。
- Added Files:
  - なし
- Notes:
  - `PeakValueEvaluation` は破壊的に置き換えず、上位観測レコードを追加する方針を採った。
  - 実データ観測整理と RMS 定数再調整要否の判断整理は今回未着手のままとし、後続作業として維持した。
- Verification:
  - `.\.venv\Scripts\python.exe -m unittest tests.test_pipeline_peak_values`
  - `$env:PYTHONPATH='src;tests'; .\.venv\Scripts\python.exe -m unittest tests.test_pipeline_and_vmd`
  - `.\.venv\Scripts\python.exe -m unittest tests.test_vmd_writer_peak_value`

---

## Entry 2026-03-29 / Session: release-v0361-repo-sync

- Date: 2026-03-29
- Session: release-v0361-repo-sync
- Summary:
  - MS11-4 の `pipeline.py` 品質改善と関連ドキュメント反映を含む現作業ツリーを `Ver 0.3.6.1` として同期した。
  - `README.md` / `pyproject.toml` / `docs/Specification_Prompt_v3.md` / `docs/repo_milestone.md` の版数・同期記述を更新した。
  - ワークスペース上に存在していた関連ドキュメントや周辺差分も、今回の同期対象としてまとめて反映した。
- Modified Files:
  - `README.md`: 版数表記を `Ver 0.3.6.1` に更新。
  - `pyproject.toml`: プロジェクトバージョンを `0.3.6.1` に更新。
  - `docs/Specification_Prompt_v3.md`: 対応リリースを `Ver 0.3.6.1` に更新し、MS11-4 反映状態を同期。
  - `docs/repo_milestone.md`: `Ver 0.3.6.1` 同期メモを追記。
  - `docs/Version_Control.md`: 本エントリを追加。
- Added Files:
  - なし
- Notes:
  - この同期は release sync であり、実装詳細自体は `ms11-4-pipeline-quality-and-doc-sync` エントリを正本とする。
  - `writer.py` 再設計、GUI / Preview 改修、MS11-5 全面実装は今回も含めていない。
- Verification:
  - `rg -n "Ver 0.3.6.1|0.3.6.1" README.md pyproject.toml docs/Specification_Prompt_v3.md docs/repo_milestone.md docs/Version_Control.md`
  - `git status --short`

---

## Entry 2026-03-29 / Session: ms11-4-pipeline-quality-and-doc-sync

- Date: 2026-03-29
- Session: ms11-4-pipeline-quality-and-doc-sync
- Summary:
  - `pipeline.py` を主対象として MS11-4 を実装し、RMS 補正後 interval を正本にした peak 評価、halo 付き peak window、保守的 fallback、`peak_value = 0.0` 理由分類を導入した。
  - `tests/test_pipeline_peak_values.py` を中心に pipeline 単体テストを拡張し、halo 内 peak 採用、`rms_unavailable`、`global_peak_zero`、各 0.0 理由の優先順を自動確認できる状態にした。
  - `tests.test_pipeline_and_vmd` および writer 既存テストを通して、`writer.py` 再設計なしで既存到達状態を維持していることを確認した。
  - 関連ドキュメントへ MS11-4 到達状態と、MS11-5 へ持ち越す残課題を反映した。
- Modified Files:
  - `src/core/pipeline.py`: 正本 interval と peak window の責務分離、halo `±0.03 sec`、保守的 RMS fallback、0.0 理由分類 helper を追加。
  - `tests/test_pipeline_peak_values.py`: MS11-4 の単体観点を追加し、halo / fallback / 理由分類優先順を検証するよう更新。
  - `docs/repo_milestone.md`: MS11-4 実装反映メモと残課題を追記。
  - `docs/MS11_Remaining_Issues_and_Next_Milestones.md`: MS11-4 完了後の到達状態と残タスク整理を追記。
  - `docs/Specification_Prompt_v3.md`: MS11-4 反映後の実装同期注記を更新。
  - `docs/Version_Control.md`: 本エントリを追加。
- Added Files:
  - なし
- Notes:
  - event は削除せず、interval を維持したまま `peak_value` と理由分類の整合を改善する方針を維持した。
  - GUI / Preview 改修、`writer.py` 再設計、MS11-5 全面実装には広げていない。
- Verification:
  - `.\.venv\Scripts\python.exe -m unittest tests.test_pipeline_peak_values`
  - `.\.venv\Scripts\python.exe -m unittest tests.test_pipeline_and_vmd tests.test_vmd_writer_peak_value`
  - `.\.venv\Scripts\python.exe -m unittest tests.test_vmd_writer_zero_guard tests.test_vmd_writer_intervals`
  - `.\.venv\Scripts\python.exe -m unittest tests.test_pipeline_peak_values tests.test_pipeline_and_vmd tests.test_vmd_writer_peak_value tests.test_vmd_writer_zero_guard tests.test_vmd_writer_intervals`

---

## Entry 2026-03-28 / Session: release-v0360-ms11-3-sync

- Date: 2026-03-28
- Session: release-v0360-ms11-3-sync
- Summary:
  - MS11-3 の実装、段階 fallback、envelope 保護、FIX01 / FIX02 整合、writer 局所の zero-only shape / short fallback 保護修正までを `Ver 0.3.6.0` として同期した。
  - Known Issues の「無音に見える区間の開口残存」は今回も未解決の既知課題として維持し、解決済み扱いにはしなかった。
- Modified Files:
  - `README.md`: 版数表記を `Ver 0.3.6.0` に更新。
  - `pyproject.toml`: プロジェクトバージョンを `0.3.6.0` に更新。
  - `docs/repo_milestone.md`: `Ver 0.3.6.0` 同期メモを追記。
  - `docs/Version_Control.md`: 本エントリを追記。
  - `docs/Specification_Prompt_v3.md`: 対応リリースと MS11-3 後の writer 局所修正反映を最小差分で更新。
  - `src/vmd_writer/writer.py`: zero-only shape 抑止と short fallback 保護の局所修正。
  - `tests/test_vmd_writer_peak_value.py`: zero-peak 期待値を新仕様へ更新。
  - `tests/test_vmd_writer_zero_guard.py`: zero-only shape / short fallback 保護の回帰防止テストを追加。
  - `tests/test_vmd_writer_grouping.py`: MS11-3 grouping テストを追加。
  - `tests/test_vmd_writer_multipoint_shape.py`: MS11-3 shape / fallback テストを追加。
- Added Files:
  - なし
- Notes:
  - `pipeline.py` は変更していない。
  - GUI / Preview の multi-point 表示対応、Known Issues 解消、出力仕様全体の再設計は今回の同期対象外とした。
- Verification:
  - `$env:PYTHONPATH='src'; .\.venv\Scripts\python.exe -m unittest tests.test_vmd_writer_grouping tests.test_vmd_writer_intervals tests.test_vmd_writer_peak_value tests.test_vmd_writer_multipoint_shape tests.test_vmd_writer_zero_guard`
  - `$env:PYTHONPATH='src;tests'; .\.venv\Scripts\python.exe -m unittest tests.test_pipeline_and_vmd tests.test_pipeline_peak_values`
  - `git diff -- README.md pyproject.toml docs/repo_milestone.md docs/Version_Control.md docs/Specification_Prompt_v3.md`

---

## Entry 2026-03-28 / Session: ms11-3-doc-sync

- Date: 2026-03-28
- Session: ms11-3-doc-sync
- Summary:
  - MS11-3 の実装・検証結果に合わせて、multi-point shape / grouping / fallback / envelope 保護 / FIX01-FIX02 整合の反映内容を文書へ同期した。
  - Known Issues の「無音に見える区間の開口残存」は今回も未解決の既知課題として維持し、解決済み扱いにはしなかった。
- Modified Files:
  - `docs/repo_milestone.md`: MS11-3 実装完了メモを追記。
  - `docs/Version_Control.md`: 本エントリを追記。
  - `docs/Specification_Prompt_v3.md`: MS11-3 反映済み範囲と残課題の記述を最小差分で更新。
- Added Files:
  - なし
- Notes:
  - コード変更・テスト変更は行わず、タスク1〜11 で確認済みの事実だけを反映した。
  - `pipeline.py` の再設計、GUI / Preview の multi-point 表示対応、Known Issues 解消は今回の反映対象外とした。
- Verification:
  - `.\.venv\Scripts\python.exe -m unittest tests.test_vmd_writer_grouping tests.test_vmd_writer_intervals tests.test_vmd_writer_peak_value tests.test_vmd_writer_multipoint_shape tests.test_vmd_writer_zero_guard`
  - `$env:PYTHONPATH='src;tests'; .\.venv\Scripts\python.exe -m unittest tests.test_pipeline_and_vmd`
  - `git diff -- docs/repo_milestone.md docs/Version_Control.md docs/Specification_Prompt_v3.md`

---

## Entry 2026-03-27 / Session: release-v0359-ms11-2-fix-sync

- Date: 2026-03-27
- Session: release-v0359-ms11-2-fix-sync
- Summary:
  - MS11-2 / MS11-2_FIX01 / MS11-2_FIX02 の実装反映状態に合わせて、関連ドキュメントと版表記を `Ver 0.3.5.9` として同期した。
  - writer 後段の保護・cleanup 補正、関連テスト更新、既知制約の整理をリリース文書へ反映した。
- Modified Files:
  - `README.md`: 版数表記を `Ver 0.3.5.9` に更新。
  - `pyproject.toml`: プロジェクトバージョンを `0.3.5.9` に更新。
  - `docs/Specification_Prompt_v3.md`: 対応リリースを `Ver 0.3.5.9` に更新。
  - `docs/repo_milestone.md`: `Ver 0.3.5.9` 同期メモを追加。
  - `docs/Version_Control.md`: 本エントリを追加。
- Added Files:
  - なし
- Notes:
  - 過去の `Ver 0.3.5.8` 記録は履歴として維持し、今回分は追加エントリとして追記した。
  - MS11-2 本体と FIX01 / FIX02 のコード・テスト変更は、同一コミットに含める前提で整理した。
- Verification:
  - `.\.venv\Scripts\python.exe -m unittest tests.test_vmd_writer_intervals tests.test_vmd_writer_peak_value tests.test_vmd_writer_zero_guard`
  - `rg -n "0\.3\.5\.8|0\.3\.5\.9|Ver 0\.3\.5\.8|Ver 0\.3\.5\.9" README.md pyproject.toml docs`

---

## Entry 2026-03-27 / Session: ms11-2-fix-doc-sync

- Date: 2026-03-27
- Session: ms11-2-fix-doc-sync
- Summary:
  - MS11-2_FIX01 / MS11-2_FIX02 の実装結果に合わせて、マイルストーン・仕様書・計画書・変更履歴の文書同期を行った。
  - writer 後段の保護範囲拡張、許容外非ゼロ除去、不要ゼロ prune、ゼロ縮退抑止、および既知課題切り分けを文書へ整理した。
- Modified Files:
  - `docs/repo_milestone.md`: MS11-2_FIX01 / FIX02 実装完了メモを追加。
  - `docs/Specification_Prompt_v3.md`: MS11 の到達状態と残課題の記述を FIX02 完了時点へ更新。
  - `docs/MS11-2_FIX01_Implementation_Plan.md`: 実装反映メモを追加。
  - `docs/MS11-2_FIX02_Implementation_Plan.md`: 実装反映メモを追加。
  - `docs/Version_Control.md`: 本エントリを追加。
- Added Files:
  - なし
- Notes:
  - 反映対象は文書同期のみとし、このセッションではコード仕様自体は変更していない。
  - `docs/MS11-2_Known_Issues.md` は FIX02 完了時点の既知課題メモとして継続利用する。
- Verification:
  - `.\.venv\Scripts\python.exe -m unittest tests.test_vmd_writer_intervals tests.test_vmd_writer_peak_value tests.test_vmd_writer_zero_guard`
  - `rg -n "MS11-2|FIX01|FIX02|Known Issues|残課題" docs`

---

## Entry 2026-03-27 / Session: ms11-2-doc-sync

- Date: 2026-03-27
- Session: ms11-2-doc-sync
- Summary:
  - MS11-2 の実装結果に合わせて、仕様書・マイルストーン・実装計画書・変更履歴の文書同期を行った。
  - `writer.py` の変形台形導入、短区間フォールバック維持、MS11-1 最終正規化との部分保護接続、関連テスト反映内容を文書へ整理した。
- Modified Files:
  - `docs/Specification_Prompt_v3.md`: MS11-2 反映済み状態、`writer.py` 責務、テスト方針、残課題を更新。
  - `docs/repo_milestone.md`: MS11-2 実装完了メモを追加。
  - `docs/MS11-2_Implementation_Plan.md`: 実装反映メモを追加。
  - `docs/Version_Control.md`: 本エントリを追加。
- Added Files:
  - なし
- Notes:
  - 反映対象は文書同期のみとし、MS11-2 のコード仕様自体はこのセッションでは変更していない。
  - `pipeline.py` / `text_processing.py` / GUI 系の文書スコープ拡張は行っていない。
- Verification:
  - `rg -n "MS11-2|変形台形|AsymmetricTrapezoidSpec|部分保護" docs/Specification_Prompt_v3.md docs/repo_milestone.md docs/MS11-2_Implementation_Plan.md docs/Version_Control.md`

---

## Entry 2026-03-26 / Session: ms11-1-doc-sync

- Date: 2026-03-26
- Session: ms11-1-doc-sync
- Summary:
  - MS11-1 の実装結果に合わせて、仕様書・マイルストーン・実装計画書・変更履歴の文書同期を行った。
  - `writer.py` の最終正規化層、重複統合、母音全体開口判定、孤立短開口抑制、個別モーフ短パルス整理、関連テストの反映内容を文書へ整理した。
- Modified Files:
  - `docs/Specification_Prompt_v3.md`: MS11-1 反映済み状態、`writer.py` 責務、VMD 出力仕様、テスト方針、残課題を更新。
  - `docs/repo_milestone.md`: MS11-1 実装完了メモを追加。
  - `docs/MS11-1_Implementation_Plan.md`: 実装反映メモを追加。
  - `docs/Version_Control.md`: 本エントリを追加。
- Added Files:
  - なし
- Notes:
  - 反映対象は文書同期のみとし、MS11-1 のコード仕様自体はこのセッションでは変更していない。
  - `docs/repo_milestone.md` に既存の conflict marker が残っているが、今回はその周辺を解消せず、MS11-1 の追記に限定した。
- Verification:
  - `rg -n "MS11-1|最終モーフフレーム正規化層|孤立短開口|個別モーフ短パルス|30fps丸め衝突" docs/Specification_Prompt_v3.md docs/repo_milestone.md docs/MS11-1_Implementation_Plan.md docs/Version_Control.md`

---
## Entry 2026-03-25 / Session: release-v0358-ms10-sync

- Date: 2026-03-25
- Session: release-v0358-ms10-sync
- Summary:
  - MS10 対応の実装と関連ドキュメント更新を、`Ver 0.3.5.8` として同期した。
  - 設定永続化、多言語化、recent 履歴、波形表示 / Preview の言語反映を含む到達状態をリリース版として整理した。
- Modified Files:
  - `README.md`: 版数表記を `Ver 0.3.5.8` に更新。
  - `pyproject.toml`: プロジェクトバージョンを `0.3.5.8` に更新。
  - `docs/Specification_Prompt_v3.md`: 対応リリースを `Ver 0.3.5.8` に更新。
  - `docs/repo_milestone.md`: MS10 実装完了状態を反映したうえで `Ver 0.3.5.8` 同期メモを追記。
  - `docs/Version_Control.md`: 本エントリを追加。
- Added Files:
  - なし
- Notes:
  - 今回のリリース同期には MS10 実装本体と、その文書反映を含む。
  - IDE 設定ファイル、`__pycache__`、ローカル設定 `.ini` はリリース対象に含めない。
- Verification:
  - `rg -n "Ver 0.3.5.8|0.3.5.8" README.md pyproject.toml docs/Specification_Prompt_v3.md docs/repo_milestone.md docs/Version_Control.md`

---
## Entry 2026-03-25 / Session: ms10-doc-sync

- Date: 2026-03-25
- Session: ms10-doc-sync
- Summary:
  - MS10 の実装到達状態に合わせて、関連ドキュメントの現状記述を同期した。
  - 設定永続化、多言語化、recent 履歴、波形表示 / Preview の言語反映、Matplotlib 和文フォント対応までを文書へ反映した。
  - 実装済み範囲と対象外範囲が文書上で読み取れるように整理した。
- Modified Files:
  - `docs/MS10_Implementation_Plan.md`: 実装反映結果セクションを追加し、MS10 の実到達状態を明文化。
  - `docs/repo_milestone.md`: MS10 実装完了メモを追加。
  - `docs/Version_Control.md`: 本エントリを追加。
- Added Files:
  - なし
- Notes:
  - 今回はドキュメント反映のみであり、追加の機能実装や仕様変更は含まない。
  - 波形表示オプション永続化、再生カーソル平滑化、再生ロジック再設計は引き続き対象外のまま維持。
- Verification:
  - `git diff -- docs/MS10_Implementation_Plan.md docs/repo_milestone.md docs/Version_Control.md`

---

このファイルは、セッション単位で変更内容を追記するためのログです。
下へ追記して運用してください（既存エントリは編集せず、必要時のみ訂正注記を追加）。

## Entry Template

- Date: YYYY-MM-DD
- Session: <短い識別子>
- Summary:
  - <要約1>
  - <要約2>
- Modified Files:
  - `<path>`: <変更概要>
- Added Files:
  - `<path>`: <追加概要>
- Notes:
  - <補足>
- Verification:
  - <実行コマンドと結果>

---

## Entry 2026-03-23 / Session: guifix06-waveform-preview-alignment

- Date: 2026-03-23
- Session: guifix06-waveform-preview-alignment
- Summary:
  - 波形表示と母音プレビュー表示の横軸基準不一致問題（GUIFIX06）を解消した。
  - WaveformView（Matplotlib）のAxes物理座標を正基準とし、PreviewAreaが動的にその矩形をコピーして描画基準とする構造を導入した。
  - リサイズ、Zoom、Pan、スプリッター操作後も再通知経路（draw_event等）により整合が維持されることを確認した。
  - 母音ラベル（あ、い...）を右寄せにし、グリッドに隣接するように視認性を改善した。
  - バージョンを `Ver 0.3.5.7` に更新し、リリース同期した。
- Modified Files:
  - `src/gui/waveform_view.py`: plot area 矩形の外部取得メソッド追加、データ未ロード時のガード緩和
  - `src/gui/preview_area.py`: 外部から波形基準矩形を受け取って描画範囲を決定するよう変更、ラベル右寄せ、グリッド基準投影の修正
  - `src/gui/main_window.py`: Matplotlib イベントフックによる同期要求パスの追加、初期/動的な同期配線、バージョン更新
  - `pyproject.toml`: バージョン更新
  - `README.md`: バージョン更新、横軸整合とラベル右寄せの改善追記
  - `docs/GUIFIX_Implementation_Plan.md`: 全フェーズ (1-10) の検証と結果を記録
  - `docs/repo_milestone.md`: GUIFIX06 の完了を追記、バージョン更新
  - `docs/Specification_Prompt_v3.md`: 対応リリース更新
  - `docs/Version_Control.md`: 本エントリを追加
- Added Files:
  - なし
- Notes:
  - 既存の秒ベース同期ロジック（ViewSync）は維持しつつ、物理ピクセル投影の基準を波形側へ一本化した。
  - 初期状態（データ未ロード）での不一致も Phase 9 で解消済み。
- Verification:
  - コード解析による論理検証。各イベント（resize/draw/pan/splitter）から `_request_waveform_bounds_sync` への到達を確認。

---

## Entry 2026-03-23 / Session: sec01-sec02-implementation

- Date: 2026-03-23
- Session: sec01-sec02-implementation
- Summary:
  - セキュリティおよび安全性向上を目的とする「実装リストSEC01」「実装リストSEC02」を実装完了した。
  - TEXT長・WAV長・VMD上限フレーム数の静的ガード（SEC01）と、詳細なTEXT/WAVバリデーション、VMD上書き防止（SEC02）を組み込んだ。
  - バージョン表記は `Ver 0.3.5.6` を維持し、ドキュメントのみ同期更新した。
- Modified Files:
  - `src/core/text_processing.py`: TEXT制限（上限5000字、制御文字、行長、記号長大行）、ZWJ等のホワイトリスト化を追加
  - `src/core/audio_processing.py`: WAV制限（上限15分）、非対応フォーマット例外のメッセージ改善を追加
  - `src/vmd_writer/writer.py`: VMD上限（22000フレーム）の安全ガードを追加
  - `src/gui/main_window.py`: TEXT文字コードフォールバック読込、VMD上書き確認ダイアログを追加
  - `tests/test_text_processing.py`: 絵文字（ZWJ等）許容パターンのテストを追加
  - `docs/repo_milestone.md`: SEC01/SEC02 進捗メモを追記
  - `docs/Version_Control.md`: 本エントリを追記
- Added Files:
  - なし
- Notes:
  - バージョン表記（`Ver 0.3.5.6`）は変更していない。
  - 絵文字（ZWJ等）が制御文字として弾かれるバグを SEC02 フェーズ4 で併せて解決済み。
- Verification:
  - `.\.venv\Scripts\python.exe -m unittest discover -s tests` を実行し、全件（37件）PASSを確認。

---

## Entry 2026-03-22 / Session: release-sync-v0356

- Date: 2026-03-22
- Session: release-sync-v0356
- Summary:
  - 現作業ツリーの到達点を `Ver 0.3.5.6` としてリリース同期した。
  - MS9-2 本実装、局所 UI 修正、関連文書更新を含む状態でバージョン表記を更新した。
- Modified Files:
  - `README.md`: 版数表記を `Ver 0.3.5.6` に更新
  - `pyproject.toml`: プロジェクトバージョンを `0.3.5.6` に更新
  - `src/gui/i18n_strings.py`: バージョン情報ダイアログのアプリ版数表記を `Ver 0.3.5.6` に更新
  - `docs/Specification_Prompt_v3.md`: 対応リリースを `Ver 0.3.5.6` に更新
  - `docs/repo_milestone.md`: リポジトリ全体の反映版表記を `Ver 0.3.5.6` に更新
  - `docs/Version_Control.md`: 本エントリを追記
- Added Files:
  - なし
- Notes:
  - 設定永続化や多言語化本実装は含めず、MS10 以降へ持ち越す前提を維持している。
- Verification:
  - `rg -n "Ver 0.3.5.6|0.3.5.6" README.md pyproject.toml src/gui/i18n_strings.py docs/Specification_Prompt_v3.md docs/repo_milestone.md`

---

## Entry 2026-03-22 / Session: ms9-2-gui-polish-and-docs-sync

- Date: 2026-03-22
- Session: ms9-2-gui-polish-and-docs-sync
- Summary:
  - MS9-2 として、初期表示サイズ・初期 splitter 比率・操作ボタンの左詰め配置・assets アイコン差し替え・余白密度調整を段階実装した。
  - モーフ上限値入力欄は短幅固定の `QDoubleSpinBox` を維持しつつ、内蔵スピンボタンを廃止して独立した `-` / `+` ボタン構成へ置換した。
  - README / 仕様書 / マイルストーン管理文書へ、MS9-2 完了状態と局所修正後の到達点を反映した。
- Modified Files:
  - `src/gui/main_window.py`: MS9-2 の初期サイズ・初期 splitter 比率適用補正・テーマ内フォント/余白基準・モーフ入力部局所スタイルを反映
  - `src/gui/operation_panel.py`: ボタン横長化抑制、主要ボタン 1 行表示、assets アイコン差し替え、左詰めグループ配置、行高調整を反映
  - `src/gui/central_panels.py`: モーフ上限値入力欄の短幅固定と独立した `-` / `+` ボタン構成を反映
  - `README.md`: MS9-2 完了状態と現状整理を反映
  - `docs/repo_milestone.md`: MS9-2 完了メモを追記
  - `docs/Specification_Prompt_v3.md`: 実装同期注記と MS9-2 反映済み事項を更新
  - `docs/Version_Control.md`: 本エントリを追記
- Added Files:
  - なし
- Notes:
  - 設定永続化、多言語化本実装、shared viewport / playback / zoom / scrollbar の責務変更、波形 / Preview 描画ロジック変更は今回も対象外のまま維持した。
  - `src/gui/i18n_strings.py` はリポジトリ実体ありのため、文書上の「未作成」扱いを解消した。
- Verification:
  - `.\.venv\Scripts\python.exe -m py_compile src\gui\main_window.py src\gui\operation_panel.py src\gui\central_panels.py src\gui\status_panel.py`
  - `QT_QPA_PLATFORM=offscreen` で `MainWindow` を生成し、初期サイズ `1270x714`、最小サイズ `720x405`、初期 splitter 実効比率、操作ボタン size hint、モーフ入力欄 size hint、assets アイコン適用を確認

---

## Entry 2026-03-22 / Session: ms9-final-doc-priority-and-receptacle-clarification

- Date: 2026-03-22
- Session: ms9-final-doc-priority-and-receptacle-clarification
- Summary:
  - MS9 詳細要件の正本を `docs/MS9_GUI_Requirements.md` とし、`Specification_Prompt_v3.md` より優先して解釈する方針を文書上で明示した。
  - `Specification_Prompt_v3.md` の `StatusPanel` 記述を、単なる文字列表示器と誤読されないよう調整した。
  - `i18n_strings.py` / `settings_store.py` について、「MS9 では全面導入不要だが、受け皿整理は対象」と読めるように整理した。
- Modified Files:
  - `docs/MS9_GUI_Requirements.md`: MS9 詳細要件の正本であること、全体仕様文書との優先順位、受け皿整理の扱いを明確化
  - `docs/Specification_Prompt_v3.md`: `OperationPanel` / `StatusPanel` / 受け皿整理の解釈を MS9 要件書と衝突しない形へ調整
  - `docs/Version_Control.md`: 本エントリを追記
- Added Files:
  - なし
- Notes:
  - 今回は文書整合作業のみで、コード実装や GUI 動作変更は行っていない。
  - `docs/repo_milestone.md` は現時点の記述で十分と判断し、今回は更新対象から外した。
- Verification:
  - `docs/MS9_GUI_Requirements.md` / `docs/Specification_Prompt_v3.md` / `docs/repo_milestone.md` / `docs/Version_Control.md` の該当箇所を読解して優先順位と用語整合を確認

---

## Entry 2026-03-22 / Session: ms9-docs-alignment-and-milestone-restructure

- Date: 2026-03-22
- Session: ms9-docs-alignment-and-milestone-restructure
- Summary:
  - MS9 詳細要件を `docs/MS9_GUI_Requirements.md` 正本として扱う前提で、仕様書・README・版管理文書の参照関係を整理した。
  - `Specification_Prompt_v3.md` では、実装済み GUI モジュールと未実装の予定ファイルを明示的に分離した。
  - `README.md` の古い現状整理を、現行の `docs/` 配下文書構成と MS9 / MS10 前提に合わせて更新した。
- Modified Files:
  - `docs/Specification_Prompt_v3.md`: 予定ファイルの明示、実装済み責務と未実装予定責務の分離、MS9 正本位置づけの追記
  - `README.md`: 文書参照先の整理、古いルート前提の現状整理を現行構成へ更新
  - `docs/Version_Control.md`: 本エントリを追記
- Added Files:
  - なし
- Notes:
  - 今回はドキュメント整備のみで、ソースコードの編集・追加は行っていない。
  - `docs/MS9_GUI_Requirements.md` は MS9 詳細要件の正本として扱う前提で整理した。
- Verification:
  - 文書相互参照の整合を読解で確認
  - `README.md` / `docs/Specification_Prompt_v3.md` / `docs/repo_milestone.md` / `docs/MS9_GUI_Requirements.md` の用語とマイルストーン番号を突き合わせて確認

---

## Entry 2026-03-22 / Session: ms8d2-zoom-center-basis-fix-and-docs-sync

- Date: 2026-03-22
- Session: ms8d2-zoom-center-basis-fix-and-docs-sync
- Summary:
  - MS8D-2 の Zoom 基準不一致を補正し、Pan 後の Zoom でも shared viewport の左端を 0.0 秒へ戻さず、現在 viewport の中心を保持して拡大縮小する挙動へ修正した。
  - Zoom span の再計算時に WAV 全体長境界へ収める補正を追加し、全体表示・左右端近傍・不正値回避の導線を既存初期化/復帰ロジックと両立させた。
  - `docs/repo_milestone.md`、`docs/MS8D-2_Requirements_and_Spec_Update.md`、`docs/Specification_Prompt_v3.md` に本修正内容を反映した。
- Modified Files:
  - `src/gui/main_window.py`: `_apply_zoom_level_to_shared_viewport()` を中心保持 Zoom に変更し、左右境界補正と全体表示復帰条件を追加
  - `docs/repo_milestone.md`: 2026-03-22 の MS8D-2 完了メモへ Zoom 基準補正を追記
  - `docs/MS8D-2_Requirements_and_Spec_Update.md`: Zoom の正しい基準と境界補正仕様、2026-03-22 実装修正メモを追記
  - `docs/Specification_Prompt_v3.md`: Zoom In / Zoom Out の仕様に「現在 viewport の中心保持」を追記
  - `docs/Version_Control.md`: 本エントリを追記
- Added Files:
  - なし
- Notes:
  - Pan 導線、shared viewport 同期、Zoom 有効/無効条件、初期化/復帰時の全体表示リセット導線は変更していない。
  - 今回の修正は通常の Zoom 操作時のみの補正であり、MS8E 以降の作業は含まない。
- Verification:
  - `.\.venv\Scripts\python.exe -m py_compile src\gui\main_window.py`
  - `PYTHONPATH=src` 相当で `MainWindow._apply_zoom_level_to_shared_viewport()` のスタブ検証を実行し、Pan 後 Zoom、左右端近傍、全体表示復帰を確認

---

## Entry 2026-03-21 / Session: ms8c-phases1-to-10-implementation-and-final-check

- Date: 2026-03-21
- Session: ms8c-phases1-to-10-implementation-and-final-check
- Summary:
  - MS8C フェーズ1〜10として、再生基盤（`PlaybackController` / `ViewSync`）と `main_window.py` 配線、Play/Stop action state、波形/Preview/ステータスの共通位置同期を実装した。
  - 共通位置正本を「秒ベース絶対値」に統一し、再生開始は常に 0.0 秒起点、再生停止/終了/解析結果無効化時は 0.0 秒リセットへ統一した。
  - TEXT/WAV 再読込、読込失敗、入力不足、再解析待ち、`suppress_warning=True` 復元を含む既存入口で、再生状態取り残しを無効化正規導線へ集約した。
- Modified Files:
  - `src/gui/main_window.py`: MS8C 全体の司令塔配線（controller/sync接続、Play/Stop 状態判定、ステータス反映、無効化統合、入口整合）
  - `src/gui/waveform_view.py`: 秒ベース再生位置カーソルの受け取り/描画/クリア導線
  - `src/gui/preview_area.py`: 秒ベース再生位置カーソルの受け取り/描画/クリア導線
  - `README.md`: MS8C 完了状態を反映（再生/同期対応、非対応一覧更新）
  - `docs/repo_milestone.md`: MS8C 完了メモを追記
  - `docs/Version_Control.md`: 本エントリを追記
- Added Files:
  - `src/gui/playback_controller.py`: 実 WAV 再生、停止、終了検知、秒位置通知、開始/終了時 0.0 秒統一
  - `src/gui/view_sync.py`: 共有秒位置の保持/配布/リセットの最小ハブ
- Notes:
  - MS8D 以降（Zoom、スクラブ、手動シーク、表示詳細化、`pipeline.py` 仕様変更）は未着手のまま維持。
  - 既存主要導線（TEXT読込 / WAV読込 / 処理実行 / VMD出力）は維持。
- Verification:
  - `.\.venv\Scripts\python.exe -m py_compile src\gui\main_window.py src\gui\playback_controller.py src\gui\view_sync.py src\gui\waveform_view.py src\gui\preview_area.py src\gui\status_panel.py src\gui\operation_panel.py`
  - `rg -n "can_play|can_stop|start_playback|shared_position_sec_changed|shared_position_reset|_invalidate_current_timing_plan" src/gui/main_window.py src/gui/playback_controller.py src/gui/view_sync.py`
  - `git diff --name-only -- src/core src/vmd_writer src/gui/preview_transform.py src/core/pipeline.py src/core/whisper_timing.py`（非対象領域の未変更確認）
---

## Entry 2026-03-19 / Session: vowel-interval-rms-integration

- Date: 2026-03-19
- Session: vowel-interval-rms-integration
- Summary:
  - 最終母音イベントを `time_sec` 単体運用から区間運用（`duration_sec/start_sec/end_sec`）へ拡張。
  - WAV から RMS 系列を取得し、イベント区間を簡易ルールで補正する処理を追加。
  - VMD 出力を `start_sec/end_sec` 優先の台形構築に接続し、GUI 波形表示と同一イベント列を共有。
- Modified Files:
  - `src/core/audio_processing.py`: RMS 系列データ構造と読み出し処理（窓・ホップ・平滑化定数）を追加。
  - `src/core/pipeline.py`: 母音イベント区間の推定/整形、RMS ベース境界補正、隣接衝突回避、フォールバック処理を追加。
  - `src/core/__init__.py`: 追加データ構造/関数の公開整理。
  - `src/gui/main_window.py`: 生成した最終母音イベント列を波形表示へ直接渡す導線を維持・整理。
  - `src/gui/waveform_view.py`: 同一イベント列参照のまま、ラベル位置 `time_sec` と区間境界参照を併用可能な構造を維持。
  - `src/vmd_writer/writer.py`: `start_sec/end_sec` を優先して rise/hold/fall を組み立てる区間ベースフレーム生成へ変更（短区間フォールバック維持）。
  - `tests/test_audio_processing.py`: RMS 系列生成の基本テストを追加/更新。
  - `tests/test_pipeline_and_vmd.py`: 区間付きイベント前提の検証を更新。
- Added Files:
  - `tests/test_vmd_writer_intervals.py`: 区間ベースVMD（台形・短区間三角・ゼロ区間フォールバック）の単体テストを追加。
- Notes:
  - UIの大きな見た目変更は未実施。
  - モーフ高さの音量連動は未実装（固定 `0.5` 維持）。
- Verification:
  - `.\.venv\Scripts\python.exe -m unittest discover -s tests` を実行し、`OK` を確認。

---

## Entry 2026-03-19 / Session: pre-rise-zero-guard-v0332

- Date: 2026-03-19
- Session: pre-rise-zero-guard-v0332
- Summary:
  - 台形モーフで同一モーフ再登場時に発生する「立ち上がり前ゼロ不足」を最小変更で補正。
  - 同一モーフ・同一フレームの 0/非0 衝突を検出し、rise_start の 0 を 1 フレーム前へ退避。
  - README/仕様書を Ver 0.3.3.2 の内容へ更新。
- Modified Files:
  - `src/vmd_writer/writer.py`: rise_start ゼロ衝突の検出・退避ロジックを追加。
  - `README.md`: バージョンを `Ver 0.3.3.2` に更新し、ゼロ保証修正を機能欄へ追記。
  - `Specifications_Prompt_v1.md`: 立ち上がり前ゼロ保証の仕様追補を追加。
  - `docs/Version_Control.md`: 本エントリを追記。
- Added Files:
  - `tests/test_vmd_writer_zero_guard.py`: 同フレーム衝突時の `-1` フレーム退避と frame 0 例外のテストを追加。
- Notes:
  - モーフ高さの音量連動は未実装（固定値運用のまま）。
  - GUI表示用イベント列とVMD出力用イベント列の二重化はしていない。
- Verification:
  - `\.\.venv\Scripts\python.exe -m unittest discover -s tests` を実行し、`OK (26 tests)` を確認。

---

## Entry 2026-03-19 / Session: peak-value-upper-limit-gui-v0340

- Date: 2026-03-19
- Session: peak-value-upper-limit-gui-v0340
- Summary:
  - 母音イベントに `peak_value` を保持し、VMD非ゼロキーへ固定 `0.5` ではなくイベント別値を接続。
  - `upper_limit`（既定 `0.5`）を内部処理に追加し、`peak_value` を `0.0..upper_limit` へクランプする導線を実装。
  - GUI に「モーフ上限値」入力欄を最小追加し、同一イベント列（`timing_plan.timeline`）を表示と出力で共通利用。
  - 仕様書/README を本セッション実装に合わせて更新。
- Modified Files:
  - `src/vmd_writer/writer.py`: `peak_value` 優先のモーフ値参照、最終書き込み時の丸め、固定 `0.5` 上限クランプの撤去。
  - `src/core/pipeline.py`: `upper_limit` パラメータ追加、RMS ベースの `peak_value` 算出とクランプ、フォールバック処理を追加。
  - `src/gui/main_window.py`: `QDoubleSpinBox` による「モーフ上限値」入力欄と `upper_limit` 受け渡し導線を追加。
  - `README.md`: バージョン・機能一覧・未実装一覧を現状実装へ更新。
  - `Specifications_Prompt_v1.md`: モーフ値仕様、GUI仕様、追補（16.8/16.9）を更新。
- Added Files:
  - `tests/test_vmd_writer_peak_value.py`: `peak_value` 優先利用とフォールバックのテストを追加。
  - `tests/test_pipeline_peak_values.py`: `upper_limit` クランプとフォールバックのテストを追加。
- Notes:
  - 16.7 の立ち上がり前ゼロ保証（同一フレーム衝突時 `frame-1` 退避）は維持。
  - GUI は入力窓口のみを追加し、計算ロジックは `core.pipeline` に一元化。
- Verification:
  - `.\.venv\Scripts\python.exe -m unittest discover -s tests` を実行し、`OK (33 tests)` を確認。

---

## Entry 2026-03-19 / Session: processing-trigger-separation-v0350

- Date: 2026-03-19
- Session: processing-trigger-separation-v0350
- Summary:
  - WAV読込直後に重い解析が自動起動しないよう、UI処理起動タイミングを分離。
  - 「処理実行」ボタンを追加し、Whisper/RMS/タイミング更新などのWAV依存処理を押下時に集約。
  - モーフ上限値変更時の即時再解析を停止し、値保持のみへ変更。
  - 未解析状態での出力時は暗黙再解析せず、警告して中断する動作へ整理。
  - README/仕様書へ現状挙動を反映。
- Modified Files:
  - `src/gui/main_window.py`: 処理実行ボタン追加、wav読込時の重処理トリガー停止、上限値変更時の再解析停止、出力時の未解析ガード追加。
  - `README.md`: バージョン `Ver 0.3.3.5` と現行挙動（処理実行導線、未解析出力中断など）を反映。
  - `Specifications_Prompt_v1.md`: 処理概要・GUI仕様・エラー処理・追補に「処理実行」導線と自動実行停止方針を追記。
  - `docs/Version_Control.md`: 本エントリを追記。
- Added Files:
  - なし
- Notes:
  - text読込時のかな化・母音変換の即時処理は維持。
  - wav読込時は基本情報表示と波形表示のみ維持。
- Verification:
  - `.\.venv\Scripts\python.exe -m unittest discover -s tests` を実行し、`OK (33 tests)` を確認。

---

## Entry 2026-03-19 / Session: repo-ops-baseline-setup

- Date: 2026-03-19
- Session: repo-ops-baseline-setup
- Summary:
  - リポジトリ運用面の不足を補うため、プロジェクト定義・除外設定・ビルド手順を追加。
  - Windowsローカル開発で再現しやすい最小運用手順を README に明記。
- Modified Files:
  - `README.md`: セットアップ/実行/テスト/EXEビルド手順と運用ファイル一覧を追記。
  - `docs/Version_Control.md`: 本エントリを追記。
- Added Files:
  - `.gitignore`: 仮想環境、キャッシュ、ビルド成果物、IDE設定の除外を追加。
  - `pyproject.toml`: プロジェクトメタデータ、依存関係、スクリプト、`src` 配下探索設定を追加。
  - `build.ps1`: PyInstaller ビルドを一括実行する PowerShell スクリプトを追加。
  - `MMD_AutoLipTool.spec`: PyInstaller の固定ビルド設定を追加。
- Notes:
  - 既存のアプリ機能ロジック（`src/core` / `src/gui` / `src/vmd_writer`）は変更していない。
- Verification:
  - `.\.venv\Scripts\python.exe -m unittest discover -s tests` を実行し、結果を確認。

---

## Entry 2026-03-19 / Session: docs-sync-before-onedir-build

- Date: 2026-03-19
- Session: docs-sync-before-onedir-build
- Summary:
  - `onedir` 化作業に入る前の現状として、md関連ドキュメントを同期更新。
  - README/仕様書へ「運用整備済みの内容」と「`onedir` 未対応（次タスク）」を明記。
- Modified Files:
  - `README.md`: EXEビルド節に `onedir` 未対応（次タスク予定）の注記を追加。
  - `Specifications_Prompt_v1.md`: 追補 16.11（リポジトリ運用整備）を追加。
  - `docs/Version_Control.md`: 本エントリを追記。
- Added Files:
  - なし
- Notes:
  - 本エントリはドキュメント更新のみを対象とし、アプリ実装コードは変更しない。
- Verification:
  - ドキュメント差分を確認し、mdファイルのみをコミット対象に設定。

---

## Entry 2026-03-19 / Session: onedir-packaging-stage1

- Date: 2026-03-19
- Session: onedir-packaging-stage1
- Summary:
  - PyInstaller spec を `onedir` 前提に再構成し、依存データ/動的ライブラリ/hidden import を明示化。
  - `build.ps1` に `SmokeLaunch`（dist exe起動確認）を追加し、ビルド手順を再現可能化。
  - 第1段階として `dist\MMD_AutoLipTool\` での配布物生成と起動スモーク確認を実施。
- Modified Files:
  - `MMD_AutoLipTool.spec`: `COLLECT` を含む `onedir` 構成へ変更。`whisper/pyopenjtalk/tiktoken` の datas・binaries・hiddenimports を追加。
  - `build.ps1`: `-SmokeLaunch` オプション、出力exe存在チェック、起動スモーク処理を追加。
  - `README.md`: `onedir` ビルド方式、同梱方針、手動確認手順、補助確認手順を追記。
  - `docs/Version_Control.md`: 本エントリを追記。
- Added Files:
  - なし
- Notes:
  - GUI の完全自動操作確認は本環境で未実施。起動確認は自動、処理導線は手動確認手順を明記。
  - ビルドログに `numba` 経由の `tbb12.dll` 警告があるが、ビルド自体は完了し起動スモークは成功。
- Verification:
  - `powershell -ExecutionPolicy Bypass -File .\build.ps1 -Clean -SmokeLaunch` を実行し、`dist\MMD_AutoLipTool\MMD_AutoLipTool.exe` 起動スモーク成功を確認。
  - `.\.venv\Scripts\python.exe` で `generate_vmd_from_text_wav` のE2Eを実行し、`dist\_smoke\smoke_output.vmd` 生成を確認。

---

## Entry 2026-03-19 / Session: repo-current-state-sync-and-full-commit

- Date: 2026-03-19
- Session: repo-current-state-sync-and-full-commit
- Summary:
  - リポジトリ現状（構成/入口/GUI候補/不足候補/最小推奨構成/未実装）を整理し、mdへ反映。
  - `README.md` と `Specifications_Prompt_v1.md` に現状整理を追記。
  - ユーザー指示に基づき、作業ツリー全体をコミット対象として確定。
- Modified Files:
  - `README.md`: 現状整理（6点）セクションを追加。
  - `Specifications_Prompt_v1.md`: 16.12（リポジトリ現状整理）を追記。
  - `docs/Version_Control.md`: 本エントリを追記。
- Added Files:
  - なし（本エントリ時点の追記対象として）
- Notes:
  - 本セッションの反映方針は「実装変更最小・文書更新中心」。
- Verification:
  - `git status --short` で対象差分を確認。
  - 反映後に `git add -A` と `git commit` を実行。

---

## Entry 2026-03-19 / Session: docs-sync-v0336-topmenu-phasea

- Date: 2026-03-19
- Session: docs-sync-v0336-topmenu-phasea
- Summary:
  - これまでの変更（RMS/区間ベースVMD、モーフ上限値、処理実行導線分離、トップメニュー フェーズA 段取り0〜4）を md ドキュメントに統合。
  - ドキュメント上のバージョンを `Ver 0.3.3.6` に同期。
  - 仕様書へトップメニュー導入状況とバージョン同期の追補（16.13/16.14）を追加。
- Modified Files:
  - `README.md`: バージョンを `Ver 0.3.3.6` に更新し、トップメニュー フェーズA（段取り0〜4）と状態整合の要点を追記。
  - `Specifications_Prompt_v1.md`: 16.13（トップメニュー追加・状態整合）と16.14（ドキュメント同期バージョン）を追記。
  - `docs/Version_Control.md`: 本エントリを追記。
- Added Files:
  - なし
- Notes:
  - 本エントリはドキュメント更新のみであり、処理ロジック・解析アルゴリズム・VMD生成仕様の新規実装変更は含まない。
- Verification:
  - `git diff -- README.md docs/Version_Control.md Specifications_Prompt_v1.md` で差分内容を確認。

---

## Entry 2026-03-19 / Session: phaseb-menu-integration-and-help-version

- Date: 2026-03-19
- Session: phaseb-menu-integration-and-help-version
- Summary:
  - フェーズB段取り8/9として、最近使ったTEXT/WAV履歴（各10件）を File メニューへ接続し、複数入口整合を最小修正で完了。
  - Run の `再解析` を処理実行と同一入口へ接続し、View の表示切替（30fps縦線/母音ラベル/イベント区間/初期化）を波形表示内部フラグへ接続。
  - Help のバージョン情報に `pyopenjtalk` / `whisper` の実行環境バージョン表示を追加。
  - README/仕様書/履歴の md を現時点の実装内容へ同期。
- Modified Files:
  - `src/gui/main_window.py`: 履歴機能（保持/更新/再読込）、Run/View 配線、View checked 同期、Help バージョン情報拡張を追加。
  - `src/gui/waveform_view.py`: 表示フラグ（frame grid / vowel labels / event regions）、setter、初期化、状態取得を追加。
  - `README.md`: フェーズB実装（履歴/View/再解析/Help表示）を反映。
  - `Specifications_Prompt_v1.md`: 追補 16.15（フェーズB）/16.16（Help表示拡張）を追加。
  - `docs/Version_Control.md`: 本エントリを追記。
- Added Files:
  - なし
- Notes:
  - 履歴の永続化は未実装（セッション内保持のみ）。
  - 履歴再読込失敗時は該当項目を履歴から削除する方針（方針A）を採用。
- Verification:
  - `.\.venv\Scripts\python.exe -m compileall src/gui/main_window.py src/gui/waveform_view.py` を実行し成功。
  - `.\.venv\Scripts\python.exe -m unittest discover -s tests` を実行し、`OK (33 tests)` を確認。
  - `QT_QPA_PLATFORM=offscreen` で `MainWindow` を起動し、Run/View/履歴の入口整合スモーク確認を実施。

---

## Entry 2026-03-19 / Session: release-v0337-full-repo-commit

- Date: 2026-03-19
- Session: release-v0337-full-repo-commit
- Summary:
  - 現セッションでの実装差分（フェーズBメニュー整合、履歴、View表示切替連動、Help版情報拡張）をリポジトリ全体として確定。
  - ドキュメント同期バージョンと Help 表示版を `Ver 0.3.3.7` へ更新。
  - md 更新だけに限定せず、作業ツリー上の変更を全体コミット対象として確定。
- Modified Files:
  - `src/gui/main_window.py`: Run/View/履歴導線と Help バージョン表示（依存バージョン表示含む）を含む更新を反映。
  - `src/gui/waveform_view.py`: View 表示切替向け内部フラグ・setter・描画分岐を反映。
  - `README.md`: 版数を `Ver 0.3.3.7` に更新し、フェーズB反映内容を同期。
  - `Specifications_Prompt_v1.md`: 16.14 の同期版数を `Ver 0.3.3.7` に更新、16.15/16.16 を維持。
  - `docs/Version_Control.md`: 本エントリを追記。
- Added Files:
  - なし
- Notes:
  - 履歴永続化は未実装（セッション内保持のみ）。
- Verification:
  - `git status --short` で全体差分を確認。
  - `.\.venv\Scripts\python.exe -m unittest discover -s tests` の既存成功結果を維持。

---

## Entry 2026-03-19 / Session: ms4-phase1-to-6-and-docs-sync

- Date: 2026-03-19
- Session: ms4-phase1-to-6-and-docs-sync
- Summary:
  - MS4（実行中状態の可視化）をフェーズ1〜6で実装し、処理中フラグ/処理中ダイアログ/再入防止/操作ロック/状態表示遷移を接続。
  - 処理終了時の復帰整合（成功/失敗共通でダイアログ終了・busy解除・UI復帰）を確認。
  - 現セッション内容を `README.md` / `docs/Specification_Prompt_v2.md` / `docs/repo_milestone.md` に反映。
- Modified Files:
  - `src/gui/main_window.py`: MS4 フェーズ1〜6（状態管理土台、処理中表示、入口接続、操作ロック、状態表示遷移、復帰整合）を実装。
  - `README.md`: 実装済み機能と直近更新に MS4 完了内容を追記。
  - `docs/Specification_Prompt_v2.md`: 6.7 節（実行中状態の可視化）を追加し、残課題から MS4 を削除。
  - `docs/repo_milestone.md`: 進捗メモを追加し、MS4 完了と確認結果要点を記載。
  - `docs/Version_Control.md`: 本エントリを追記。
- Added Files:
  - なし
- Notes:
  - 本エントリ時点で、MS4 以外の新機能拡張（非同期化、進捗率表示、キャンセル）は未対応。
- Verification:
  - `.\.venv\Scripts\python.exe -m py_compile src\gui\main_window.py` を実行し成功。
  - `.\.venv\Scripts\python.exe -m unittest discover -s tests` を実行し、`OK (33 tests)` を確認。

---

## Entry 2026-03-19 / Session: release-v0338-repo-sync

- Date: 2026-03-19
- Session: release-v0338-repo-sync
- Summary:
  - リポジトリ全体の現状を再確認し、反映版を `Ver 0.3.3.8` として同期。
  - 直近実装（MS4 フェーズ1〜6、および関連ドキュメント更新）を含めてコミット対象を確定。
- Modified Files:
  - `README.md`: 版数表記を `Ver 0.3.3.8` に更新。
  - `pyproject.toml`: プロジェクトバージョンを `0.3.3.8` に更新。
  - `src/gui/main_window.py`: Help のバージョン表示を `Ver 0.3.3.8` に更新。
  - `docs/Specification_Prompt_v2.md`: 文書情報に対応リリース `Ver 0.3.3.8` を追記。
  - `docs/repo_milestone.md`: 進捗メモへ `Ver 0.3.3.8` 同期を追記。
  - `docs/Version_Control.md`: 本エントリを追記。
- Added Files:
  - `docs/Specification_Prompt_v2.md`: v2 仕様書をリポジトリ管理対象として追加。
  - `docs/repo_milestone.md`: マイルストーン管理文書をリポジトリ管理対象として追加。
  - `_old/Specifications_Prompt_v1.md`: 旧仕様書を退避先へ移動して管理。
- Notes:
  - 旧配置の `Specifications_Prompt_v1.md` は削除し、`_old/` へ移管。
- Verification:
  - `.\.venv\Scripts\python.exe -m unittest discover -s tests` を実行し、`OK (33 tests)` を確認。

---

## Entry 2026-03-19 / Session: ms7-io-safety-phases2-to-8-and-docs-sync

- Date: 2026-03-19
- Session: ms7-io-safety-phases2-to-8-and-docs-sync
- Summary:
  - MS7（入出力安全性点検）として、TEXT/WAV 読込・VMD 保存・履歴再読込の入口に対する最小防御を実装。
  - 想定外例外時に GUI 警告へフォールバックする復帰経路を補強し、状態不整合の残留リスクを低減。
  - フェーズ7/8として、修正範囲の固定（`main_window.py` 局所）と完了判定観点（TEXT/WAV/保存/履歴/例外）を整理。
  - `README.md` / `docs/repo_milestone.md` / `docs/Specification_Prompt_v2.md` に MS7 の実施結果を反映。
- Modified Files:
  - `src/gui/main_window.py`: MS7 フェーズ2〜6の最小修正（入口パス確認、保存前確認、履歴再読込防御、例外フォールバック）を反映。
  - `README.md`: MS7 実装内容と完了観点を追記。
  - `docs/repo_milestone.md`: MS7 フェーズ1〜8の進捗・方針固定・完了判定観点を追記。
  - `docs/Specification_Prompt_v2.md`: 6.8 節（MS7）を追加し、残課題から MS7 項目を除外。
  - `docs/Version_Control.md`: 本エントリを追記。
- Added Files:
  - なし
- Notes:
  - 本セッションでは `src/app_io/` 導入、履歴永続化、非同期化は対象外。
  - 主要導線（TEXT→WAV→処理実行→出力）は維持。
- Verification:
  - `.\.venv\Scripts\python.exe -m py_compile src\gui\main_window.py` を実行し成功。

---

## Entry 2026-03-19 / Session: release-v0340-repo-sync

- Date: 2026-03-19
- Session: release-v0340-repo-sync
- Summary:
  - リポジトリ現状を再確認し、反映版を `Ver 0.3.4.0` へ同期。
  - MS7（入出力安全性点検）反映済みの状態を、版数とドキュメント表記へ統一。
- Modified Files:
  - `README.md`: 版数表記を `Ver 0.3.4.0` に更新。
  - `pyproject.toml`: プロジェクトバージョンを `0.3.4.0` に更新。
  - `src/gui/main_window.py`: Help のバージョン表示を `Ver 0.3.4.0` に更新。
  - `docs/Specification_Prompt_v2.md`: 文書情報の対応リリースを `Ver 0.3.4.0` に更新。
  - `docs/repo_milestone.md`: 進捗メモのリリース同期版を `Ver 0.3.4.0` に更新。
  - `docs/Version_Control.md`: 本エントリを追記。
- Added Files:
  - なし
- Notes:
  - 主要導線（TEXT→WAV→処理実行→出力）は維持。
  - 本エントリはバージョン同期と反映整理を対象とし、追加機能の導入は行わない。
- Verification:
  - `.\.venv\Scripts\python.exe -m py_compile src\gui\main_window.py` を実行し成功。

---

## Entry 2026-03-20 / Session: ms5-current-dir-memory-phases2-to-9-and-docs-sync

- Date: 2026-03-20
- Session: ms5-current-dir-memory-phases2-to-9-and-docs-sync
- Summary:
  - MS5（読み込み関係のカレントディレクトリ記憶）をフェーズ2〜8で実装し、TEXT/WAV別の保持、通常読込成功時更新、履歴再読込成功時更新、無効値フォールバックを反映。
  - フェーズ9として、確認観点（9-1〜9-5）をコード読解と最小実行確認で整理。
  - `README.md` / `docs/repo_milestone.md` / `docs/Specification_Prompt_v2.md` に本セッション内容を同期。
- Modified Files:
  - `src/gui/main_window.py`: MS5 フェーズ2〜8の局所修正（保持値追加、初期ディレクトリ解決、読込導線接続、成功時更新、履歴再読込連動、無効値フォールバック）を反映。
  - `README.md`: MS5 実装内容と 2026-03-20 の直近更新を追記。
  - `docs/repo_milestone.md`: 進捗メモに MS5 完了（フェーズ1〜9）と確認結果要点を追記。
  - `docs/Specification_Prompt_v2.md`: 6.6 節へ MS5 挙動を追記し、残課題から「読込ダイアログのカレントディレクトリ記憶」を除外。
  - `docs/Version_Control.md`: 本エントリを追記。
- Added Files:
  - なし
- Notes:
  - 永続化（QSettings等）および保存ダイアログ拡張は未対応のまま維持。
  - 変更対象は `src/gui/main_window.py` の局所修正に限定。
- Verification:
  - `.\.venv\Scripts\python.exe -` でモックベース確認スクリプトを実行し、MS5 観点 `9-1..9-5` がすべて `PASS` を確認。
  - `.\.venv\Scripts\python.exe -m unittest discover -s tests` を実行し、`OK (33 tests)` を確認。

---

## Entry 2026-03-20 / Session: ms6-recent-files-phases1-to-9-and-docs-sync

- Date: 2026-03-20
- Session: ms6-recent-files-phases1-to-9-and-docs-sync
- Summary:
  - MS6（最近使ったファイル履歴）をフェーズ1〜8の方針に沿って整理し、TEXT/WAV 履歴の10件上限、重複先頭移動、再読込導線、失敗時除去、更新タイミング整合、非混線を `main_window.py` で確定。
  - フェーズ9として、確認観点（10件上限/重複先頭移動/履歴メニュー再読込/壊れた履歴値の該当除去/非混線）をコード読解と最小スモーク確認で整理。
  - `README.md` / `docs/repo_milestone.md` / `docs/Specification_Prompt_v2.md` に MS6 到達状況を同期。
- Modified Files:
  - `src/gui/main_window.py`: MS6 対応（履歴追加/削除/再読込/メニュー反映/非混線）を局所修正で確定。
  - `README.md`: MS6 の実装済み機能と 2026-03-20 の直近更新を追記。
  - `docs/repo_milestone.md`: 進捗メモに MS6 完了（フェーズ1〜9）と確認結果要点を追記。
  - `docs/Specification_Prompt_v2.md`: 6.6 節へ MS6 の挙動（再構築・再読込導線・失敗時除去・非混線）を追記。
  - `docs/Version_Control.md`: 本エントリを追記。
- Added Files:
  - なし
- Notes:
  - 履歴および表示設定のセッション外永続化（QSettings等）は未対応のまま維持。
  - VMD 保存履歴、`app_io` 分離、大規模リファクタリングは対象外。
- Verification:
  - `.\.venv\Scripts\python.exe -` で MS6 観点の最小スモーク確認を実行し、`MS6 phase9 smoke checks passed` を確認。
  - `.\.venv\Scripts\python.exe -` でメニュー action から `_load_*` 到達確認を実行し、`MS6 phase9 menu->reload route checks passed` を確認。

---

## Entry 2026-03-20 / Session: release-v0341-repo-sync

- Date: 2026-03-20
- Session: release-v0341-repo-sync
- Summary:
  - リポジトリ全体の現状（`src/`, `tests/`, `sample/`, `build/`, `dist/` と主要ドキュメント）を再確認。
  - 反映版を `Ver 0.3.4.1` として同期し、版数表記を統一。
  - 現在の作業ツリー差分をリリースコミットとして確定し、GitHub (`origin/main`) へ同期。
- Modified Files:
  - `README.md`: 版数表記を `Ver 0.3.4.1` に更新。
  - `pyproject.toml`: プロジェクトバージョンを `0.3.4.1` に更新。
  - `src/gui/main_window.py`: Help のバージョン表示を `Ver 0.3.4.1` に更新。
  - `docs/Specification_Prompt_v2.md`: 文書情報の対応リリースを `Ver 0.3.4.1` に更新。
  - `docs/repo_milestone.md`: 進捗メモのリリース同期版を `Ver 0.3.4.1` に更新。
  - `docs/Version_Control.md`: 本エントリを追記。
- Added Files:
  - なし
- Notes:
  - 版数同期は最小変更で実施し、機能仕様の追加実装は行わない。
- Verification:
  - `git status --short` / `git branch --show-current` / `git remote -v` で同期前状態を確認。
  - `git commit` 後、`git push origin main` でリモート同期を実施。

---

## Entry 2026-03-20 / Session: ms6b-autocomplete-counterpart-phases1-to-10-docs-sync

- Date: 2026-03-20
- Session: ms6b-autocomplete-counterpart-phases1-to-10-docs-sync
- Summary:
  - MS6B（同名対応ファイルの自動補完読込）として、主読込成功後に同一フォルダ・同一 stem の相方（`.txt/.wav`）を1回試行する導線を `main_window.py` に反映。
  - 通常読込と履歴再読込の双方で同一補完処理を呼び、反対側既読込ガード・未存在/失敗サイレント・再連鎖なしを確定。
  - 自動補完成功時の履歴反映、読込開始ディレクトリ保持、ready 状態/`current_timing_plan` 整合を既存成功導線の再利用で成立させた。
  - 本フェーズ10として、`docs/repo_milestone.md` / `docs/Specification_Prompt_v2.md` / `docs/Version_Control.md` へ MS6B 仕様を同期。
- Modified Files:
  - `src/gui/main_window.py`: MS6B 実装（相方候補解決、自動補完試行、サイレント失敗、通常/履歴入口接続、履歴/開始ディレクトリ反映）を局所修正で反映。
  - `docs/repo_milestone.md`: MS6B を独立マイルストーンとして追加し、対象/非対象と完了要点を追記。
  - `docs/Specification_Prompt_v2.md`: 6.9 節として MS6B の現行仕様（発動条件、探索条件、サイレント方針、再連鎖防止、成功時反映）を追加。
  - `docs/Version_Control.md`: 本エントリを追記。
- Added Files:
  - なし
- Notes:
  - セッション外永続化の復元時発動は対象外のまま維持。
  - 自動補完専用の通知・確認ダイアログは追加しない方針を維持。
- Verification:
  - フェーズ9 観点（9-1〜9-8）に対して、`src/gui/main_window.py` の条件分岐と呼出し導線をコード読解で確認。
  - `.\.venv\Scripts\python.exe -m py_compile src\gui\main_window.py` を実行し、構文上の整合を確認。

---

## Entry 2026-03-20 / Session: ms8a-gui-foundation-phases1-to-10-docs-sync

- Date: 2026-03-20
- Session: ms8a-gui-foundation-phases1-to-10-docs-sync
- Summary:
  - MS8A（GUI再構成基盤）フェーズ1〜9で反映済みの実装状態を確認し、ドキュメントをコード実体へ同期。
  - `docs/repo_milestone.md` に MS8A 完了（GUI骨格、導線維持、安全動作維持、範囲外未実装）を追記。
  - `docs/MS8A_phase1_ui_partition.md` に実装後の確定状態と MS8B へ渡す固定前提を最小補足。
- Modified Files:
  - `docs/repo_milestone.md`: MS8A をマイルストーン一覧/進捗メモ/GUI整備フェーズへ追記し、完了要点と後続対象を明記。
  - `docs/Version_Control.md`: 本エントリを追記。
  - `docs/MS8A_phase1_ui_partition.md`: 実装後補足（OperationPanel/StatusPanel適用、2カラム配置、責務固定、未実装範囲）を追加。
- Added Files:
  - なし
- Notes:
  - 本フェーズは文書同期のみを実施し、`main_window.py` / `operation_panel.py` / `status_panel.py` / `waveform_view.py` への追加改修は行わない。
  - 状態判定の正本は引き続き `main_window.py`、`OperationPanel` / `StatusPanel` は表示専用を維持。
- Verification:
  - `rg -n "OperationPanel|StatusPanel|preview_placeholder|morph_upper_limit|_update_action_states|_set_output_status" src/gui/main_window.py` で MS8A 到達状態を確認。
  - `rg -n "class OperationPanel|set_button_enabled_states|set_button_states" src/gui/operation_panel.py` と `rg -n "class StatusPanel|set_status_text|status_text" src/gui/status_panel.py` で責務境界を確認。

---

## Entry 2026-03-20 / Session: ms8a-session-docs-full-sync

- Date: 2026-03-20
- Session: ms8a-session-docs-full-sync
- Summary:
  - 本セッションで実施した MS8A（フェーズ1〜10）内容を、md系ドキュメントへ追加同期。
  - `README.md` に MS8A 完了状態（実装済み/未実装）を追記し、GUI骨格の現状を明文化。
  - `docs/Specification_Prompt_v3.md` に実装同期注記を追加し、目標仕様と現時点実装境界を明確化。
- Modified Files:
  - `README.md`: 直近更新（2026-03-20）へ MS8A 完了要点を追記し、未実装項目を現状に合わせて補強。
  - `docs/Specification_Prompt_v3.md`: 「0.1 実装同期注記」を追加し、MS8A実装済み範囲と後続対象を明記。
  - `docs/Version_Control.md`: 本エントリを追記。
- Added Files:
  - なし
- Notes:
  - 本エントリは文書同期のみであり、GUI/処理コードの追加改修は行っていない。
  - `main_window.py` 司令塔責務、`OperationPanel`/`StatusPanel` 表示専用責務の記述を文書間で統一。
- Verification:
  - `rg -n "MS8A|OperationPanel|StatusPanel|未実装" README.md docs/Specification_Prompt_v3.md docs/repo_milestone.md docs/Version_Control.md` で同期記述を確認。

---

## Entry 2026-03-20 / Session: release-v0351-repo-sync

- Date: 2026-03-20
- Session: release-v0351-repo-sync
- Summary:
  - リポジトリ全体の現状を再確認し、反映版を `Ver 0.3.5.1` として同期。
  - 既存作業ツリー差分（MS8A関連のGUI再構成・文書移設/同期を含む）をリポジトリ全体コミット対象として確定。
  - 版数表記を `README` / `pyproject` / GUIバージョン表示 / 主要ドキュメントへ反映。
- Modified Files:
  - `README.md`: 版数表記を `Ver 0.3.5.1` に更新。
  - `pyproject.toml`: プロジェクトバージョンを `0.3.5.1` に更新。
  - `src/gui/main_window.py`: Help のバージョン表示を `Ver 0.3.5.1` に更新。
  - `docs/Specification_Prompt_v2.md`: 対応リリースを `Ver 0.3.5.1` に更新。
  - `docs/repo_milestone.md`: 進捗メモのリリース同期版を `Ver 0.3.5.1` に更新。
  - `docs/Version_Control.md`: 本エントリを追記。
- Added Files:
  - セッション内で追加済みの `docs/` 配下文書群および `src/gui/operation_panel.py` / `src/gui/status_panel.py` を含む作業ツリー差分を対象。
- Notes:
  - 本エントリはリリース同期と全体確定を目的とし、新規機能の先行実装は追加しない。
- Verification:
  - `git status --short` / `git branch --show-current` / `git remote -v` で同期前状態を確認。
  - `rg -n "Ver 0.3.5.1|0.3.5.1" README.md pyproject.toml src/gui/main_window.py docs/Specification_Prompt_v2.md docs/repo_milestone.md` で版数反映を確認。

---

## Entry 2026-03-21 / Session: ms8b-preimplementation-doc-sync

- Date: 2026-03-21
- Session: ms8b-preimplementation-doc-sync
- Summary:
  - MS8B（Preview Area 静止表示導入）について、実装前に固定した仕様・責務分割・境界条件をドキュメントへ同期。
  - `docs/Specification_Prompt_v3.md` に MS8B 実装前固定章を追加し、対象/非対象、中間契約、クリア方針、silent restore 方針、完了条件を明文化。
  - `docs/repo_milestone.md` に MS8B を「実装前固定・未完了」マイルストーンとして追加し、フェーズ1〜9の整理を反映。
- Modified Files:
  - `docs/Specification_Prompt_v3.md`: MS8B 実装前固定仕様（目的、責務、データ契約、クリア/復元方針、対象外、完了条件）を追記。
  - `docs/repo_milestone.md`: マイルストーン一覧へ MS8B を追加し、実装前固定メモとフェーズ分解を追記。
  - `docs/Version_Control.md`: 本エントリを追記。
- Added Files:
  - なし
- Notes:
  - 本エントリはドキュメント同期のみ。`preview_area.py` / `preview_transform.py` は未作成であり、MS8B 実装完了を示すものではない。
  - ソースコード・設定ファイルの変更は行っていない。
- Verification:
  - `rg -n "MS8B|実装前固定|Preview Area|suppress_warning|current_timing_plan.timeline" docs/Specification_Prompt_v3.md docs/repo_milestone.md docs/Version_Control.md` で追記内容を確認。
  - `git diff -- docs/Specification_Prompt_v3.md docs/repo_milestone.md docs/Version_Control.md` で差分が文書のみであることを確認。

---

## Entry 2026-03-21 / Session: ms8b-postimplementation-doc-sync

- Date: 2026-03-21
- Session: ms8b-postimplementation-doc-sync
- Summary:
  - MS8B（Preview Area 静止表示導入）フェーズ1〜9の実装反映に合わせ、md系ドキュメントを実装済み状態へ同期。
  - `current_timing_plan.timeline` 正本、5段固定、クリア/無効化導線、`suppress_warning=True` 復元整合、責務分離の成立を文書へ反映。
  - MS8B 対象外（再生同期・カーソル・Zoom・独立キャッシュ等）が未着手であることを明記。
- Modified Files:
  - `README.md`: 直近更新と未実装一覧を MS8B 実装済み状態へ更新。
  - `docs/repo_milestone.md`: MS8B 行の対象項目を実装済み表現へ更新し、実装完了メモを追記。
  - `docs/Specification_Prompt_v3.md`: 実装同期注記と 14章（MS8B 固定仕様）を実装済み状態へ更新。
  - `docs/MS8B_Implementation_Handoff.md`: 実装反映状況（2026-03-21）を追記し、現状位置を実装完了へ更新。
  - `docs/Version_Control.md`: 本エントリを追記。
- Added Files:
  - なし
- Notes:
  - 本エントリはドキュメント同期のみで、追加機能実装は行わない。
  - MS8C 以降の先回り実装は含まない。
- Verification:
  - `rg -n "MS8B|実装前|実装完了|Preview Area|current_timing_plan.timeline|suppress_warning" README.md docs/MS8B_Implementation_Handoff.md docs/Specification_Prompt_v3.md docs/repo_milestone.md docs/Version_Control.md` で更新箇所を確認。
  - `git diff -- README.md docs/MS8B_Implementation_Handoff.md docs/Specification_Prompt_v3.md docs/repo_milestone.md docs/Version_Control.md` で差分内容を確認。

---

## Entry 2026-03-21 / Session: release-v0352-repo-sync

- Date: 2026-03-21
- Session: release-v0352-repo-sync
- Summary:
  - リポジトリ現状を再確認し、反映版を `Ver 0.3.5.2` として同期。
  - MS8B（Preview Area 静止表示導入）を含む現作業ツリー差分をリポジトリ全体コミット対象として確定。
  - 版数表記を `README.md` / `pyproject.toml` / `src/gui/main_window.py` / `docs/Specification_Prompt_v3.md` / `docs/repo_milestone.md` に反映。
- Modified Files:
  - `README.md`: 版数表記を `Ver 0.3.5.2` に更新。
  - `pyproject.toml`: プロジェクトバージョンを `0.3.5.2` に更新。
  - `src/gui/main_window.py`: Help のバージョン表示を `Ver 0.3.5.2` に更新。
  - `docs/Specification_Prompt_v3.md`: 対応リリースを `Ver 0.3.5.2` に更新。
  - `docs/repo_milestone.md`: 進捗メモへ `Ver 0.3.5.2` のリリース同期追記。
  - `docs/Version_Control.md`: 本エントリを追記。
- Added Files:
  - なし
- Notes:
  - 本エントリはリリース同期と全体確定を目的とし、新規機能の先行実装は追加しない。
- Verification:
  - `git status --short` / `git branch --show-current` / `git remote -v` で同期前状態を確認。
  - `rg -n "Ver 0.3.5.2|0.3.5.2" README.md pyproject.toml src/gui/main_window.py docs/Specification_Prompt_v3.md docs/repo_milestone.md` で版数反映を確認。

## Entry 2026-03-21 / Session: release-v0353-repo-sync

- Date: 2026-03-21
- Session: release-v0353-repo-sync
- Summary:
  - Current repository state was re-checked and synchronized as `Ver 0.3.5.3`.
  - MS8C implementation files and related documentation updates were included in the same repository sync commit.
  - Version markers were updated consistently for the current release.
- Modified Files:
  - `README.md`: version label updated to `Ver 0.3.5.3`.
  - `pyproject.toml`: project version updated to `0.3.5.3`.
  - `src/gui/main_window.py`: Help version text updated to `Ver 0.3.5.3`.
  - `docs/Specification_Prompt_v3.md`: target release updated to `Ver 0.3.5.3`.
  - `docs/repo_milestone.md`: repository sync release line updated to `Ver 0.3.5.3`.
  - `docs/Version_Control.md`: this release entry added.
- Added Files:
  - `docs/MS8C_Implementation_Handoff.md`
  - `src/gui/playback_controller.py`
  - `src/gui/view_sync.py`
- Notes:
  - This entry is a repository sync entry; feature-level implementation details remain in each MS8C session entry.
- Verification:
  - `git status --short` / `git branch --show-current` / `git remote -v` used for sync pre-check.
  - `rg -n "Ver 0.3.5.3|0.3.5.3" README.md pyproject.toml src/gui/main_window.py docs/Specification_Prompt_v3.md docs/repo_milestone.md` used for version marker check.
---

## Entry 2026-03-22 / Session: ms8d2-cross-doc-sync-and-consistency-pass

- Date: 2026-03-22
- Session: ms8d2-cross-doc-sync-and-consistency-pass
- Summary:
  - MS8D-2 実装完了状態を前提に、md 系ドキュメントを横断更新して整合を取った。
  - `README.md` / `docs/repo_milestone.md` / `docs/Specification_Prompt_v3.md` の記述を、共有ビューポート・Zoom/Pan・フレーム目盛り・パス中間省略+tooltip の実装済み状態へ同期した。
  - 旧来の `MS8D` 記述を改訂版 `MS8D-2` 基準へ更新し、次段階（MS8E）へ進む前提の文書矛盾を解消した。
- Modified Files:
  - `README.md`: 現在の主な機能へ MS8D-2 実装項目を追記。直近更新（2026-03-22 / MS8D-2）を追加。未対応一覧から Zoom を除外。
  - `docs/repo_milestone.md`: マイルストーン表の `MS8D` 行を `MS8D-2` 行へ更新。推奨実装順とフェーズ分類を現状へ同期。MS8D-2 完了メモを追記。
  - `docs/Specification_Prompt_v3.md`: 実装同期注記を MS8D-2 完了反映へ更新。`view_sync` / パス表示 / 残課題の記述を現状実装へ同期。
  - `docs/Version_Control.md`: 本エントリを追記。
- Added Files:
  - なし
- Notes:
  - 本エントリはドキュメント更新のみで、ソースコード実装は変更しない。
  - ユーザー依頼文中の `MS8B-2` 表記は、既存文書系の改訂段階 `MS8D-2` を指す前提で整合を実施。
- Verification:
  - `rg -n "MS8D-2|MS8D |Zoom|Pan|可視範囲|中間省略|tooltip" README.md docs/repo_milestone.md docs/Specification_Prompt_v3.md`
  - `git diff -- README.md docs/repo_milestone.md docs/Specification_Prompt_v3.md docs/Version_Control.md`
---

## Entry 2026-03-22 / Session: release-v0354-repo-sync

- Date: 2026-03-22
- Session: release-v0354-repo-sync
- Summary:
  - リポジトリ現状を再確認し、反映版を `Ver 0.3.5.4` として同期。
  - MS8D-2 実装反映済みの作業ツリー（GUI 実装 + 文書同期）を、同一リリースとして確定対象に整理。
  - 版数表記を `README.md` / `pyproject.toml` / `src/gui/main_window.py` / `docs/Specification_Prompt_v3.md` / `docs/repo_milestone.md` に反映。
- Modified Files:
  - `README.md`: 版数表記を `Ver 0.3.5.4` に更新。
  - `pyproject.toml`: プロジェクトバージョンを `0.3.5.4` に更新。
  - `src/gui/main_window.py`: Help のバージョン表示を `Ver 0.3.5.4` に更新。
  - `docs/Specification_Prompt_v3.md`: 対応リリースを `Ver 0.3.5.4` に更新。
  - `docs/repo_milestone.md`: 進捗メモへ `Ver 0.3.5.4` のリリース同期追記。
  - `docs/Version_Control.md`: 本エントリを追記。
- Added Files:
  - `docs/MS8D-2_Requirements_and_Spec_Update.md`
- Notes:
  - 本エントリはリリース同期と現作業ツリー確定を目的とし、MS8E の先行実装は含まない。
- Verification:
  - `git status --short` / `git branch --show-current` / `git remote -v`
  - `rg -n "Ver 0.3.5.4|0.3.5.4" README.md pyproject.toml src/gui/main_window.py docs/Specification_Prompt_v3.md docs/repo_milestone.md`
  - `.\.venv\Scripts\python.exe -m py_compile src\gui\main_window.py src\gui\view_sync.py src\gui\waveform_view.py src\gui\preview_area.py src\gui\operation_panel.py src\gui\playback_controller.py src\gui\preview_transform.py`
---
## Entry 2026-03-22 / Session: ms9-post-implementation-doc-sync-and-ms9-2-handoff

- Date: 2026-03-22
- Session: ms9-post-implementation-doc-sync-and-ms9-2-handoff
- Summary:
  - MS9 本体実装、および MS9 追加改修として導入した右表示領域共通の横スクロールバー実装後の到達状態を、主要ドキュメントへ同期。
  - 文書上で、MS9 本体完了、右表示領域共通 scrollbar の実装済み範囲、関連不具合修正（PreviewArea 末尾伸び補正 / PreviewArea mousePressEvent 型整合 / 端部クランプ時体感改善）を明文化。
  - 次セッションでは見た目調整や最終 UX 微修正を `MS9-2` として扱う方針を README / milestone / specification に明示。
- Modified Files:
  - `README.md`: MS9 実装済み内容、右表示領域共通 scrollbar 追加改修、次セッション `MS9-2` 予定を追記。
  - `docs/repo_milestone.md`: MS9 完了状態、scrollbar 追加改修の到達点、`MS9-2` の位置づけを追記。
  - `docs/Specification_Prompt_v3.md`: MS9 実装反映済み事項、scrollbar 追加改修の扱い、`MS9-2` の範囲を追記。
  - `docs/Version_Control.md`: 本エントリを追記。
- Added Files:
  - なし
- Notes:
  - 本エントリは文書整備のみであり、コードファイルの追加修正は含まない。
  - バージョン番号は引き続き `Ver 0.3.5.4` を維持し、今回はリリース同期ではなく実装到達状態の整理に留める。
- Verification:
  - `git diff -- README.md docs/repo_milestone.md docs/Specification_Prompt_v3.md docs/Version_Control.md`
  - 文書更新のみであることを確認。
---
## Entry 2026-03-22 / Session: release-v0355-local-checkpoint

- Date: 2026-03-22
- Session: release-v0355-local-checkpoint
- Summary:
  - ここまでの MS9 本体、MS9 追加改修（右表示領域共通横スクロールバー）、関連不具合修正、および文書整備までをローカル区切りとして `Ver 0.3.5.5` に同期。
  - GitHub 側への push は行わず、ローカルコミット用の版数同期に留める。
- Modified Files:
  - `README.md`: 版数表記を `Ver 0.3.5.5` に更新。
  - `pyproject.toml`: プロジェクトバージョンを `0.3.5.5` に更新。
  - `src/gui/i18n_strings.py`: バージョン情報ダイアログのアプリ版数表記を `Ver 0.3.5.5` に更新。
  - `docs/Specification_Prompt_v3.md`: 対応リリースを `Ver 0.3.5.5` に更新。
  - `docs/repo_milestone.md`: リポジトリ全体の反映版表記を `Ver 0.3.5.5` に更新。
  - `docs/Version_Control.md`: 本エントリを追記。
- Added Files:
  - なし
- Notes:
  - 本エントリはローカルチェックポイント作成のための版数同期であり、GitHub 側の同期は含まない。
- Verification:
  - `rg -n "Ver 0.3.5.5|0.3.5.5" README.md pyproject.toml src/gui/i18n_strings.py docs/Specification_Prompt_v3.md docs/repo_milestone.md`
---

## Entry 2026-03-23 / Session: app-icon-and-splash-screen

- Date: 2026-03-23
- Session: app-icon-and-splash-screen
- Summary:
  - アプリケーションアイコン（GUIおよびEXE本体）を設定した。
  - アプリ起動時のスプラッシュスクリーン表示処理（QSplashScreen）を追加した。
  - PyInstaller環境とローカル開発環境の両方でリソースパスを安全に解決する仕組みを導入した。
- Modified Files:
  - `src/main.py`: パス解決処理、アプリアイコン適用（タスクバーID宣言含む）、スプラッシュスクリーン表示処理を追加。
  - `MMD_AutoLipTool.spec`: EXEファイルへのアイコン設定、アセット画像の同梱指定を追加。
  - `docs/Version_Control.md`: 本エントリを追記。
  - `docs/Specification_Prompt_v3.md`: アイコンとスプラッシュに関する仕様を追記。
- Added Files:
  - なし
- Notes:
  - アセット画像（`assets/icons/MMD_AutoLipTool.ico`, `assets/MMD_AutoLipTool_splash.png`）の存在を前提とする。
- Verification:
  - ローカル実行およびビルド後のEXE起動にて、タスクバー・タイトルバーのアイコンとスプラッシュの表示を確認。
