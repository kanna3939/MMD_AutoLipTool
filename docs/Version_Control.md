# Version Control Log

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
  - `Version_Control.md`: 本エントリを追記。
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
  - `Version_Control.md`: 本エントリを追記。
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
  - `Version_Control.md`: 本エントリを追記。
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
  - `Version_Control.md`: 本エントリを追記。
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
  - `Version_Control.md`: 本エントリを追記。
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
  - `Version_Control.md`: 本エントリを追記。
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
  - `Version_Control.md`: 本エントリを追記。
- Added Files:
  - なし
- Notes:
  - 本エントリはドキュメント更新のみであり、処理ロジック・解析アルゴリズム・VMD生成仕様の新規実装変更は含まない。
- Verification:
  - `git diff -- README.md Version_Control.md Specifications_Prompt_v1.md` で差分内容を確認。

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
  - `Version_Control.md`: 本エントリを追記。
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
  - `Version_Control.md`: 本エントリを追記。
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
  - 現セッション内容を `README.md` / `Specification_Prompt_v2.md` / `repo_milestone.md` に反映。
- Modified Files:
  - `src/gui/main_window.py`: MS4 フェーズ1〜6（状態管理土台、処理中表示、入口接続、操作ロック、状態表示遷移、復帰整合）を実装。
  - `README.md`: 実装済み機能と直近更新に MS4 完了内容を追記。
  - `Specification_Prompt_v2.md`: 6.7 節（実行中状態の可視化）を追加し、残課題から MS4 を削除。
  - `repo_milestone.md`: 進捗メモを追加し、MS4 完了と確認結果要点を記載。
  - `Version_Control.md`: 本エントリを追記。
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
  - `Specification_Prompt_v2.md`: 文書情報に対応リリース `Ver 0.3.3.8` を追記。
  - `repo_milestone.md`: 進捗メモへ `Ver 0.3.3.8` 同期を追記。
  - `Version_Control.md`: 本エントリを追記。
- Added Files:
  - `Specification_Prompt_v2.md`: v2 仕様書をリポジトリ管理対象として追加。
  - `repo_milestone.md`: マイルストーン管理文書をリポジトリ管理対象として追加。
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
  - `README.md` / `repo_milestone.md` / `Specification_Prompt_v2.md` に MS7 の実施結果を反映。
- Modified Files:
  - `src/gui/main_window.py`: MS7 フェーズ2〜6の最小修正（入口パス確認、保存前確認、履歴再読込防御、例外フォールバック）を反映。
  - `README.md`: MS7 実装内容と完了観点を追記。
  - `repo_milestone.md`: MS7 フェーズ1〜8の進捗・方針固定・完了判定観点を追記。
  - `Specification_Prompt_v2.md`: 6.8 節（MS7）を追加し、残課題から MS7 項目を除外。
  - `Version_Control.md`: 本エントリを追記。
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
  - `Specification_Prompt_v2.md`: 文書情報の対応リリースを `Ver 0.3.4.0` に更新。
  - `repo_milestone.md`: 進捗メモのリリース同期版を `Ver 0.3.4.0` に更新。
  - `Version_Control.md`: 本エントリを追記。
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
  - `README.md` / `repo_milestone.md` / `Specification_Prompt_v2.md` に本セッション内容を同期。
- Modified Files:
  - `src/gui/main_window.py`: MS5 フェーズ2〜8の局所修正（保持値追加、初期ディレクトリ解決、読込導線接続、成功時更新、履歴再読込連動、無効値フォールバック）を反映。
  - `README.md`: MS5 実装内容と 2026-03-20 の直近更新を追記。
  - `repo_milestone.md`: 進捗メモに MS5 完了（フェーズ1〜9）と確認結果要点を追記。
  - `Specification_Prompt_v2.md`: 6.6 節へ MS5 挙動を追記し、残課題から「読込ダイアログのカレントディレクトリ記憶」を除外。
  - `Version_Control.md`: 本エントリを追記。
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
  - `README.md` / `repo_milestone.md` / `Specification_Prompt_v2.md` に MS6 到達状況を同期。
- Modified Files:
  - `src/gui/main_window.py`: MS6 対応（履歴追加/削除/再読込/メニュー反映/非混線）を局所修正で確定。
  - `README.md`: MS6 の実装済み機能と 2026-03-20 の直近更新を追記。
  - `repo_milestone.md`: 進捗メモに MS6 完了（フェーズ1〜9）と確認結果要点を追記。
  - `Specification_Prompt_v2.md`: 6.6 節へ MS6 の挙動（再構築・再読込導線・失敗時除去・非混線）を追記。
  - `Version_Control.md`: 本エントリを追記。
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
  - `Specification_Prompt_v2.md`: 文書情報の対応リリースを `Ver 0.3.4.1` に更新。
  - `repo_milestone.md`: 進捗メモのリリース同期版を `Ver 0.3.4.1` に更新。
  - `Version_Control.md`: 本エントリを追記。
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
  - 本フェーズ10として、`repo_milestone.md` / `Specification_Prompt_v2.md` / `Version_Control.md` へ MS6B 仕様を同期。
- Modified Files:
  - `src/gui/main_window.py`: MS6B 実装（相方候補解決、自動補完試行、サイレント失敗、通常/履歴入口接続、履歴/開始ディレクトリ反映）を局所修正で反映。
  - `repo_milestone.md`: MS6B を独立マイルストーンとして追加し、対象/非対象と完了要点を追記。
  - `Specification_Prompt_v2.md`: 6.9 節として MS6B の現行仕様（発動条件、探索条件、サイレント方針、再連鎖防止、成功時反映）を追加。
  - `Version_Control.md`: 本エントリを追記。
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
  - `repo_milestone.md` に MS8A 完了（GUI骨格、導線維持、安全動作維持、範囲外未実装）を追記。
  - `docs/MS8A_phase1_ui_partition.md` に実装後の確定状態と MS8B へ渡す固定前提を最小補足。
- Modified Files:
  - `repo_milestone.md`: MS8A をマイルストーン一覧/進捗メモ/GUI整備フェーズへ追記し、完了要点と後続対象を明記。
  - `Version_Control.md`: 本エントリを追記。
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

