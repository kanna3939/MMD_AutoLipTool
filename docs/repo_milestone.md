# MMD_AutoLipTool GUI整備・機能拡張 マイルストーン一覧
## 2026-04-09 / MS13-B2 メインフレーム最小骨格作成 メモ

- 対象: MS13-B2
- 実装反映:
  - wxPython のメインフレーム内にルートパネルを追加した。
  - ルートパネル内を縦の `wx.BoxSizer` によって、「上部操作域」「中央主領域」「下部ステータス域」の3パネルへと分割した。
  - 各領域には簡素な `wx.StaticText` をプレースホルダとして配置し、`wx.BORDER_SIMPLE` で境界を可視化した。
- 確認状態:
  - 起動時にエラーなく3領域が描画されることを確認した。
  - 余計な細分化や `wx.SplitterWindow`、`wx.StatusBar` の導入は行っていない。
- 現在地:
  - MS13-B2 の完了条件である「メインフレーム内を3領域へ分割し骨格を作る」ことが成立した。
  - 次段は B3 にて、この骨格に具体的なメニューやボタン等の最小UI要素を配置していく状態。

---

## 2026-04-09 / MS13-B1 移行前提固定とwx起動入口作成 メモ

- 対象: MS13-B1
- 実装反映:
  - `src/main.py` を旧Qt主系から、wxPythonアプリを初期化・起動するだけのwx主系の起動入口へ直接差し替えた。
  - 新主系パッケージとして `src/gui_wx/` を新設し、アプリ初期化を担う `app.py` と最小の空フレームを担う `main_frame.py` を追加した。
  - 旧Qt系コード（`src/gui/`）のディレクトリ削除は行わず、今後の改修対象外とする凍結領域として分離構造を明確にした。
- 確認状態:
  - `python src/main.py` にて、エラーやクラッシュなく空のwxメインフレームが表示されることを確認済み。
  - 閉じる操作での正常終了、Qt系との二重主系化の排除が確認できている。
- 現在地:
  - MS13-B1 の完了条件である「wx アプリが起動する」「最小 frame が表示される」「qt主系からの分離」が成立した。
  - 次段は B2 にて、この空フレーム上にメインフレームのレイアウトを構築していく状態。

---

## 2026-04-02 / Ver 0.3.8.0 / MS12 packaging sync メモ

- 対象: Ver 0.3.8.0 同期
- 同期内容:
  - `README.md` / `pyproject.toml` / `docs/Specification_Prompt_v3.md` / `docs/MS12_Implementation_Roadmap.md` / `docs/MS11_MS12_Roadmap_and_Scope_Split.md` / `docs/MS11-10_Implementation_Plan.md` / `docs/MS12-4_Implementation_Plan.md` を `Ver 0.3.8.0` 基準へ更新
  - MS12-5 の build / packaging / license 文書整備を、`Ver 0.3.8.0` の repository-facing current state として整理
  - 手動配置された `FFmpeg\bin\` の実バイナリを、release build 入力としてコミット対象へ含める前提を確認
- 現在地:
  - 現在版の正本は `pyproject.toml` の `0.3.8.0`
  - splash / Help / README / 主要仕様文書は `Ver 0.3.8.0` 前提へ同期済み
  - 次段は、この状態をコミットし GitHub main と同期する

---

## 2026-04-02 / MS12-5 実装メモ

- 対象: MS12-5
- 実装反映:
  - `.gitignore` に `FFmpeg\bin\` 手動配置用の ignore ルールを追加し、`.gitkeep` のみを repo 管理対象にした
  - `build.ps1` に、公式配布ビルド `FFmpeg v8.1` の `bin` 手動配置前提チェックを追加し、`ffmpeg.exe` / `ffprobe.exe` 不在時は build 前に停止するようにした
  - `MMD_AutoLipTool.spec` に、`LICENSE` / `NOTICE` / `THIRD_PARTY_LICENSES.md` の同梱と、`FFmpeg\bin\` 配下バイナリの `FFmpeg\` への bundling を追加した
  - `README.md` / `NOTICE` / `THIRD_PARTY_LICENSES.md` / `docs/MS12_Implementation_Roadmap.md` / `docs/MS11_MS12_Roadmap_and_Scope_Split.md` / `docs/Specification_Prompt_v3.md` を、公式配布ビルド `FFmpeg v8.1`・手動配置・`bin` のみ・`onedir` 前提へ同期した
- 確認状態:
  - `MMD_AutoLipTool.spec` は `.gitkeep` を bundling 対象から除外する形で整合済み
  - 実コード上には現時点で FFmpeg 直接呼出し経路は無く、今回の主責務は build / release 契約の固定であることを確認済み
  - 実 build は、実バイナリ未配置のためこの時点では未実施
- 現在地:
  - MS12-5 の最小契約である onedir 配布前提の FFmpeg bundling 方針固定と release-side documentation 同期が repo 上に反映された
  - 次段は、実バイナリを配置した上での build 実施と実機確認になる

---

## 2026-04-02 / MS12-5 実装 plan 整理メモ

- 対象: MS12-5
- 追加文書:
  - `docs/MS12-5_Implementation_Plan.md` を追加
- 整理内容:
  - distribution dependency bundling cleanup について、対象 / 非対象 / build / spec / docs 同期方針 / 保留課題を単独文書化
  - 現行 build には FFmpeg bundling が無いこと、採用時は取得元・同梱対象・license 案内をセットで定義すべきことを整理
  - MS12-5 は FFmpeg 採用可否で実装内容が大きく変わることを明記
- 現在地:
  - MS12-5 実装前の論点分解はできた
  - FFmpeg bundling を採用して進める方針を確定
  - 配置方法は手動配置で確定
  - 手動配置先は exe ルート下 `FFmpeg`、配布物単位は `bin` のみ、版数記録は関連ドキュメント全てへ反映する方針を確定

---

## 2026-04-02 / MS12-4 実装メモ

- 対象: MS12-4
- 実装反映:
  - `src/app_version.py` を追加し、app version / installed version の共通解決 helper を導入した
  - `src/main.py` で splash pixmap に `Ver. x.y.z` 形式の version 文字列を重ねる導線を追加した
  - `src/gui/main_window.py` の Help version 表示を共通 helper 参照へ切り替えた
  - `tests/test_app_version.py`、`tests/test_main_startup_splash.py`、`tests/test_main_window_version_info.py` で version source と splash 表示の最小回帰を追加した
- 確認状態:
  - `tests/test_app_version.py tests/test_main_startup_splash.py tests/test_main_window_version_info.py tests/test_main_window_processing_responsiveness.py` は通過
- 現在地:
  - MS12-4 の最小契約である splash version display が実装済みになった
  - 次段は MS12-5 の packaging 系整理へ進める状態

---

## 2026-04-02 / MS12-4 実装 plan 整理メモ

- 対象: MS12-4
- 追加文書:
  - `docs/MS12-4_Implementation_Plan.md` を追加
- 整理内容:
  - splash version display について、対象 / 非対象 / version source 単一化 / splash 描画方針 / テスト方針 / 保留課題を単独文書化
  - app version source を helper へ 1 本化し、splash と Help が同じ version を参照する方針を固定
  - 表記形式と表示位置のような見た目判断は保留課題として分離
- 現在地:
  - MS12-4 実装に必要な責務境界と論点分解ができた
  - まだコード実装・テスト追加には入っていない
  - 追加方針として、表記は `Ver. x.y.z`、位置はロゴ下の中央下寄り空白帯に固定した

---

## 2026-04-02 / MS12-3 実装メモ

- 対象: MS12-3
- 実装反映:
  - `src/main.py` に splash の生成・表示・finish を扱う最小 helper を追加した
  - splash 表示開始時刻を保持し、起動が速い環境でも短時間は表示されるよう最小表示時間付きの finish 予約を追加した
  - `tests/test_main_startup_splash.py` を追加し、splash 表示、missing asset fallback、finish 予約を固定した
- 確認状態:
  - `tests/test_main_startup_splash.py tests/test_main_window_processing_responsiveness.py tests/test_main_window_vmd_output_dir.py` は通過
- 現在地:
  - MS12-3 の最小契約である splash timing improvement が実装済みになった
  - 次段は MS12-4 の splash version display へ進める状態

---

## 2026-04-02 / MS12-3 実装 plan 整理メモ

- 対象: MS12-3
- 追加文書:
  - `docs/MS12-3_Implementation_Plan.md` を追加
- 整理内容:
  - splash timing improvement について、対象 / 非対象 / 壊さない前提 / 起動順整理 / finish タイミング / テスト方針 / 保留課題を単独文書化
  - `QApplication` 作成後のできるだけ早い段階で splash を表示し、settings load と `MainWindow` 構築待ちを splash 中に吸収する方針を固定
  - finish 遅延や最小表示時間のような見た目判断は保留課題として分離
- 現在地:
  - MS12-3 実装に必要な起動導線の整理と論点分解ができた
  - まだコード実装・テスト追加には入っていない
  - 追加方針として、起動が速い環境でも splash を一瞬だけでも表示させる方向を採る

---

## 2026-04-02 / MS12-2 実装メモ

- 対象: MS12-2
- 実装反映:
  - `src/gui/main_window.py` に `QThread + QObject worker` ベースの最小 processing worker 導線を追加した
  - `build_vowel_timing_plan(...)` の実行を worker 側へ切り出し、timing plan 反映・waveform / preview / status 更新は UI 側へ残した
  - `tests/test_main_window_processing_responsiveness.py` を追加し、処理開始時の busy state、成功時の UI 反映、失敗時の warning / 復帰を固定した
- 確認状態:
  - `tests/test_main_window_processing_responsiveness.py tests/test_main_window_vmd_output_dir.py tests/test_main_window_closing_softness.py` は通過
- 現在地:
  - MS12-2 の最小契約である processing-time responsiveness improvement が実装済みになった
  - 次段は MS12-3 の splash timing improvement へ進める状態

---

## 2026-04-02 / MS12-2 実装 plan 整理メモ

- 対象: MS12-2
- 追加文書:
  - `docs/MS12-2_Implementation_Plan.md` を追加
- 整理内容:
  - processing-time UI responsiveness improvement について、対象 / 非対象 / 壊さない前提 / worker 境界 / 想定実装ステップ / テスト方針 / 保留課題を単独文書化
  - `build_vowel_timing_plan(...)` の同期実行を worker 側へ寄せ、timing plan 反映・waveform / preview / status 更新は UI 側へ残す方針を固定
  - 未確定事項は問い合わせず、worker 形式、payload 形、dialog modality などを保留課題として明記
- 現在地:
  - MS12-2 に入る前提となる責務境界が整理され、実装着手可能な状態になった
  - まだコード実装・テスト追加には入っていない

---

## 2026-04-02 / MS12-1 実装メモ

- 対象: MS12-1
- 実装反映:
  - `src/gui/settings_store.py` に `last_vmd_output_dir` を追加し、settings の save / load / normalize 対象へ組み込んだ
  - `src/gui/main_window.py` で VMD 保存ダイアログの初期フォルダに remembered dir を使い、保存成功時のみ親フォルダを更新するようにした
  - `tests/test_settings_store.py` と `tests/test_main_window_vmd_output_dir.py` に round-trip / success / cancel / failure の最小回帰を追加した
- 確認状態:
  - `tests/test_settings_store.py tests/test_main_window_vmd_output_dir.py` は通過
- 現在地:
  - VMD 保存先フォルダの記憶と永続化が、MS12-1 の最小契約として実装済みになった
  - 次段は MS12-2 の responsiveness 改修へ進める状態

---

## 2026-04-02 / MS12-1 実装 plan 整理メモ

- 対象: MS12-1
- 追加文書:
  - `docs/MS12-1_Implementation_Plan.md` を追加
- 整理内容:
  - VMD 保存先フォルダの記憶と永続化について、対象 / 非対象 / 壊さない前提 / 想定実装ステップ / テスト方針 / 保留課題を単独文書化
  - 保存成功時のみ記憶更新し、次回 save dialog 初期フォルダと再起動後復元へつなぐ方針を固定
  - 未確定事項は問い合わせず、settings key 配置、保存タイミング、invalid dir 扱いなどを保留課題として明記
- 現在地:
  - MS12 の親ロードマップに続き、MS12-1 単体で着手できる plan が揃った
  - まだ実装・テスト追加には入っていない

---

## 2026-04-02 / MS12 要件整理メモ

- 対象: MS12 roadmap / 仕様整理
- 追加方針:
  - MS12 の最初の着手候補として、`VMD保存先フォルダの記憶と永続化` を追加
  - 既存の processing responsiveness は 1 段後ろへ送り、順序を `保存先記憶 -> responsiveness -> splash timing -> splash version -> packaging` とする
- 現在地:
  - 現行コードには TEXT / WAV 読込用の直前ディレクトリ保持はある
  - ただし、VMD 保存先フォルダを設定保存して次回起動へ復元する契約は未導入
  - このため、MS12 の最初の自然単位として GUI 利便性と settings 永続化境界の整理対象に追加する

---

## 2026-04-02 / MS12 実装ロードマップ整理メモ

- 対象: MS12 全体
- 追加文書:
  - `docs/MS12_Implementation_Roadmap.md` を追加
- 整理内容:
  - MS12 を `保存先記憶 -> responsiveness -> splash timing -> splash version -> packaging` の 5 段に固定
  - 各段の主対象ファイル、非対象、完了条件、リスクを整理
  - 現時点では問い合わせず、未確定事項とユーザー判断項目を保留課題として文書化
- 現在地:
  - MS12 着手前の親ロードマップができ、次段の個別 plan を切る入口が整った
  - 最初の自然な最小単位は引き続き MS12-1 とする

---

## 2026-04-02 / MS11-9FIX7 closing smoothing 契約整理メモ

- 対象: MS11-9FIX7
- 実装反映:
  - `src/vmd_writer/writer.py` の closing smoothing を、family ごとの tail 再構成から
    **元の end-zero 以降へ hold / softness を追加する共通 tail post-process** へ整理
  - `src/gui/preview_transform.py` を writer の post-process 結果に追随させ、
    Preview 独自補正を増やさない方針を維持
  - `tests/test_vmd_writer_intervals.py` / `tests/test_preview_transform.py` を、
    「元 tail を短縮しない」契約ベースへ更新
- 確認状態:
  - `tests/test_vmd_writer_intervals.py tests/test_preview_transform.py tests/test_pipeline_and_vmd.py tests/test_main_window_closing_softness.py`
    が `78 passed`
  - `Test11_9S1.vmd` / `Test11_9S2.vmd` / `Test11_9S3.vmd` / `Test11_9S4.vmd` の比較で、
    `開口維持` / `閉口スムーズ` は短縮ではなく末尾追加として出ている
- 現在地:
  - FIX7 により、旧不具合だった「全音の後半スロープが一律 1 フレーム短くなる」挙動は
    実出力 VMD 差分上では確認されなくなった
  - 今後の主題は不具合修正よりも、closing smoothing の効き方の自然さ確認へ移る

---

## 2026-04-02 / Ver 0.3.7.1 / MS11-10 closeout sync メモ

- 対象: MS11-10 相当の総まとめ文書整備
- 同期内容:
  - `README.md` / `pyproject.toml` / `docs/Specification_Prompt_v3.md` / `docs/MS11_MS12_Roadmap_and_Scope_Split.md` / `docs/repo_milestone.md` / `docs/Version_Control.md` を `Ver 0.3.7.1` 基準へ同期
  - `docs/MS11-10_Implementation_Plan.md` を、MS11 全体の closeout と MS11-9FIX7 まで反映済みの現在地が読める文書へ更新
  - MS11-9 系の横断文書群と `MS11-10` の記述を、same-vowel 微調整 / observation 契約整理 / closing smoothing 自然さ確認という残テーマへ揃えた
- 現在地:
  - 反映版を `Ver 0.3.7.1` としてコミット前同期可能な状態まで整備
  - MS11 系は FIX7 までを含めて closeout 状態を文書上で追跡可能
  - MS12 は引き続き GUI responsiveness / splash / packaging 系の別ラインとして維持

---

## 2026-04-02 / Ver 0.3.7.0 / MS11-10 文書同期メモ

- 対象: MS11-10 相当の最終文書整備
- 同期内容:
  - `README.md` / `pyproject.toml` / `docs/Specification_Prompt_v3.md` / `docs/MS11_MS12_Roadmap_and_Scope_Split.md` / `docs/repo_milestone.md` / `docs/Version_Control.md` を `Ver 0.3.7.0` 基準へ同期
  - `docs/MS11-10_Implementation_Plan.md` を追加し、MS11 final consistency sync の目的・対象・完了条件を固定
  - `docs/MS11-9_Summary_and_Handoff.md` を MS11-9 系の横断入口として採用し、same-vowel / cross-vowel / top-end shaping の現在地を参照しやすく整理
  - MS11-9G は MMD 側確認込みで一旦クローズ扱いとし、MS11 側の主残テーマを same-vowel 微調整と observation 契約整理へ絞った
- 現在地:
  - 反映版を `Ver 0.3.7.0` としてコミット前同期可能な状態まで整備
  - MS11-9 系の個別計画書は保持しつつ、見返し入口を summary / remaining / contract memo へ寄せた
  - MS12 は引き続き GUI responsiveness / splash / packaging 系の別ラインとして維持

---

## 2026-04-01 / MS11-9 closeout and summary sync

- 対象: MS11-9 系全体
- 文書反映:
  - [docs/MS11-9_Summary_and_Handoff.md](d:/Kanna_Works/MMD_AppWork/MMD_AutoLipTool/MMD_AutoLipTool_Codex/docs/MS11-9_Summary_and_Handoff.md) を追加し、MS11-9 から MS11-9G までの変遷、レイヤ責務、実出力確認、現在の残課題を横断要約した
  - [docs/MS11-9_Remaining_Issues.md](d:/Kanna_Works/MMD_AppWork/MMD_AutoLipTool/MMD_AutoLipTool_Codex/docs/MS11-9_Remaining_Issues.md) を更新し、MS11-9G を MMD 側確認込みで一旦クローズ扱いへ整理した
  - [docs/MS11-9_Observation_Handoff_Contract_Memo.md](d:/Kanna_Works/MMD_AppWork/MMD_AutoLipTool/MMD_AutoLipTool_Codex/docs/MS11-9_Observation_Handoff_Contract_Memo.md) を更新し、top-end shaping を保留テーマへ移した
  - [docs/MS11_MS12_Roadmap_and_Scope_Split.md](d:/Kanna_Works/MMD_AppWork/MMD_AutoLipTool/MMD_AutoLipTool_Codex/docs/MS11_MS12_Roadmap_and_Scope_Split.md) と [docs/Specification_Prompt_v3.md](d:/Kanna_Works/MMD_AppWork/MMD_AutoLipTool/MMD_AutoLipTool_Codex/docs/Specification_Prompt_v3.md) を現状へ同期した
- 現在地:
  - same-vowel は微調整テーマとして継続
  - cross-vowel は F-4 で一旦停止基準を確定
  - top-end shaping は G と MMD 側確認をもって一旦クローズ
  - MS11-9 系の主な残テーマは same-vowel 微調整と observation 契約整理に絞られた

---

## 2026-04-01 / MS11-9G top-end shaping residual 整理メモ

- 対象: MS11-9G
- 実装反映:
  - `src/vmd_writer/writer.py` の `_resolve_peak_end_value_from_observation(...)` を更新し、`peak_end_frame` 以降の最初の RMS を主値に、直後 1 点を補助参照する局所安定化を追加
  - `tests/test_vmd_writer_intervals.py` と `tests/test_preview_transform.py` に、flat-top residual / 急減衰 residual の top-end 回帰を追加
  - `docs/MS11-9G_Implementation_Plan.md` に実装・確認結果を追記
- 確認状態:
  - `writer / Preview` 系と `pipeline / and_vmd` 系の主要回帰は通過
  - ローカル再生成の [dist/_tmp_ms11_9g_sample_input2_upper1.vmd](d:/Kanna_Works/MMD_AppWork/MMD_AutoLipTool/MMD_AutoLipTool_Codex/dist/_tmp_ms11_9g_sample_input2_upper1.vmd) は [Test11_9o.vmd](d:/Visual%20Works/Kanna%20Work/Voice/Test11_9o.vmd) と不一致であり、top-end shaping 差分が実出力へ届くことを確認
  - [Test11_9p.vmd](d:/Visual%20Works/Kanna%20Work/Voice/Test11_9p.vmd) はローカル再生成結果と一致
- 現在地:
  - MS11-9G は、新 family を増やさず writer-side の top-end 値配分だけで差分を出す段階まで到達した
  - 次段は「差分が出たか」より、「MMD 上で flat-top / 急減衰の見え方がどこまで自然になったか」の評価と微調整が主題になる

---

## 2026-04-01 / MS11-9F cross-vowel residual 整理メモ

- 対象: MS11-9F / MS11-9F-2 / MS11-9F-3 / MS11-9F-4
- 実装反映:
  - `src/core/pipeline.py` に cross-vowel representative span、moderate right-gap residual transition helper、wide 2-event zero-run residual floor helper を追加
  - `tests/test_pipeline_peak_values.py` に cross-vowel residual transition / floor の回帰を追加
  - `docs/MS11-9F_Implementation_Plan.md`、`docs/MS11-9F-2_Implementation_Plan.md`、`docs/MS11-9F-3_Implementation_Plan.md`、`docs/MS11-9F-4_Implementation_Plan.md` に段階到達を整理
- 確認状態:
  - `sample_input2` の residual cross-vowel は `23 -> 10 -> 7 -> 3`
  - `cross_transition = 17`, `cross_floor = 4` まで到達
  - `Test11_9n.vmd` は MS11-9F、`Test11_9m.vmd` は MS11-9F-2、`Test11_9o.vmd` は MS11-9F-3 のローカル再生成結果と一致
  - cross-vowel 改善は段階的に実出力差分まで到達している
- 文書上の確定:
  - `idx 172` / `193` は pause 寄りの非対象候補として扱う
  - `idx 6` は mixed-gap 境界 case として保留する
  - MS11-9F-4 は「残件を無理に救済し切る」のではなく、「ここで閉じる基準を明示する」段階として確定扱いとする
- スコープ外として維持:
  - `idx 6` の mixed-gap 個別救済
  - top-end shaping 再調整
  - MS12

---

## 2026-04-01 / MS11-9C 実装反映メモ

- 対象: MS11-9C Lip Hold GUI exposure and final-closing hold semantics alignment
- 実装反映:
  - `src/gui/main_window.py` / `src/gui/central_panels.py` / `src/gui/settings_store.py` / `src/gui/i18n_strings.py` / `src/core/pipeline.py` に、`開口保持` / `Lip Hold` と `closing_hold_frames` の GUI・保存・Preview・export handoff を追加
  - `src/vmd_writer/writer.py` に、final closing を `hold -> 70% midpoint -> zero` として再構成する処理を追加
  - 対象 family は MS11-2 / legacy symmetric trapezoid / legacy triangle / peak fallback / MS11-3 multi-point envelope
  - `closing_hold_frames` は hold 区間だけの長さとして扱い、70% midpoint は最後の non-zero 値の 70% を使う
  - `peak == 0.0` 相当のイベントは shape 非生成であり、clamp blocker にも使わない方針を writer / Preview の両方へ反映
  - clamp 上限は、次の有効 non-zero shape 開始直前までに統一
  - `tests/test_vmd_writer_intervals.py` と `tests/test_preview_transform.py` を更新し、hold / midpoint / zero-peak clamp の回帰を追加
- 確認状態:
  - GUI の `開口保持` と `閉口スムース` は単一路線で Preview / export に渡る
  - Preview は writer と同じ family 境界・clamp 規則で closing shape を表現する
  - `sample_input2` の実データ確認で、zero-peak 後の長い無音区間を不必要に早く閉じないことを確認
  - `tests.test_vmd_writer_intervals`、`tests.test_preview_transform`、`tests.test_main_window_closing_softness`、`tests.test_settings_store`、`tests.test_pipeline_and_vmd` が通過
- スコープ外として維持:
  - RMS 再調整
  - 無音判定ロジック全体の再設計
  - MS12

---

## 2026-04-01 / MS11-9C 実装前整理メモ

- 対象: MS11-9C Lip Hold GUI exposure and final-closing hold semantics alignment
- 実装前固定:
  - `closing_softness_frames` の意味は維持し、新規 parameter `closing_hold_frames` を追加する
  - `closing_hold_frames` は final closing 前に最後の non-zero を一定フレーム保持する
  - 適用順は `hold -> softness -> clamp`
  - 対象は final closing が実在する MS11-2 / legacy / peak fallback / MS11-3 family
  - 開始側固定、zero-only 非生成、後続 shape 開始前 clamp を維持する
  - Preview と writer は同じ family 境界で揃える
  - GUI 名称は `開口保持` / `Lip Hold`
  - UI 並び順は `モーフ最大値` → `開口保持` → `閉口スムース`
- 主変更想定:
  - `src/vmd_writer/writer.py`
  - `src/gui/preview_transform.py`
  - `src/gui/main_window.py`
  - `src/gui/central_panels.py`
  - `src/gui/settings_store.py`
  - `src/gui/i18n_strings.py`
- 最低限の確認観点:
  - `closing_hold_frames=0` 互換
  - hold 単独効果
  - softness との併用
  - Preview / export 整合
  - settings round-trip

---

## 2026-04-01 / MS11-9B 実装前整理メモ

- 対象: MS11-9B Closing Softness GUI exposure and preview/output handoff alignment
- 実装前固定:
  - `閉口スムース` を `モーフ最大値` の右横に配置し、`[input] フレーム` / `[input] Frame` の単位表示を常時出す
  - 値仕様は `int / 0以上 / default 0`、解釈は一貫して frame count とする
  - Preview 更新と export handoff は同じ単一の現在値参照経路を使う
  - `閉口スムース` 変更時は `current_timing_plan` を破棄せず、再解析を走らせず、Preview 再描画と設定保存更新に留める
  - 処理中ロックは spinbox 本体だけでなく `-` / `+` ボタンも含めて一貫させる
  - MS11-8 final-closing-only semantics と zero-only shape 非生成の安全条件を崩さない
- 主変更想定:
  - `src/gui/central_panels.py`
  - `src/gui/i18n_strings.py`
  - `src/gui/main_window.py`
  - `src/gui/settings_store.py`
- 最低限の確認観点:
  - `softness=0` 互換
  - 再解析非発生
  - Preview 反映
  - export handoff
  - settings round-trip
  - 日英の単位表示

---

## 2026-04-01 / MS11-9 実装反映メモ

- 対象: MS11-9 Preview trapezoid / multi-point display alignment
- 実装反映:
  - `src/gui/preview_transform.py` に `PreviewControlPoint` と `shape_kind` / `control_points` を追加し、`rows -> segments` の流れを維持した最小契約拡張を実施
  - writer 側 helper を再利用し、MS11-2 asymmetric trapezoid / legacy triangle / legacy symmetric trapezoid / MS11-3 multi-point envelope / MS11-8 closing softness を Preview 用 shape として再構成
  - shape semantics は 30fps frame basis で解決し、Preview 描画入力は seconds basis へ変換する方針を反映
  - `src/gui/preview_area.py` を矩形塗りつぶし中心描画から polygon / path ベース shape 描画へ更新
  - visible range clipping 時の control point 補間、および shared viewport / playback cursor / waveform plot area rect 基準整合を維持
  - `src/gui/main_window.py` は変更せず、既存 `build_preview_data(self.current_timing_plan.timeline)` handoff を維持
  - `tests/test_preview_transform.py` を更新し、trapezoid / legacy 区別 / multi-point / closing softness / mixed case clamp の回帰を追加
- 確認状態:
  - Preview は単純矩形ではなく writer-side shape semantics に近い形を描画できる
  - trapezoid 表示は必須対応分を反映済み
  - representative multi-point shape は表現でき、mixed case でも破綻しない範囲を確認済み
  - shared viewport / playback sync の既存導線は維持されている
  - `tests.test_preview_transform`、`tests.test_vmd_writer_intervals`、`tests.test_vmd_writer_multipoint_shape`、`tests.test_pipeline_and_vmd` が通過
- スコープ外として維持:
  - GUI からの closing softness 入力導線
  - RMS 再調整
  - MS11-10 / MS12

---

## 2026-04-01 / MS11-8 実装反映メモ

- 対象: MS11-8 `writer.py` 側 mouth-closing softness control
- 実装反映:
  - `src/vmd_writer/writer.py` に `closing_softness_frames: int = 0` を追加
  - `closing_softness_frames` を additive frame-count concept として扱い、`softness=0` は現行出力互換を維持
  - MS11-2 closing は `peak_end_frame` 固定 / `end_frame` 延長で実装
  - `legacy_triangle` / `legacy_symmetric_trapezoid` は final closing のみ延長
  - MS11-3 は final `end_zero` のみ延長し、中間 valley 側下降辺には触れない
  - 後続 shape 開始直前で clamp し、後段 normalization へ衝突解消を委ねない方針を反映
  - `protected_envelope_ranges` / `allowed_non_zero_ranges` / `required_zero_frames` を延長後 shape に合わせて整合
  - `src/core/pipeline.py` には writer への最小 handoff のみを追加
  - writer 系テストと `tests/test_pipeline_and_vmd.py` に最小回帰確認を追加
- 確認状態:
  - `softness=0` の既存挙動互換を維持
  - zero-only shape 抑止、short / legacy fallback 保護、MS11-2 / MS11-3 保護導線を維持
  - 対象 86 件の関連テストが通過
- スコープ外として維持:
  - GUI 入力導線
  - Preview 表示整合
  - RMS 再調整
  - MS11-9 / MS11-10 / MS12

---

## 2026-04-01 / Ver 0.3.6.4 同期メモ

- 対象: MS11-7 文書整備・最小テスト反映後の版同期
- 同期内容:
  - `README.md` / `pyproject.toml` / `docs/Specification_Prompt_v3.md` / `docs/MS11_MS12_Roadmap_and_Scope_Split.md` / `docs/MS11-7_Implementation_Plan.md` / `docs/repo_milestone.md` / `docs/Version_Control.md` を `Ver 0.3.6.4` 基準へ同期
  - MS11-7 の到達状態を「実データ review 本体の前段としての文書整備 + 最小テスト追加」までとして整理
  - リポジトリ全体の反映版を `Ver 0.3.6.4` として確定
- 確認状態:
  - `docs/MS11-7_Real_Data_Observation_Review.md` が実データ review の正本テンプレートとして追加済み
  - `tests/test_pipeline_peak_values.py` の最小追加で observation 記録欄整合を固定済み
  - RMS 定数変更、`pipeline.py` helper 追加、writer / GUI 改修は未実施
- 次段階:
  - 実データの投入
  - reason 別整理
  - RMS 定数再調整要否の最終判断

---

## 2026-04-01 / MS11-7 文書整備・review 雛形追加メモ

- 対象: MS11-7 実装開始時の文書整備と review 正本雛形追加
- 反映内容:
  - `docs/MS11-7_Implementation_Plan.md` を、MS11-7 の固定方針に沿って整理
  - `docs/MS11-7_Real_Data_Observation_Review.md` を新規追加し、実データ観測結果の正本テンプレートを整備
  - `tests/test_pipeline_peak_values.py` に、`global_peak_zero` observation の記録欄整合を確認する最小テストを追加
- 確認状態:
  - `peak_value = 0.0` を一律不具合扱いしない方針を維持
  - 今回は RMS 定数変更そのものを行っていない
  - `pipeline.py` への review 専用 helper 追加や writer / GUI 改修には広げていない
- 次段階:
  - 実データを投入して reason 別に記録
  - 同種の不自然 zero case の複数確認有無に基づき、再調整要否を判断

---

## 2026-03-31 / Ver 0.3.6.3 同期メモ

- 対象: MS11-6 実装反映後の版同期
- 同期内容:
  - `pipeline.py` の main-flow-connected observation 接続、provided timing plan 経路の observation 方針、および関連テスト更新の反映状態を関連ドキュメントへ同期
  - `README.md` / `pyproject.toml` / `docs/Specification_Prompt_v3.md` の版数表記を `Ver 0.3.6.3` へ更新
  - リポジトリ全体の反映版を `Ver 0.3.6.3` として確定
- 確認状態:
  - `VowelTimingPlan` を正本とした optional observation 保持が main flow に接続済み
  - `timeline` を canonical writer input とする既存導線は維持済み
  - provided timing plan 経路は「そのまま利用時は observation 維持」「duration 補完時は `observations=None`」の方針をテストで明文化済み
- 次段階:
  - MS11-7: 実データ observation review と RMS 定数再調整判断

---

## 2026-03-31 / MS11-6 実装反映メモ

- 対象: MS11-6 `pipeline.py` 側 observation connection cleanup
- 実装反映:
  - `src/core/pipeline.py` で `VowelTimingPlan` に optional な `observations` を追加し、main flow から observation を参照可能化
  - refine 前 initial timeline と refine 後 timeline を main flow 内で対として追跡し、`PeakValueObservation` を構築する内部接続を追加
  - `PipelineResult` には optional な observation の受け渡しのみを追加し、writer handoff は引き続き `timeline` を canonical input として維持
  - provided timing plan をそのまま使う経路では observation を維持し、duration 補完を行った provided timing plan 経路では `observations=None` に落とす方針を整理
  - `tests/test_pipeline_and_vmd.py` に、main-flow-connected observation 取得確認と、provided timing plan 2 経路の observation 挙動確認を追加
- 確認状態:
  - `tests.test_pipeline_peak_values` 14 件が通過
  - `tests.test_pipeline_and_vmd` 8 件が `PYTHONPATH='src;tests'` 付きで通過
  - `tests.test_vmd_writer_peak_value` 4 件が通過
  - 上記の範囲で MS11-6 の主目的と残確認事項が収束している
- スコープ外として維持:
  - `writer.py` 再設計
  - GUI / Preview 改修
  - RMS 定数再調整

---

## 2026-03-30 / Ver 0.3.6.2 同期メモ

- 対象: MS11-5 観測支援反映後の版同期
- 同期内容:
  - `pipeline.py` の observation helper / observation record、および pipeline 系テスト拡張の反映状態を関連ドキュメントへ同期
  - `README.md` / `pyproject.toml` / `docs/Specification_Prompt_v3.md` / `docs/MS11-5_Implementation_Plan.md` の版数表記を `Ver 0.3.6.2` へ更新
  - リポジトリ全体の反映版を `Ver 0.3.6.2` として確定
- 確認状態:
  - MS11-5 第一段階の観測支援実装と関連テスト更新が反映済み
  - `writer.py` 再設計なしで pipeline 側観測性のみを拡張した状態を維持
  - 関連 docs は MS11-5 第一段階反映後の状態へ同期済み
- 残課題:
  - 実データ上の `peak_value = 0.0` 事例の理由別整理
  - RMS 定数再調整要否の判断整理
  - 必要に応じた複合ケース観測テストの追加整理

---

## 2026-03-30 / MS11-5 観測支援 実装反映メモ

- 対象: MS11-5 `pipeline.py` 側 observation helper / observation record / pipeline 系テスト拡張
- 実装反映:
  - `src/core/pipeline.py` に、既存 `PeakValueEvaluation` を維持したまま上位観測レコード `PeakValueObservation` を追加
  - event index / vowel / `time_sec` / 元 interval / RMS 補正後 interval / peak window / `local_peak` / `global_peak` / `peak_value` / `reason` / fallback 情報 / window sample 数をまとめて返せる internal helper を追加
  - 観測 helper は既存 peak 評価結果を再利用して構成し、本処理ロジックの正本を置き換えない方針で接続
  - `tests/test_pipeline_peak_values.py` に、元 interval と補正後 interval の同時確認、halo 窓と sample 数確認、`rms_unavailable` fallback 観測、initial timeline 長不一致の観点を追加
- 確認状態:
  - `tests.test_pipeline_peak_values` 14 件が通過
  - `tests.test_pipeline_and_vmd` 6 件が `PYTHONPATH='src;tests'` 付きで通過
  - `tests.test_vmd_writer_peak_value` 4 件が通過
  - 上記合計 24 件の回帰確認が通過
  - `writer.py` 再設計や GUI / Preview 改修なしで、pipeline 側観測性のみを拡張している
- 残課題:
  - 実データ上の `peak_value = 0.0` 事例の理由別整理
  - RMS 定数再調整要否の判断整理
  - 必要に応じた複合ケース観測テストの追加整理
- スコープ外として維持:
  - `writer.py` 再設計
  - GUI / Preview 改修
  - 大幅な RMS 定数チューニング

---

## 2026-03-29 / Ver 0.3.6.1 同期メモ

- 対象: MS11-4 実装反映、関連ドキュメント更新、周辺差分のリポジトリ同期
- 同期内容:
  - MS11-4 の `pipeline.py` 変更、pipeline 系テスト更新、MS11-4 到達整理を関連ドキュメントへ反映
  - `README.md` / `pyproject.toml` / `docs/Specification_Prompt_v3.md` の版数表記を `Ver 0.3.6.1` へ更新
  - ワークスペース内に存在していた関連ドキュメント・設定更新も同一同期に含める
  - リポジトリ全体の反映版を `Ver 0.3.6.1` として確定
- 確認状態:
  - MS11-4 の構造修正とテスト更新が反映済み
  - `writer.py` 再設計なしで pipeline-writer 回帰が通る状態を維持
  - 既存 docs と版管理ログは MS11-4 反映後の状態へ同期済み
- 残課題:
  - 実データ上での `peak_value = 0.0` 事例の観測蓄積
  - 必要最小限に限った RMS 定数の再調整判断
  - internal helper / test 観測点を起点にした MS11-5 の整理

---

## 2026-03-29 / MS11-4 実装反映メモ

- 対象: MS11-4 `pipeline.py` 側 event interval / peak 割当品質改善
- 実装反映:
  - `src/core/pipeline.py` で、正本 interval と peak 探索窓の責務を分離
  - RMS 補正後 interval を `peak_value` 評価の正本とし、halo `±0.03 sec` を隣接 interval 端点中点でクリップする peak window を導入
  - `load_rms_series()` 失敗時の一律 `upper_limit` fallback を廃止し、`upper_limit * 0.25` の保守的 fallback へ変更
  - RMS は取得できたが `global_peak <= 0.0` の場合、全 event を `peak_value = 0.0` とする分岐を追加
  - `peak_value = 0.0` 理由を `rms_unavailable / global_peak_zero / no_peak_in_window / below_abs_threshold / below_rel_threshold` で追跡できる internal helper を追加
  - event は削除せず、interval を維持したまま `peak_value` と理由分類の整合を改善
  - `tests/test_pipeline_peak_values.py` を拡張し、halo 探索・fallback・理由分類優先順を単体で確認できるよう更新
- 確認状態:
  - `tests.test_pipeline_peak_values` 10 件が通過
  - `tests.test_pipeline_and_vmd` と `tests.test_vmd_writer_peak_value` 10 件が通過
  - `tests.test_vmd_writer_zero_guard` と `tests.test_vmd_writer_intervals` 43 件が通過
  - 上記合計 63 件の回帰確認が通過
  - `writer.py` の再設計なしで、`peak_value = 0.0` event を既存 writer 側へ受け渡せる状態を維持
- 残課題:
  - 実データ上での `peak_value = 0.0` 事例の観測蓄積
  - 必要最小限に限った RMS 定数の再調整判断
  - internal helper / test 観測点を起点にした MS11-5 の整理
- スコープ外として維持:
  - `writer.py` 再設計
  - GUI / Preview 改修
  - MS11-5 の全面実装

---

## 2026-03-28 / Ver 0.3.6.0 同期メモ

- 対象: MS11-3 実装完了後の版同期
- 同期内容:
  - `src/vmd_writer/writer.py` の MS11-3 本体、段階 fallback、envelope 保護、FIX01 / FIX02 整合、writer 局所の zero-only shape / short fallback 保護修正を関連ドキュメントへ反映
  - writer 系テスト拡張と回帰確認結果、`pipeline + writer` の参照的確認結果を `docs/Specification_Prompt_v3.md` / `docs/Version_Control.md` に同期
  - リポジトリ全体の反映版を `Ver 0.3.6.0` として確定
- 確認状態:
  - writer 系テスト 67 件が通過している
  - `PYTHONPATH='src;tests'` 付きの `tests.test_pipeline_and_vmd` と `tests.test_pipeline_peak_values` を含む 9 件が通過している
  - `peak_value == 0.0` 由来の意味のない全ゼロ台形は最終出力へ残さない
  - 正規な short / legacy fallback shape は current normalization flow でも不必要に消えない
  - MS11-3 / MS11-2 / legacy fallback の順序と、MS11-2 / FIX01 / FIX02 の到達状態を維持している
- 既知課題として維持:
  - `docs/MS11-2_Known_Issues.md` に整理済みの「無音に見える区間の開口残存」は今回も既知課題のままとし、解決済み扱いにしない
- スコープ外として維持:
  - GUI / Preview の multi-point 表示対応
  - `pipeline.py` 側イベント存在判定ポリシー改善
  - より高度な平滑化
  - 出力仕様全体の再設計

---

## 2026-03-28 / MS11-3 実装完了メモ

- 対象: MS11 出力品質拡張の第3段階
- 実装反映:
  - `src/vmd_writer/writer.py` を主対象として、同一母音近接イベント群を multi-point shape として扱う MS11-3 を実装
  - 秒ベース grouping と frame ベース成立判定を導入し、multi-point shape 生成・`MorphFrame` 展開・採用条件判定を追加
  - 谷値は非ゼロ維持の固定ルールで扱い、`peak_value` を上辺点高さへ反映
  - MS11-3 不成立時は MS11-2 単一上辺台形、さらに不成立時は legacy fallback へ戻る段階フォールバックを接続
  - 後段正規化に対して、MS11-3 成功 shape を envelope 全体単位で保護する導線を追加
  - FIX01 / FIX02 の改善意図を崩さないよう、allowed range / required zero / suppression / zero prune の整合を writer 側で維持
  - writer 系テストを拡張し、grouping / multi-point shape / fallback / protection / FIX01-FIX02 回帰を自動確認できる状態にした
- 到達状態:
  - 同一母音近接イベント群は、条件を満たす場合 multi-point shape として出力される
  - 谷は原則 0.0 へ完全閉口せず、非ゼロで維持される
  - MS11-3 成功時は envelope 全体を allowed non-zero range / protected range の単位として扱う
  - MS11-3 / MS11-2 / legacy fallback の順序が writer 内で成立している
  - writer 系テスト 65 件、および `PYTHONPATH='src;tests'` 付きの `tests.test_pipeline_and_vmd` 6 件が通過している
- 既知課題として維持:
  - `docs/MS11-2_Known_Issues.md` に整理済みの「無音に見える区間の開口残存」は今回も既知課題のままとし、解決済み扱いにしない
- スコープ外として維持:
  - GUI / Preview の multi-point 表示対応
  - `pipeline.py` 側イベント存在判定ポリシー改善
  - より高度な平滑化
  - 出力仕様全体の再設計

---

## 2026-03-27 / Ver 0.3.5.9 同期メモ

- 対象: MS11-2 / MS11-2_FIX01 / MS11-2_FIX02 の反映版同期
- 同期内容:
  - `src/vmd_writer/writer.py` の MS11-2 本体、FIX01、FIX02 の修正内容を関連ドキュメントへ反映
  - writer 系テスト更新内容と到達状態を `docs/Specification_Prompt_v3.md` / 各 Implementation Plan / `docs/Version_Control.md` に同期
  - リポジトリ全体の反映版を `Ver 0.3.5.9` として確定
- 確認状態:
  - writer 系テスト 33 件が通過している
  - MS11-2 は 4点の非対称・単一上辺台形、`time_sec` 上辺中央基準、4 frame 未満 fallback、MS11-1 との部分保護接続を維持
  - FIX01 / FIX02 により、無音区間の非ゼロ除去、不要ゼロ cleanup、発話イベント内部 shape 保護の補正まで反映済み
- スコープ外として維持:
  - 多ポイント台形
  - 上辺複数点対応
  - より高度な平滑化
  - `pipeline.py` の構造変更
  - 出力仕様全体の再設計

---

## 2026-03-27 / MS11-2 実装完了メモ

- 対象: MS11-2 出力品質拡張の第2段階
- 実装反映:
  - `src/vmd_writer/writer.py` に、4点の非対称・単一上辺台形を扱う内部仕様 `AsymmetricTrapezoidSpec` を追加
  - 区間処理を「区間 → 台形仕様 → MorphFrame 展開」の二段構造へ整理
  - `start_sec / time_sec / end_sec` を 30fps で frame 化したうえで、`time_sec` を上辺中央基準として扱う変形台形判定を追加
  - `start_frame`〜`end_frame` が 4 frame 以上のときのみ上辺ありの変形台形を生成し、4 frame 未満では既存短区間フォールバックへ戻す接続を整理
  - 開始 / 終了ゼロ保証を維持した 4点展開と、MS11-1 最終正規化層への導線維持を実装
  - 正規な MS11-2 由来形状が孤立短開口抑制 / 個別モーフ短パルス整理で無条件に潰れないよう、必要最小限の部分保護を追加
  - `tests/test_vmd_writer_intervals.py` / `tests/test_vmd_writer_peak_value.py` / `tests/test_vmd_writer_zero_guard.py` を更新し、正常系 / 境界系 / 正規化連携 / 既存保証の観点を反映
- 到達状態:
  - 適用可能区間は旧対称台形ではなく、4点の非対称・単一上辺台形で出力される
  - `time_sec` は上辺中央基準として frame 配置へ反映される
  - 4 frame 未満は既存短区間フォールバックへ落ちる
  - MS11-1 の最終正規化層を維持したまま、正規な MS11-2 由来形状のみを原則維持する構造になった
  - writer 系テスト 29 件が通過している
- スコープ外として維持:
  - 多ポイント台形
  - 上辺複数点対応
  - より高度な平滑化
  - `pipeline.py` の構造変更
  - GUI / 波形 / 再生ロジック改修

---

## 2026-03-26 / MS11-1 実装完了メモ

- 対象: MS11-1 出力品質拡張の第1段階
- 実装反映:
  - `src/vmd_writer/writer.py` に最終モーフフレーム正規化層を追加
  - `(morph_name, frame_no)` 単位の一般重複正規化を実装し、非ゼロ優先 / 複数非ゼロは最大値 / 全ゼロは1件化を適用
  - 母音全体の `open_value = max(あ, い, う, え, お)` を扱う内部表現と `epsilon` ベースの開閉判定を追加
  - 開口区間 / 閉口区間抽出と、前後閉口に挟まれた孤立短開口候補検出を追加
  - 孤立短開口候補の 0 化による抑制と、母音全体の開口列を変えない範囲に限定した個別モーフ短パルス整理を追加
  - `tests/test_vmd_writer_zero_guard.py` に重複統合 / 瞬間開閉 / 30fps 丸め衝突 / 既存仕様維持の確認を追加
- 到達状態:
  - 最終 VMD キー列で同一モーフ・同一フレーム重複が残らない
  - 母音全体ベースで孤立した短開口だけを抑制する構造になった
  - 他モーフ非ゼロ時に単一モーフだけ見て誤って閉口扱いしない
  - 開始 / 終了ゼロ保証、通常台形出力、短区間フォールバック、最大フレーム数ガード、書き出し順安定性を維持する方針で接続した
- スコープ外として維持:
  - 変形台形
  - 多ポイント台形
  - 上辺複数点対応
  - より高度な平滑化
  - `pipeline.py` の構造変更
  - GUI / 波形 / 再生ロジック改修

---

## 2026-03-25 / MS10 実装完了メモ

- 対象: MS10 多言語化・設定永続化
- 実装反映:
  - `src/gui/settings_store.py` を追加し、`MMD_AutoLipTool.ini` による設定保存・復元導線を実装
  - `src/main.py` で起動時設定読込と OS 言語フォールバックを接続
  - `src/gui/main_window.py` でテーマ / splitter 比率 / ウィンドウサイズ / 言語 / モーフ最大値 / recent TEXT / recent WAV の保存・復元導線を実装
  - `src/gui/i18n_strings.py` を GUI 文字列正本として整理し、日本語 / 英語の切替基盤を実装
  - `src/gui/operation_panel.py` / `src/gui/central_panels.py` / `src/gui/status_panel.py` / `src/gui/waveform_view.py` / `src/gui/preview_area.py` に実行中言語切替反映を実装
  - recent TEXT / WAV の別管理、起動時無効履歴除去、0 件時プレースホルダ表示を実装
  - 波形表示の空状態文言 / 軸ラベル / 母音表示、および Preview 側母音表示の言語対応を実装
  - 波形表示の日本語プレースホルダと横軸ラベルに対する Matplotlib 和文フォント適用を反映
- 到達状態:
  - 日本語 / EN の実行中切替が成立
  - 言語設定と recent 履歴が次回起動時に復元される
  - 重要 UI 設定とモーフ最大値が永続化される
  - 設定破損時フォールバックと保存失敗時の安全停止が入っている
  - 文字列定義の正本は `i18n_strings.py` に集約された
- リリース同期:
  - リポジトリ全体の反映版を `Ver 0.3.5.8` として確定。

---

## 方針

既存の処理導線（TEXT読込 → WAV読込 → 処理実行 → 出力）を崩さず、  
GUI層・表示層・設定層・処理層が混線しにくい順で段階的に実装する。

---

## マイルストーン一覧

| No. | マイルストーン名 | 対象項目 | 目的 | 完了条件 |
| MS1 | 画面骨格整理 | トップメニュー「ファイル」追加 / ボタン再配置 / 読み込みエリアと表示エリアの区分け | GUIの基本導線を整理し、後続機能の追加先を安定させる | ボタン操作とメニュー操作が同じ処理を呼ぶ。レイアウト変更後も既存導線が崩れない。 |
| MS2 | 読込エラー統一 | 壊れたファイル、不明ファイル読込時の処理 | 入力異常時の挙動を統一し、例外経路の散在を防ぐ | TEXT/WAV読込失敗時の警告表示、内部状態、後続操作禁止条件が一貫する。 |
| MS3 | 波形確認性向上 | 波形表示に30fps縦線区切りを表示 | MMD基準での確認性を上げる | 波形上に30fps基準の縦線が表示され、既存ラベル表示と干渉しない。出力結果には影響しない。 |
| MS4 | 実行中状態の可視化 | 処理中ダイアログ / プログレスバー表示 | 重い処理実行中の状態を明確化する | 処理実行中の状態遷移が明確で、二重実行防止と終了後復帰が整合する。 |
| MS5 | 利便性設定追加① | 読み込み関係のカレントディレクトリ記憶 | 読込操作の手間を減らす | TEXT/WAVそれぞれで直前ディレクトリが保持され、次回読込時に利用される。 |
| MS6 | 利便性設定追加② | ファイル読み込み履歴を各10個記憶し、再呼び出しできるGUI追加 | 再読込の利便性を上げる | 履歴追加・削除・再読込の挙動が一貫し、失敗読込の扱いも定義される。 |
| MS6B | 同名対応ファイルの自動補完読込 | 同一フォルダ・同一 stem の相方（`.txt/.wav`）を主読込成功後に1回試行 | 通常読込/履歴再読込の入力手間を減らしつつ既存導線を維持する | 既読込側は上書きせず、未存在/読込失敗はサイレント、成功時は履歴/表示/開始ディレクトリ保持が既存成功導線で反映され、再連鎖しない。 |
| MS7 | 入出力安全性点検 | セキュリティ関係のチェック | ファイル入力・設定保存まわりの安全性を確認する | 入力・保存・履歴保存・例外処理について危険箇所の確認と修正方針が整理される。 |
| MS8 | 出力品質拡張 | モーフのスムージング | 口の動きの滑らかさを改善する | 既存台形出力との差分を比較でき、現行仕様を壊さず追加評価できる。 |
| MS8A | GUI再構成基盤 | 上部操作列分離 / モーフ上限値UI再配置 / 中央2カラム化 / ステータス欄専用部品化 | 既存導線を維持したまま v3 GUI骨格を最小変更で導入する | `main_window.py` を司令塔のまま、`OperationPanel` / `StatusPanel` を表示専用で組み込み、既存安全動作を維持する。 |
| MS8B | Preview Area 静止表示導入 | `PreviewArea` 追加 / `preview_transform.py` 追加 / `main_window.py` の受け渡し導線整理 / クリア・無効化導線整理 / silent restore 整合 | `current_timing_plan.timeline` を正本とした Preview 静止表示を最小変更で導入する | 5段固定（あ/い/う/え/お）で静止表示でき、解析結果無効化時は Preview をクリアし、`suppress_warning=True` 復元時も Preview 表示整合を維持し、既存導線（TEXT/WAV/処理実行/VMD出力）を維持する。 |
| MS8C | 再生基盤導入 | `playback_controller.py` / `view_sync.py` / Play・Stop・現在地同期 | 波形・Preview Area・ステータスを再生位置で同期させる | Play は処理実行後のみ有効、Stop は再生中のみ有効となり、再生開始は常にゼロフレームからで、波形・Preview Area・ステータス表示が共通位置で同期する。 |
| MS8D-2 | 表示詳細化（改訂） | 横軸フレーム表記 / 共通ビューポート / Zoom / Pan / Preview目盛り / Zoomメニュー導線 / パス中間省略+tooltip | MMD基準での確認性と操作性を高め、波形と Preview Area の表示一貫性を成立させる | 秒内部保持を維持したまま、波形・Preview が同一可視範囲で同期し、Zoom/Pan とパス表示拡張が既存主要導線を壊さず動作する。 |
| MS9 | GUI整備 | アイコン＋文字ボタン化 / ボタン固定サイズ＋折り返し / 英語時の省略記号対応 / ボタン群グルーピング / 状態差の視覚化 / 左右領域の可変分割 / テキスト領域幅調整 / 波形/Preview のテーマ追従配色 / 波形表示配色調整 / `Amp` 削除 / ステータス表示整理 / 分析完了音 / 多言語化を見据えた文言長耐性 | モックアップに近いユーザーフレンドリーな GUI へ整備し、後続の多言語化・設定永続化の前提となる画面構造と外観を安定させる | 主要操作がアイコン＋文字ボタンで視認しやすく整理され、縮小時も折り返しと可変分割で破綻しにくい。波形/Preview は新配色で可読性を維持し、ステータス表示と完了通知を含めて GUI 全体の操作理解性が向上する。日本語/英語の文字長差でもレイアウトが大きく崩れない。 |
| MS10 | 多言語化・設定永続化 | `i18n_strings.py` / `settings_store.py` / 言語切替 / 履歴永続化 | UI多言語化と設定保存を分離責務で導入する | 日本語/EN の実行中切替が成立し、言語設定と履歴が次回起動に復元される。文字列定義の正本は1か所に集約される。 |
| MS11 | 出力品質拡張 | モーフスムージング / 変形台形 / 複数上辺点対応 | 口の動きの滑らかさを改善する | 既存台形出力との差分を比較でき、開始/終了ゼロ点を維持したまま、変形台形や同一母音連続時の複数上辺点を評価できる。 |

---

## 進捗メモ（2026-03-20）

- リリース同期:
  - リポジトリ全体の反映版を `Ver 0.3.5.1` として確定
- 完了:
  - MS1 画面骨格整理
  - MS2 読込エラー統一
  - MS3 波形確認性向上
  - MS4 実行中状態の可視化（フェーズ1〜6）
  - MS5 利便性設定追加①（フェーズ1〜9）
  - MS6 利便性設定追加②（フェーズ1〜9）
  - MS6B 同名対応ファイルの自動補完読込（フェーズ1〜10）
  - MS7 入出力安全性点検（フェーズ1〜8）
  - MS8A GUI再構成基盤（フェーズ1〜10）
  - MS8B Preview Area 静止表示導入（フェーズ1〜9）
- MS4 完了時の確認結果（要点）:
  - 処理中ダイアログ表示（不定進捗、キャンセルなし）
  - 処理中の再入防止
  - 処理中の操作ロック（読込/再実行/出力/履歴/モーフ上限値）
  - 成功/失敗時の復帰整合（ダイアログ終了・busy解除・状態表示復帰）
- MS7 完了時の確認結果（要点）:
  - TEXT/WAV 読込入口で、空・非存在・ディレクトリなどの事前確認を最小導入
  - VMD 保存入口で、`.vmd` 補完後パスの妥当性確認を導入
  - 履歴再読込で、危険値（空/非存在/ディレクトリ/拡張子不一致）を事前確認
  - 履歴再読込失敗時は該当履歴のみ除去し、メニュー更新を維持
  - 想定外例外時も GUI 警告へフォールバックし、状態復帰を統一
- MS5 完了時の確認結果（要点）:
  - TEXT/WAV 読込ダイアログの開始位置を、それぞれ独立した保持値で管理
  - 通常読込成功時のみ、各保持値を「選択ファイルの親ディレクトリ」で更新
  - 履歴再読込成功時にも同様に更新し、失敗時の既存履歴除去ロジックを維持
  - 保持値が無効（未設定/空/非存在/非ディレクトリ）でも警告追加なしで安全フォールバック
  - フェーズ9観点（9-1〜9-5）をコード上で満たし、最小実行確認でも PASS
- MS6 完了時の確認結果（要点）:
  - TEXT/WAV 履歴を別配列で保持し、通常読込成功時のみ対応側履歴へ追加
  - 重複時は先頭再配置、上限10件超過時は末尾削除で統一
  - 履歴メニュー再構築時は古い action をクリアし、各項目を対応する再読込処理へ接続
  - 壊れた履歴値（空/非存在/ディレクトリ/拡張子不一致）と再読込失敗時は、該当履歴のみ除去して即時メニュー更新
  - TEXT/WAV の履歴更新先・メニュー表示元・再読込導線が相互に混線しないことをコード上で固定
  - フェーズ9観点（10件上限/重複先頭移動/再読込導線/壊れた履歴値除去/非混線）を最小スモーク確認で PASS
- MS6B 完了時の確認結果（要点）:
  - 発動対象は通常読込と履歴再読込に限定し、セッション外永続化の復元時発動は対象外のまま維持
  - 同一フォルダ・同一 stem・拡張子相補（`.txt/.wav`、大文字小文字非区別）で相方候補を解決
  - 主読込成功時のみ補完を1回試行し、反対側が既読込なら補完しない
  - 相方未存在/読込失敗はサイレントで終了し、専用通知を追加しない
  - 自動補完成功時は既存読込成功導線を再利用し、履歴更新・表示更新・読込開始ディレクトリ保持を反映
  - 補完側から逆方向補完を起こさない構造で再連鎖を防止
- MS8A 完了時の確認結果（要点）:
  - 上部操作列を `OperationPanel` に置換し、`text/wav/process/output` の既存接続先を維持
  - モーフ上限値UI（`morph_upper_limit_label/input`）を操作列直下へ再配置し、変更時の再解析待ち復帰導線（`current_timing_plan=None` / 波形ラベルクリア / 自動再解析なし）を維持
  - 中央領域を左右2カラム化し、左にテキスト系・ファイル状態系、右上に既存 `WaveformView`、右下に将来用プレースホルダを配置
  - 最下部ステータス表示を `StatusPanel` 化し、`_set_output_status(...)` の表示先を `StatusPanel` へ統一
  - `_update_action_states()` の判定ロジックは `main_window.py` に維持し、Play/Stop/Zoom は未実装ボタンとして無効固定
  - 既存主要導線（TEXT読込 / WAV読込 / 処理実行 / VMD出力）と既存安全動作（処理中ダイアログ・二重実行防止・未解析時保存禁止・処理中ロック）を維持
  - MS8A 範囲外（Preview実装 / 再生機能 / Zoom機能 / 多言語化 / 設定永続化 / 出力品質拡張）は未実装のまま後続対象として保持

---

## 進捗メモ（2026-03-21 / リリース同期）

- リポジトリ全体の反映版を `Ver 0.3.5.3` として同期。
- MS8B（Preview Area 静止表示導入）の実装反映状態を含めて、現作業ツリーを確定対象とする。

---

## 進捗メモ（2026-03-24 / Ver 0.3.5.7 リリース同期）

- リポジトリ全体の反映版を `Ver 0.3.5.7` として確定。
- GUIFIX06（波形とプレビューの横軸整合、ラベル右寄せ）の実装を統合。

---

## 進捗メモ（2026-03-23 / セキュリティ実装 SEC01・SEC02 完了）

- リポジトリ全体の反映版は `Ver 0.3.5.6` を維持。
- 対象: 実装リストSEC01（フェーズ1）、実装リストSEC02（フェーズ1〜4）
- 完了内容（要点）:
  - **SEC01**:
    - TEXTの絶対文字数上限（5000文字）制約を導入し、超過時は即時エラー停止
    - WAVの絶対再生時間上限（15分）制約を導入し、超過時は即時エラー停止
    - VMDの生成フレーム数上限（22000フレーム）制約を導入し、超過時は出力前エラー停止
  - **SEC02**:
    - TEXT内の異常制御文字（5文字以上）、規定長超過行（500/2000文字）、記号長大行（300文字）のエラー検証機能を追加
    - 絵文字関連フォーマット文字（ZWJ等）をエラーカウントから除外するホワイトリスト処理を追加（自動テスト済）
    - TEXT読込時の文字コードフォールバック（UTF-8 → Shift_JIS → UTF-16）を追加
    - WAV読み込み時の非対応フォーマット（PCM以外）や破損エラーの表示をユーザー向けへ改善
    - VMD保存時のファイル同名上書き確認ダイアログ（Yes/No）を追加

---

## 進捗メモ（2026-03-23 / GUIFIX06 横軸整合完了）

- 対象: 実装リストGUIFIX06（フェーズ1〜10）
- 完了内容（要点）:
  - **横軸基準の一本化**: Matplotlib の Axes（実プロットエリア）を X軸の正基準に固定し、PreviewArea がその物理座標を動的に模倣する構造を実装。
  - **同期経路の整備**: `draw_event` / `resize_event` / `splitterMoved` / `Pan` 等のあらゆる再レイアウト契機で、最新の基準矩形を伝播・再適用する経路を `MainWindow` に集約。
  - **初期状態の整合**: データ未ロード時でも Axes の枠線位置を正しく取得し、プレビュー側のグリッドと一致させるよう修正（Phase 9）。
  - **視認性向上**: 母音ラベル（あ、い...）を右寄せ表示に変更し、ウィンドウ幅に関わらず常にグリッド（表）のすぐ左隣に隣接するよう改善（Phase 10）。
  - **副作用の抑制**: 既存の秒ベース同期（ViewSync）への影響を最小限に抑え、ピクセル投影の基点のみを波形側へ動的に吸着させる方式を採用。

---

## 進捗メモ（2026-03-22 / リリース同期）

- リポジトリ全体の反映版を `Ver 0.3.5.7` としてリリース同期
- MS8D-2（共有ビューポート / Zoom・Pan / フレーム目盛り / パス表示拡張）反映状態を含めて、現作業ツリーを確定対象とする。
- 追加修正として、通常の Zoom 操作時に viewport 左端が 0.0 秒へ戻る不一致を補正し、現在 viewport の中心を保持した Zoom に統一した。

---

## 進捗メモ（2026-03-21 / MS8B 実装前固定）

- MS8B は実装開始前。ここでは実装前仕様・責務境界・完了条件のみを固定し、完了扱いにはしない。
- 固定済み（実装前）要点:
  - 目的: Preview Area の静止表示導入（右カラム下段、5段固定、波形とは別ウィジェット）
  - 正本: `current_timing_plan.timeline` を Preview の元データとして共用し、二重管理しない
  - 責務: `main_window.py`（司令塔）/ `preview_transform.py`（整形専用）/ `preview_area.py`（描画専用）へ分離
  - クリア基準: 失敗時だけでなく「解析結果無効化時全体」を対象にする
  - silent restore: `suppress_warning=True` は通常破壊的クリア導線と分離し、復元後 `current_timing_plan` から再構成する
- MS8B フェーズ分解（実装前整理）:
  - フェーズ1: 現状導線と組み込み位置の確定
  - フェーズ2: Preview 用データ契約の固定
  - フェーズ3: Preview 整形責務の導入準備
  - フェーズ4: Preview 描画責務の導入準備
  - フェーズ5: `main_window.py` の受け渡し責務整理
  - フェーズ6: Preview クリア / 無効化導線の整理
  - フェーズ7: `suppress_warning=True` 復元導線の扱い固定
  - フェーズ8: UI 組み込み成立条件の確認
  - フェーズ9: スコープ逸脱防止の最終固定

---

## 進捗メモ（2026-03-21 / MS8B 実装完了）

- MS8B フェーズ1〜9を実装・確認し、Preview Area 静止表示導入を完了扱いとした。
- 反映済み（コード実体）:
  - 右カラム下段へ `PreviewArea` を組み込み（波形とは別ウィジェット）
  - `preview_transform.py` で `timeline -> PreviewData` 整形責務を分離
  - `main_window.py` で `current_timing_plan.timeline` を正本にした受け渡し導線を接続
  - 解析結果無効化入口で Preview クリア導線を統一（失敗時限定ではない）
  - `suppress_warning=True` 復元時の Preview 再構成整合を反映（独立キャッシュなし）
- 非対象を維持（MS8B 時点）:
  - 再生同期 / 再生中カーソル / 共通カーソル線 / Play/Stop 実機能 / Zoom / スクラブ / 設定永続化 などは未着手
- 責務境界:
  - `main_window.py`（受け取り・保持・受け渡し制御）
  - `preview_transform.py`（整形）
  - `preview_area.py`（描画）
  - `waveform_view.py` / `pipeline.py` は責務変更なし

---

## MS7 方針固定（フェーズ7）

- 修正優先順位:
  1. 保存前パス確認
  2. 履歴再読込の安全確認
  3. 読込入口の事前パス確認
  4. 例外経路の復帰揃え
- 修正範囲:
  - `src/gui/main_window.py` の局所修正に限定
  - `src/app_io/` 導入や I/O 層の本格分離は MS7 対象外
- 運用原則:
  - 問題がなければ変更しない
  - 新機能追加や大規模設計変更に進まない

---

## MS7 完了判定観点（フェーズ8）

- TEXT:
  - 非存在/UTF-8不可/空内容/有効文字なしで安全に警告中断できる
- WAV:
  - 非存在/解析不能/プレビュー不能で安全に中断し、表示復帰できる
- 保存:
  - `.vmd` 補完と未解析出力禁止を維持し、保存失敗後も再試行可能
- 履歴:
  - 壊れた履歴値でクラッシュせず、失敗時に該当履歴除去とメニュー更新が行われる
- 例外:
  - 想定外例外でも GUI 警告へ落ち、状態が不整合のまま残らない

---

## 推奨実装順

1. MS1 画面骨格整理  
2. MS2 読込エラー統一  
3. MS3 波形確認性向上  
4. MS4 実行中状態の可視化  
5. MS5 利便性設定追加①  
6. MS6 利便性設定追加②  
7. MS6B 同名対応ファイルの自動補完読込  
8. MS7 入出力安全性点検  
9. MS8A GUI再構成基盤（完了）
10. MS8B Preview Area 静止表示導入（完了）
11. MS8C 再生基盤導入（完了）
12. MS8D-2 表示詳細化（改訂）（完了）
13. MS9 GUI整備（次段階）
14. MS10 多言語化・設定永続化
15. MS11 出力品質拡張

---

## 補足整理

### GUI整備フェーズ

- MS1 画面骨格整理
- MS2 読込エラー統一
- MS3 波形確認性向上
- MS4 実行中状態の可視化
- MS5 利便性設定追加①
- MS6 利便性設定追加②
- MS6B 同名対応ファイルの自動補完読込
- MS8A GUI再構成基盤（完了）
- MS8B Preview Area 静止表示導入（完了）
- MS8C 再生基盤導入（完了）
- MS8D-2 表示詳細化（改訂）（完了）
- MS9 GUI整備

### 品質確認フェーズ

- MS7 入出力安全性点検

### 機能拡張フェーズ

- MS10 多言語化・設定永続化
- MS11 出力品質拡張

---

## 段階的実装の意図

- 前半は GUI層・表示層・設定層の整理に限定する
- 処理ロジック変更を伴う項目は後半へ分離する
- 既存の内部データ構造や処理導線への影響を最小化する
- 開発途中でコード責務が混ざらない状態を維持する

---

## 追記メモ（2026-03-21 / MS8C 完了）

- 対象: MS8C フェーズ1〜10
- 完了内容（要点）:
  - `playback_controller.py` / `view_sync.py` を追加し、実 WAV 再生と秒ベース共通位置同期の基盤を導入
  - `main_window.py` で `controller -> view_sync -> waveform/preview/status` の配布経路を接続
  - Play/Stop を action state に統合（Play は処理実行後のみ有効、Stop は再生中のみ有効）
  - 再生開始 0.0 秒起点、停止/終了/無効化で 0.0 秒へ戻す遷移を統一
  - `WaveformView` / `PreviewArea` に再生カーソル表示/クリア導線を接続
  - ステータス欄に再生中フレーム表示（30fps派生）を追加し、既存優先順位を維持
  - 解析結果無効化導線と既存入口（再読込・失敗・入力不足・再解析待ち・silent restore）で再生状態取り残しを解消
- 非対象（MS8C 時点で未実装のまま維持）:
  - Zoom / スクラブ / 手動シーク / クリック移動 / 表示詳細化
  - `pipeline.py` / `writer.py` / `preview_transform.py` / `whisper_timing.py` の仕様変更

---

## 追記メモ（2026-03-22 / MS8D-2 完了）

- 対象: MS8D-2 フェーズ1〜12
- 完了内容（要点）:
  - `view_sync.py` を共有表示状態ハブへ拡張し、共有可視範囲（秒ベース）を導入
  - `main_window.py` に Zoom/Pan/viewport 初期化導線を統合し、WAV 読込成功/失敗/無効化で表示範囲を安全に復帰
  - `waveform_view.py` を可視範囲ベース描画へ移行し、横軸をフレーム表記（30fps）へ変更
  - `preview_area.py` を可視範囲ベース描画へ移行し、可視範囲クリップ表示とフレーム目盛りを追加
  - Zoom を Operation Panel ボタンと View メニュー action の両方へ接続し、有効/無効判定を同期
  - Pan 操作を導入し、波形/Preview を同一可視範囲で同期移動可能化（境界クランプ含む）
  - TEXT/WAV パス表示を中間省略 + tooltip フルパスへ拡張
- 非対象（維持）:
  - `pipeline.py` / `writer.py` / `whisper_timing.py` の仕様変更
  - `preview_transform.py` への UI 状態（Zoom/Pan/viewport）責務追加
---

## 2026-03-22 追記 / MS9 完了状態と MS9-2 への接続

- MS9 本体は、GUI 整備マイルストーンとして実装完了扱いとする。
- 実装済み範囲:
  - `main_window.py` の GUI 構築責務分散
  - 左情報表示パネル化
  - 右表示領域コンテナ化
  - `QSplitter` による左右分割
  - `OperationPanel` の 3 グループ整理
  - `StatusPanel` の 2 領域化
  - 文字列管理受け皿
  - テーマ切替導線と Qt / 描画側テーマ追従
  - `Amp` 削除
  - 分割比率 / テーマ設定受け皿
  - 分析終了時通知音
- MS9 追加改修として、右表示領域共通の横スクロールバーを実装済みとする。
  - 第1段階: バー設置 + shared viewport 基本連動
  - 第2段階: 無効化条件・Zoom 連動・Scrollbar 状態調整
  - 追加修正: PreviewArea の viewport 全長解釈補正、Zoom 端部クランプ時の体感改善、PreviewArea マウス座標型修正
- ただし、見た目最終調整・余白最終調整・実機 UX の微修正は次セッション `MS9-2` で扱う。

## 実装前メモ / MS9-2

- 位置づけ:
  - MS9 本体完了後の外観・UX 微調整セッション
- 主対象:
  - 右表示領域共通スクロールバーの見た目調整
  - 余白 / 高さ / splitter リサイズ時の違和感低減
  - テーマとの見た目馴染ませの微修正
  - 端部近傍 UX の実機確認を踏まえた軽微調整
- 非対象:
  - shared viewport 正本責務の変更
  - 再生制御仕様変更
  - 設定永続化本格実装
- ※上記は実装前整理メモであり、到達点は後続の「MS9-2 完了」節を正とする。

## 2026-03-22 追記 / MS9-2 完了

- MS9-2 は、MS9 本体と右表示領域共通横スクロールバー追加後の見た目・余白・初期表示バランス調整として完了扱いとする。
- 反映済み（コード実体）:
  - 初期ウィンドウサイズを `1270x714`、最小サイズを `720x405` へ調整
  - 中央 `QSplitter` の初期比率を `左3 : 右7` とし、表示確定後の再適用で初期実効比率を安定化
  - GUI 主要部へ `11pt` 基準フォントと 4〜6px 基準の余白を反映
  - 操作ボタンの横長化を抑制し、`TXT読込` / `WAV読込` / `処理実行` の改行を解消
  - 操作ボタンの assets アイコン差し替えを反映し、広い幅ではボタングループが左詰めで並ぶよう再配置
  - `処理実行` / `VMD保存` ボタンの高さを統一
  - モーフ上限値入力欄を短幅固定のまま維持し、内蔵スピンボタンを廃止して独立した `-` / `+` ボタンへ置換
  - モーフ上限値入力まわりはダーク / ライト両テーマで視認できる局所スタイルへ整理
- 非対象を維持:
  - shared viewport / playback / zoom / scrollbar の責務や挙動変更
  - 設定永続化
  - 多言語化本実装
  - 波形 / Preview 描画ロジックの再設計
## 2026-03-27 / MS11-2_FIX02 実装完了メモ

- 対象: MS11-2_FIX02 writer 後段ゼロ縮退抑止
- 実装反映:
  - `src/vmd_writer/writer.py` に、発話イベント範囲ベースの `protected_event_ranges` を追加
  - short open / short morph pulse 抑制に、MS11-2 shape だけでなくイベント全域保護の条件を追加
  - 近接イベントおよび fallback 混在時に、rise / top / fall の有効寄与が suppression で過剰に失われないよう補正
  - FIX01 で導入した許容外非ゼロ除去と不要ゼロ prune の意図を維持したまま、肩消失が起きにくいよう後段条件を調整
  - `tests/test_vmd_writer_zero_guard.py` に、short fallback 維持・近接イベント共存・FIX01 意図維持の回帰テストを追加
- 到達状態:
  - 発話イベント内部で、頂点だけ残して肩が消えるゼロ縮退が起きにくくなった
  - MS11-2 正規 shape と legacy fallback の近接ケースでも、後段 suppression による過剰 0 化を抑制できる構造になった
  - FIX01 の無音区間非ゼロ除去意図は維持されている
  - writer 系テスト 33 件が通過している
- スコープ外として維持:
  - 多ポイント台形
  - 上辺複数点対応
  - より高度な平滑化
  - `pipeline.py` の構造変更
  - GUI / 波形 / 再生ロジック改修

---

## 2026-03-27 / MS11-2_FIX01 実装完了メモ

- 対象: MS11-2_FIX01 writer 正規化整合修正
- 実装反映:
  - `src/vmd_writer/writer.py` に、許容非ゼロ範囲と維持すべき境界ゼロの文脈情報を導入
  - MS11-2 保護範囲を `start_frame`〜`end_frame` 全体へ拡張
  - 許容外区間の非ゼロ除去と、不要な中間 `0.0` キーの prune を追加
  - `tests/test_vmd_writer_zero_guard.py` に、不要ゼロ整理と許容外非ゼロ除去の回帰確認を追加
- 到達状態:
  - 発話区間内に `0.0` キーだけが不自然に残る状態を主要ケースで改善
  - 無音区間に残る不要な非ゼロキーを writer 後段で落とせる構造になった
  - 開始 / 終了ゼロと collision 回避ゼロは維持される
- スコープ外として維持:
  - 多ポイント台形
  - 上辺複数点対応
  - より高度な平滑化
  - `pipeline.py` の構造変更
  - GUI / 波形 / 再生ロジック改修

---
## 2026-04-01 / MS11-9 残課題整理・文書同期メモ

- 対象: MS11-9 系の区切り整理
- 文書反映:
  - `docs/MS11-9_Remaining_Issues.md` を新規追加し、MS11-9 / 9B / 9C / 9D / 9D-2 / 9D-3 / 9D-4 / 9D-5 / 9D-6 を経た現時点の残課題を正本として整理
  - `docs/MS11_MS12_Roadmap_and_Scope_Split.md` に、MS11-9D-2〜MS11-9D-6 の実装到達状態と現在の残課題参照先を同期
  - `docs/Version_Control.md` に、今回の残課題整理と文書同期ログを追加
- 現在地整理:
  - Preview trapezoid / multi-point alignment、closing hold / softness、same-vowel / cross-vowel の speech-internal bridge、zero-run span、top-end shaping、continuity floor、same-vowel burst smoothing は現ワークスペースへ反映済み
  - 一方で、実データ上では residual same-vowel burst、residual cross-vowel full closure、top-end shaping の取りこぼし、暫定閾値依存、observation 契約の混雑が残課題として存在する
- 今回残課題として明示した主項目:
  - same-vowel 連音でも急な開閉が残る箇所
  - cross-vowel でも発話中の完全閉口が残る箇所
  - `peak_end_value` / RMS 依存の top-end shaping の限界
  - `0.1` floor / `0.2` low-positive threshold / `2 event / 2 frame` 上限の暫定性
  - `PeakValueObservation` 契約の混雑
- スコープ外として維持:
  - MS12
  - final closing 系の再設計
  - RMS 閾値全体の全面見直し

---
## 2026-04-01 / Ver 0.3.6.5 同期メモ

- 対象: MS11-9 系拡張反映後の版同期
- 同期内容:
  - `README.md` / `pyproject.toml` / `docs/Specification_Prompt_v3.md` / `docs/MS11_MS12_Roadmap_and_Scope_Split.md` / `docs/MS11-9_Remaining_Issues.md` / `docs/repo_milestone.md` / `docs/Version_Control.md` を `Ver 0.3.6.5` 基準へ同期
  - MS11-9D から MS11-9D-6 までの speech-internal lip-motion 改善を、現行 workspace の反映済み到達として整理
  - MS11-9 系の残課題を `docs/MS11-9_Remaining_Issues.md` へ切り出し、今後の改善対象を明確化
  - リポジトリ全体の反映版を `Ver 0.3.6.5` として確定
- 確認状態:
  - same-vowel / cross-vowel bridge、zero-run span、top-end shaping、continuity floor、same-vowel burst smoothing は現 workspace に反映済み
  - 残課題は residual same-vowel burst、residual cross-vowel full closure、暫定閾値、observation 契約整理として別文書化済み
  - MS12 と final closing 系再設計は引き続き本同期の対象外

---
## 2026-04-01 / MS11-9D 初回実装反映メモ

- 対象: MS11-9D Speech-internal micro-gap bridging
- 実装反映:
  - `src/core/pipeline.py` の `PeakValueObservation` を最小拡張し、same-vowel micro-gap bridge 候補を `observations` 側で保持する導線を追加
  - bridge 候補の初回条件は `same-vowel only` / `1 frame max` / `reason in {no_peak_in_window, below_rel_threshold}` に限定
  - `timeline` は canonical writer input のまま維持し、`peak_value` の直接上書きは行わない
  - `src/vmd_writer/writer.py` は `timeline + observations` を参照し、bridgeable zero event を独立 grouping 入力から外して既存 same-vowel multi-point envelope 側へ寄せる
  - `src/gui/preview_transform.py` と `src/gui/main_window.py` も同じ `timeline + observations` handoff に揃え、Preview / export の semantics を一致させる
  - `tests/test_pipeline_peak_values.py` / `tests/test_vmd_writer_intervals.py` / `tests/test_preview_transform.py` / `tests/test_main_window_closing_softness.py` / `tests/test_pipeline_and_vmd.py` を更新し、候補判定・writer bridge・Preview/export handoff の回帰を追加
- 確認状態:
  - 初回 MS11-9D は same-vowel の狭い zero micro-gap に限定して導入済み
  - `observations` が無い経路では bridge 無効となり、現行互換を維持する
  - `69 tests` が通過
- スコープ外として維持:
  - cross-vowel bridge
  - 2 frame 以上の gap 対応
  - `below_abs_threshold` / `global_peak_zero` / `rms_unavailable` の救済拡張
  - GUI パラメータ追加
  - RMS 再調整
  - 無音判定ロジック全体の再設計
  - MS12

---
## 2026-04-01 / MS11-9D-2 実装前整理メモ

- 対象: MS11-9D-2 Cross-vowel transition bridging
- 実装前固定:
  - cross-vowel は same-vowel の単純拡張として扱わず、transition bridging として別ルールで扱う
  - `timeline` は canonical writer input のまま維持し、bridge 候補の正本は引き続き `observations` 側に置く
  - 初回対象は `cross-vowel only` / `1 frame max` / `reason in {no_peak_in_window, below_rel_threshold}`
  - zero event の `peak_value` を直接上書きせず、前母音の fall と次母音の rise を少し重ねる transition shape を優先する
  - GUI 追加なし、Preview / export は同じ `timeline + observations` semantics で揃える
- 主変更想定:
  - `src/core/pipeline.py`
  - `src/vmd_writer/writer.py`
  - `src/gui/preview_transform.py`
  - `src/gui/main_window.py`
- 最低限の確認観点:
  - cross-vowel candidate 判定
  - zero event を独立 peak として生成しないこと
  - 前母音の完全閉口前に次母音の rise が始まること
  - Preview / export 整合
  - observations 無し経路の現行互換

---
