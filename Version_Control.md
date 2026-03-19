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

