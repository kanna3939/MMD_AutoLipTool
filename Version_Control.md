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
  - `README.md`: バージョン `Ver 0.3.5.0` と現行挙動（処理実行導線、未解析出力中断など）を反映。
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
