# MS24 Block Breakdown

## 1. 文書情報

- 文書名: MS24 Block Breakdown
- 対象マイルストーン: MS24 Whisper Model Selection
- 作成日: 2026-08-20
- 状態: MS24-B1/B2/B3/B4/B5/B6実装済み・MS24-B6自動検証済み・ユーザー手動GUI確認済み・MS24 Closeout A判定済みのBlock Breakdown
- 対象ブランチ: `feature/MS23-implementation`
- 前提となる完了状態: MS23 Closeout A
- 実装状態: MS24-B1は`eafdc16`、MS24-B2は`b011b37`、MS24-B3は`a27a26f`で実装済み。MS24-B4は`0a119cb`、MS24-B5は`78172d9`、MS24-B6は`1f1aff2`で実装・自動検証・ユーザー手動GUI確認まで完了した。MS24-B7はintegration regression・static package audit・利用者向け文書同期・Python 3.14.3 development / acceptance gateを実施済み。MS24 Closeout Aは2026-08-28に判定済み
- 本文書の権限: 計画・責務分割・受け入れ条件の定義、および各Blockの到達状態記録。production code、test code、GUI、依存関係、runtime user dataは変更しない
- 2026-08-21同期: ユーザー承認済みの「候補選択 → Download & Verify → Apply and Re-analyze」二段階切替を正本とし、候補選択だけではactive model・既存解析を変更しない。selected candidateとactive model identityは別々に永続化し、未Apply候補は再起動後も候補表示だけ、active未配置・未検証時は自動download / fallbackなしとする。manifestはsource / frozenの`src.core`でruntime解決し、installed packageは`core/whisper_models.json`のpackage-data配置マッピングを静的確認する
- 2026-08-22同期: B1のmanifest、catalog、verified-local bytes loader、package/spec境界は`eafdc16`で実装済みとして扱う。B2は`whisper_models_dir`、artifact availability、canonical `.part` cleanup、preflight、atomic promote、permit検証付きfilesystem deleteを所有し、B3はselected / active identityとUIを所有する。B2のpreflightはユーザー確認後かつdownload開始前、B4のdownload workerはB2のfilesystem APIだけを使用し、B5だけがownership解除後の単回permitを発行する
- 2026-08-22メインエージェント再チェック同期: promoteはcaller-supplied pathを受け取らずmodel key由来のcanonical `.part`だけを扱う。保存先rootと既存親要素のsymlink / junction / Windows reparse point / network redirectはB2が拒否し、permitはB5専用issuer boundaryのopaque capabilityとする。B2 failure codeはB4/B5/B6へdiagnostic detailとして引き継ぎ、P1 / P2 / P3は残存しない
- 2026-08-23実装状態同期: MS24-B2を`b011b37 Implement MS24-B2 model storage core`で実装済みとして記録し、B2 / B1 / SettingsStore関連のtargeted baseline 40 passed、2 skipped（Windows symlink capability依存）を確認した。MS24-B3 Implementation Planは作成済み・P2/P3補正済みで、次工程はrouting同期後のfresh read-only pre-implementation checkとする。B3以降のproduction code、test code、GUI、runtime user data、実MMD確認は未実施のまま維持する。
- 2026-08-23 MS24-B3 P2解消同期: B3 plan / Block Breakdownへ、startup resolver / availability worker testでtemporaryな`whisper_models_dir`またはtemporary B2 store/rootを明示注入し、repository既定の`models` rootとroot runtime user dataを読まない契約を追加した。temporary SettingsStore pathだけではテスト隔離の証拠にしない。production code、test code、GUI、依存関係、runtime user dataは変更していない。
- 2026-08-23 MS24-B3 P2/P3解消同期: 明示設定された不正rootの`StorageRootResolution`失敗時に既定`models`へfallbackせず、store / worker / root作成を行わず、B2 failure code / detailをfailed stateへ投影する契約を追加した。B3関連回帰へ`tests/test_whisper_timing.py`と`tests/test_ms19_b3_textless_pipeline.py`を追加した。production code、test code、GUI、依存関係、runtime user dataは変更していない。
- 2026-08-23 MS24-B4 plan P2/P3解消同期: B4の明示保存先変更をWhisper管理UIのlocal-only DirDialog操作として追加し、B2 resolve・設定保存・new-root scan・no-fallbackを固定した。download/delete/ownership providerはUI thread外のmanagement workerへ固定し、完了後のavailability scanはcontrollerの再利用可能な`start_whisper_availability_rescan()`へ委譲した。HTTP redirectは全面拒否とした。B4 standaloneのblocked/test-only Delete seamと、B5連携後のproduction Delete成功を受け入れ境界として分離した。MS24-B4 planの索引を追加し、B3のcommit待ち表記を`a27a26f`へ更新した。production code、test code、GUI実装、依存関係、runtime user dataは変更していない。
- 2026-08-23 MS24-B4再チェックP2/P3解消同期: 保存先変更は`whisper_models_dir`だけを渡すpartial saveを禁止し、現在の全設定を保持する安全なmerge保存とtheme、window、recent path、selected / active identityの回帰を計画へ追加した。B2内部の対象model検証scanと、controllerの再利用可能な`start_whisper_availability_rescan()`による全体availability projectionを分離した。Index、Roadmap、repo milestone、Version Control、B3 plan、Block Breakdownの現在地をB3コミット済み・B4 plan作成済み・B4 fresh read-only check待ちへ同期した。production code、test code、GUI実装、依存関係、runtime user dataは変更していない。
- 2026-08-23 MS24-B4実装プラン再チェックP2/P3解消同期: `SettingsStore`のmanaged persistenceを通常アプリの保存入口として明記し、runtime INIの直接編集・コピー・stageは禁止した。`system` / `light` / `dark` themeのround-tripと、`whisper_models_dir`だけを置換する全設定merge回帰をB4対象へ追加し、`src/core/settings_store.py`と`tests/test_settings_store.py`を変更候補へ含めた。promote成功後の全体availability projectionはcontrollerの再利用可能な`start_whisper_availability_rescan()`だけを入口とし、Python 3.13.xの実行ファイルpath・version・process exit code記録をcompatibility gateへ追加した。production code、test code、GUI、依存関係、runtime user dataは変更していない。次工程は補正後MS24-B4 planのfresh read-only pre-implementation checkである。
- 2026-08-23 MS24-B3 P2解消同期: B2 `StorageRootResolution`の正本fieldを`failure_code` / `message`へ統一し、B3はfailure codeから安全なユーザー向け通知を生成する一方、message由来のraw例外・絶対パスを通常UIへ表示せず診断・handoff用detailへ限定する契約と回帰を追加した。production code、test code、GUI、依存関係、runtime user dataは変更していない。次工程は補正後MS24-B3のfresh read-only pre-implementation checkとする。
- 2026-08-23 MS24-B3実装・検証状態同期: `SettingsStore`のselected / active identity、`UiState`のWhisper selection state、RightPane専用Whisperモデルtab、startup projection、local-only availability scan worker、Busy / stale / shutdown guard、safe failure noticeを実装した。B3追加・関連の限定検証、full suite `846 passed, 2 skipped`、`compileall src tests`、`git diff --check`はprocess exit code `0`で完了した。ユーザーから手動GUI確認完了・問題なしの報告を受領したが、これはCodex自身のGUI実行結果ではない。実network、実model、実Whisper解析、実MMD確認は未実施で、B4/B5/MS26へ引き継ぐ。stage / commit / push等は未実施である。
- 2026-08-24 MS24-B4実装・検証状態同期: 公式manifest URL限定のdownloader、Content-Length / exact size / redirect / short read / overrun / cancel / cleanup検証、専用management worker、Download & Verify / Cancel / Delete / 保存先変更UI、managed settings merge、再利用可能な`start_whisper_availability_rescan()`、B5 permit未接続時のDelete blocked境界を実装した。全pytestは`860 passed, 2 skipped, 77 subtests passed`、`compileall src tests`、`git diff --check`はprocess exit code `0`で完了した。ユーザーからB4手動GUI確認完了・問題なしの報告を受領したが、これはCodex自身のGUI実行結果ではない。Python 3.13.x互換性、B5 ownership provider接続後の実production Delete、実MMD確認、MS27 package / release readinessは未完了である。stage / commit / push等は未実施である。
- 2026-08-25 MS24-B5実装・検証状態同期: verified-local model request、single-active runtime、Apply / candidate commit-reject、TEXT + 音声・voice-onlyのmodel identity伝播、model-aware rollback、B5 production ownership permit、delete / storage root change / shutdown lifecycleを実装した。解析時の暗黙downloadを禁止し、word timestamp / segment fallback、MS23固定morph・Latin profile・preset・diagnostics・fingerprint契約を維持した。全pytestは`872 passed, 2 skipped`、`compileall -q src`、`git diff --check`はprocess exit code `0`で完了した。ユーザーからB5手動GUI確認完了・問題なしの報告を受領したが、これはCodex自身のGUI実行結果ではない。Python 3.13.x互換性確認、実MMD確認、MS27 package / release readinessは未確認または別工程である。stage / commit / push等は未実施である。
- 2026-08-26 MS24-B6実装・検証状態同期: `WhisperDiagnosticsSummary`、selected / active / loaded / analysis identityの分離、package version / gate status、safe failure分類、projection generation、Info / report / RightPaneの同一snapshot投影、model-aware rollbackの診断連携を実装した。MS23固定morph・Latin profile・preset・diagnostics・fingerprint契約、暗黙download禁止、依存値、runtime user data境界を維持した。全pytestは`881 passed, 2 skipped`、`compileall -q src tests`、`git diff --check`はprocess exit code `0`で完了した。ユーザーからB6手動GUI確認通過・問題なしの報告を受領したが、これはCodex自身のGUI実行結果ではない。Python 3.13.x互換性確認は未実施、実MMD確認はMS26、MS27 package / release readinessはMS27へ引き継ぐ。B6のproduction code・test code変更は`1f1aff2`としてcommit済みであり、B6のstage / commitは完了している。MS24-B7 Implementation Planは作成済みである。

## 2. 参照した正本文書と現行ベースライン

### 2.1 正本文書

- `docs/MS17_and_Beyond_Index.md`
- `docs/MS20_and_Beyond_Index.md`
- `docs/MS20_and_Beyond_Roadmap.md`
- `docs/Pipeline_Data_Contract_Specification.md`
- `docs/GUI_State_Theme_Specification.md`
- `docs/Error_Handling_Specification.md`
- `docs/Implementation_Plan/MS23_Block_Breakdown.md`
- `docs/Implementation_Plan/MS23-B7_Implementation_Plan.md`
- `README.md`
- `pyproject.toml`
- `requirements.txt`

### 2.2 現行実装の確認対象

- `src/core/whisper_timing.py`
- `src/core/pipeline.py`
- `src/core/settings_store.py`
- `src/core/output_diagnostics.py`
- `src/core/diagnostic_report.py`
- `src/gui_wx/analysis_worker.py`
- `src/gui_wx/analysis_rollback.py`
- `src/gui_wx/app_controller.py`
- `src/gui_wx/main_frame.py`
- `src/gui_wx/right_pane.py`
- `src/gui_wx/ui_state.py`
- `src/gui_wx/output_diagnostics_adapter.py`
- `src/gui_wx/worker_state.py`
- `src/gui_wx/audio_worker.py`
- `MMD_AutoLipTool.spec`
- `docs/Release_Package_Manifest.md`
- `.gitignore`

### 2.3 現行ベースラインの事実

- `openai-whisper==20250625` が `pyproject.toml` に固定されている。
- `src/core/whisper_timing.py` の既定モデルは `small` である。
- 現行の `_load_whisper_model()` は `whisper.load_model(model_name)` を呼ぶため、Whisperライブラリの既定 `download_root` と自動取得挙動を直接受ける。
- `AnalysisWorker` は `whisper_model_name` を受け取れるが、現行の `MainFrame` からの生成時には明示的に渡されず、実質的に `small` 固定である。
- voice-onlyだけでなく、TEXT + 音声でも `AnalysisWorker -> build_vowel_timing_plan() -> recognize_audio_timing()` を通り、Whisper timingが実行される。
- voice-onlyの `analysis_pending_rebuild` は、現行では書き起こし編集時に保持済みWhisper timingを再利用するが、rebuild reasonとmodel identityをまだ保持していない。
- 解析失敗時のrollback parameter snapshotはWhisper model identityをまだ保持せず、失敗分類によって旧解析結果の復元を禁止する契約もない。
- 現行の `_load_whisper_model()` は `lru_cache(maxsize=2)` であり、single-active model ownership、明示eviction / unload、削除前のownership解除は未実装である。
- `SettingsStore` には`whisper_models_dir`、`selected_whisper_model_key`、`active_whisper_model_key`、`active_whisper_manifest_identity`がB3で追加済みである。B4は既存keyの保存先変更と新rootへの再projectionを使用し、新しい設定keyを追加しない。
- 右ペインにはInfo、Warning、選択イベント、プリセット、モデルプロファイルの拡張可能なタブ構成がある。
- 設定メニューの設定ダイアログ入口は現時点でStubであり、MS24の選択UIをそこへ依存すると新規設定ダイアログ全体の実装へ範囲が広がる。
- `MMD_AutoLipTool.spec` はWhisperのPythonコードと関連データを同梱するが、モデル重みを同梱する設定ではない。
- 配布manifestはPyInstaller onefileを前提とし、モデル重みの外部管理方針をまだ定義していない。
- 現行のsource / PyInstaller論理namespaceは`src.core`、setuptoolsのpackage discovery結果は`core`である。manifestはsource / frozenではpackage-relativeにruntime解決し、installed packageでは`core/whisper_models.json`のpackage-data配置マッピングを静的確認する。既存アプリ全体の`src.core` / `core` import統一とinstalled `core.whisper_models` runtime importはB1の対象にしない。
- `presets.json`、`profiles.json`、`MMD_AutoLipTool.ini` はroot限定のruntime user dataであり、計画確認中に直接編集・コピー・stageしない。MS24-B4の通常アプリ動作だけは、保存先変更のため既存`SettingsStore` managed persistenceを介して読み込み・atomic保存し、テストはtemporary settings pathを使用する。
- 現行 `.venv` の実測はPython 3.14.3、`openai-whisper==20250625`、PyTorch 2.13.0+cpu、PyInstaller 6.19.0である。本リポジトリの開発・受入対象はPython 3.14.3とし、Python 3.11 / 3.12は今回の受入ゲートに含めず未検証として記録する。

## 3. 公式Whisper調査結果

調査日: 2026-08-20

### 3.1 公開版とGitHub mainの扱い

- 公式PyPIの最新リリースは `20250625` であり、現行の依存固定値と一致する。
- 公式GitHub `main` の `whisper/version.py` も `20250625` である。ただし、release tag以後にもmainの変更が存在し得るため、GitHub `main` や未タグcommitを実行依存へ直接採用しない。
- `20250625` には `torch.load(weights_only=True)`、DTW device修正、Python 3.13 CI、PEP 621移行などの変更が含まれる。MS24ではこれらを理由に無条件の依存更新を行わず、実装前の互換性ゲートで公開版・PyTorch・PyInstaller・現行word timestamp処理を照合する。

### 3.2 対象モデル

- Roadmapで指定された選択肢は `small`、`medium`、`turbo` とする。
- 日本語音声の既存契約に従い、`.en`モデルは選択肢に含めない。
- 公式READMEのモデル表では、`small`、`medium`、`turbo`はいずれも多言語モデルであり、概算VRAMはそれぞれ約2 GB、約5 GB、約6 GBと説明されている。実際の必要量はCPU/GPU、PyTorch、音声長、他の常駐ソフトウェアで変動するため、GUIには「目安」として表示する。
- 公式READMEでは現在のCLI例の既定モデルが `turbo` になっているが、MMD AutoLipToolは既存アプリの既定値 `small` を維持する。公式CLIの既定値をアプリへ自動反映しない。

### 3.3 公式取得・検証契約

- 公式WhisperのモデルURLにはSHA256相当の値が埋め込まれており、公式loaderもダウンロード後にSHA256を検証する。
- 公式loaderは、モデル名を直接渡すと未配置時に既定cacheまたは指定 `download_root` へ取得を試みる。したがって、MS24では解析経路から未配置モデルを直接 `load_model(model_name)` へ渡さない。
- 解析時に公式model keyと `download_root` を直接 `load_model()` へ渡す方式は採用しない。verified判定後でも、検証とloadの間にファイルが消失・破損すると公式loaderが再downloadし得るため、ユーザー確認のない通信をTOCTOUで発生させる余地が残る。
- 解析loaderは、B2で生成された`VerifiedWhisperCheckpoint` DTOだけを受け取り、loader自身がpathを一度openしてsize / SHA256とfile identityを再検証し、その同一open handleからbytesへ束縛して、ネットワーク処理へ到達するコード経路を持たない専用adapterに固定する。
- checkpoint pathを公式loaderへ渡すだけではalignment headsが設定されず、検証とloadの間のpath再openによるTOCTOUも残るため、adapterは `whisper.__version__ == manifest.openai_whisper_version == 20250625` を確認し、同一open handleから束縛した検証済みbytesで構築したmodelへ公式model key対応のv20250625 alignment headsを設定する。
- alignment heads取得にWhisperのprivate APIを使用する依存を明示し、private symbol、key、値形式、`model.set_alignment_heads()`のいずれかが一致しない場合はfail closedする。Whisper依存更新時はこのprivate API契約とword timestamp回帰を再検証する。
- MS24のversioned manifestには、少なくとも次を固定する。
  - manifest schema version
  - `openai_whisper_version`
  - model key (`small` / `medium` / `turbo`)
  - official model URL
  - filename
  - SHA256
  - exact `size_bytes`
  - display name
  - multilingual / Japanese availability
  - approximate VRAM label
  - approximate relative speed label
- `size_bytes`は推測値や表示上の丸め値で埋めず、公式取得元のContent-Lengthまたは取得実体から検証して固定する。正確な値を確定できないモデルはdownload可能状態にしない。

### 3.4 依存更新の方針

- MS24の初期計画では `openai-whisper==20250625` を維持する。
- MS24のWhisper互換性受け入れ対象は、本リポジトリの現行開発環境であるPython 3.14.3に固定する。Python 3.11 / 3.12は今回の開発・受入ゲートに含めず、3.14.3の実測結果と混同しない形で未検証として記録する。
- `pyproject.toml` と `requirements.txt` のWhisper依存値を同期検証する。初期計画では両方とも変更せず、依存更新を採用する場合だけ同一公開版へ同期する。
- 新しいPyPI releaseが実装着手前に公開されていた場合だけ、別途次を確認する。
  - `turbo`名、モデルURL、SHA256、word-level timestamp、`load_model`引数の互換性
  - 現行PyTorch、Python 3.14.3、PyInstaller onefileとの互換性
  - 既存のTEXT + 音声およびvoice-only解析、segment fallback、Preview、VMD保存への回帰
  - `pyproject.toml` / `requirements.txt`同期、license、配布サイズへの影響
- 新しい公開版の採用、GitHub `main`直採用、PyTorchの同時更新は、互換性確認とユーザー承認なしに行わない。

参照した公式一次情報:

- [OpenAI Whisper PyPI](https://pypi.org/project/openai-whisper/)
- [OpenAI Whisper releases](https://github.com/openai/whisper/releases)
- [OpenAI Whisper README](https://github.com/openai/whisper/blob/main/README.md)
- [OpenAI Whisper version.py](https://raw.githubusercontent.com/openai/whisper/main/whisper/version.py)
- [OpenAI Whisper __init__.py](https://raw.githubusercontent.com/openai/whisper/main/whisper/__init__.py)
- [OpenAI Whisper CHANGELOG](https://github.com/openai/whisper/blob/main/CHANGELOG.md)

## 4. MS24の目的

現行コードでWhisper timingを使用するTEXT + 音声とvoice-onlyの全解析経路について、ユーザーが処理負荷・概算必要容量・推奨用途を確認したうえで、ローカルWhisperモデルを `small`、`medium`、`turbo` から選択できるようにする。選択値を設定、解析worker、pipeline、Info、診断レポートへ一貫して渡し、モデル未配置・ダウンロード中断・SHA256不一致・load失敗・メモリ不足でも、古い解析結果を誤ってVMD保存できない状態を維持する。

## 5. Block分割

### MS24-B1: Whisperモデル契約・versioned manifest・互換性ゲート

責務:

- Roadmapの `small` / `medium` / `turbo` 選択肢を厳密なcatalogとして定義する。
- 日本語音声で使用する多言語モデルだけを許可し、`.en`、未知のモデル名、任意URLを拒否する。
- `src/core/whisper_models.json` などのrepo内versioned manifestに公式URL、filename、SHA256、exact size、表示情報、Whisper package versionを固定する。
- `WhisperModelSpec`相当のUI非依存DTOとmanifest validatorを定義する。
- 現行 `openai-whisper==20250625` を基準に、manifestのモデルURL・SHA256・loader契約が一致することを実装前に検証する。
- 解析loaderを、`VerifiedWhisperCheckpoint` DTOだけを入力とし、loader自身が同一open handleで再検証して束縛したbytesをloadするネットワーク到達不能adapterとして定義する。公式model key + `download_root`、local path再openを解析時に使う方式は禁止する。
- adapterはv20250625のpackage / manifest version gateを通過した場合だけ、公式model key対応alignment headsをprivate APIから適用する。private API不一致、未知key、version不一致はfail closedする。
- verified checkpoint bytes load、alignment heads適用、word timestamp、segment fallback、network未到達をB1のversioned contract testへ固定する。
- model keyと表示名、VRAM目安、速度目安を分離し、表示文言を解析処理へ渡さない。
- manifest resourceは`__package__`に対するpackage-relative解決とし、source / PyInstaller onefile（`src.core`）でruntime検証する。installed packageはsetuptoolsの`core = ["whisper_models.json"]`から`core/whisper_models.json`へ対応するpackage-data配置を静的検証する。PyInstallerは`src/core/whisper_models.json`を展開先`src/core`へ追加し、installed `core.whisper_models` runtime importとinstalled entry point全体の既存namespace補修はB1へ持ち込まない。

依存: なし

主な対象候補:

- `src/core/whisper_models.py`
- `src/core/whisper_models.json`
- `src/core/whisper_model_loader.py`
- `src/core/__init__.py`（公開が必要な場合だけ）
- `pyproject.toml`（`[tool.setuptools.package-data] core = ["whisper_models.json"]`を追加。dependency値は変更せず、採用版変更時だけ別途承認対象）
- `requirements.txt`（read-onlyの依存整合確認。採用版変更時だけ別途承認対象）
- `MMD_AutoLipTool.spec`（`src/core/whisper_models.json`をdatasの展開先`src/core`へ追加。model weightsは追加しない）
- `tests/test_whisper_model_catalog.py`
- `tests/test_whisper_model_loader.py`
- `tests/test_whisper_timing.py`

受け入れ境界:

- manifestが不正、重複、SHA256不正、size未確定、非公式URL、`.en`モデルを含む場合はfail closedする。
- catalogの既定値は `small` とする。
- 解析loaderはverified local checkpoint以外を受け取らず、公式model key + `download_root`経路やその他の暗黙download経路を持たない。
- v20250625対応alignment headsとword timestamp回帰が確認できず、またはprivate API / version gateが不一致の場合はloadを開始しない。
- checkpoint open / streaming read中のI/O failureは`checkpoint_read_failed`へ分類し、bytes loader 0回・loaded handleなしでfail closedする。
- source / PyInstaller onefileの各runtime resource経路でmanifestを解決でき、installed packageでは`core/whisper_models.json`のpackage-data配置マッピングを確認できる。installed `core.whisper_models` runtime importと既存アプリ全体のinstalled entry point起動可否はB1の合否に含めない。
- B1はネットワークdownloadを実行しない。

### MS24-B2: モデル保存先・availability・整合性検証

責務:

- 既定保存先をfrozen実行時のexe隣接 `models` とする。
- source実行時は現行のアプリ配置境界に対応するローカル `models` を既定候補とし、テストでは一時ディレクトリを注入できるようにする。
- 既定保存先が存在しない場合は必要に応じて作成候補として扱う。書込不可の場合はB3/B4のUIから書込可能な保存先選択へ誘導する。
- `whisper_models_dir`を設定へ保存し、path validationとcanonical path生成をB2だけが所有する。runtime user dataとモデル重みをGit管理対象へしない。
- 保存先rootとnearest existing parentまでの既存各要素をcanonical化し、symlink、junction、Windows reparse point、network redirectを拒否してからdrive typeを検査する。これをB2のlocal-only境界とする。
- 各モデルについて、missing、partial、verified、サイズ不一致、SHA256不一致、読取失敗をartifact状態として区別する。`downloading`、`cancelled`、`load_failed`、`delete_blocked`は別のtransfer / load / ownership軸で扱う。
- 通常ファイル確認、期待size確認、SHA256確認、空き容量確認をUI非依存処理として提供する。
- 一時ファイル、途中ファイル、異なるmanifestの重みを解析loaderへ渡さない。
- canonical `.part`のdiscard、closed-before-`os.replace()`、promote後scanをB2のfilesystem APIとして提供する。
- promote public APIはcaller-supplied pathを受け取らず、model keyから解決したcanonical `.part`だけを検証・replaceする。内部helperへpathを渡す場合もcanonical一致をopen前に検証する。
- B2はdelete primitiveを提供するが、B5発行のmodel-bound・manifest-bound・request-scoped単回permitなしでは削除しない。
- permitはB5専用issuer boundaryが発行するopaque capabilityとし、B4が公開fieldの組み合わせから作成できない。B2はissuer対応verifierで対象一致・未消費を検証する。
- B2のstorage / cleanup / promote / delete failure codeはB4/B5/B6へdiagnostic detailとして引き継ぎ、上位failure classへの投影は各後続Blockが所有する。
- model fileの削除前に、B5のsingle-active loader ownershipが解除済みであることを確認する。解析worker使用中または明示unload未完了なら削除可能状態にしない。

依存: B1

主な対象候補:

- `src/core/whisper_model_store.py`
- `src/core/settings_store.py`
- `src/resource_utils.py`または同等の配置解決境界（現行構成を確認して選択）
- `.gitignore`
- `tests/test_whisper_model_store.py`
- `tests/test_settings_store.py`のMS24追加ケース

受け入れ境界:

- `models`配下の検証済み重みだけがavailableとなる。
- SHA256不一致時に既存の不正ファイルを有効扱いしない。
- 既定保存先を決め打ちしたまま書込不可で失敗させず、保存先変更へ復帰できる状態を返す。
- 解析worker使用中またはloader ownershipが残るモデルの重み削除は拒否する。別モデルへの切替または使用終了後に明示unloadを完了すれば削除可能状態へ遷移できる。

### MS24-B3: 設定・UiState・モデル選択UI

責務:

- `MMD_AutoLipTool.ini` の既存schemaへ、selected / active model identityを後方互換で追加する。`whisper_models_dir`はB2が追加・検証し、B3は利用するだけとする。
- 旧INIで選択identityキーがない場合は`small`を候補・activeの既定値として扱う。保存先がない場合の既定解決、空文字、local-only validationはB2が所有し、B3が再実装しない。
- 候補選択、active model、analysis model、availability、download状態、loaded状態、保存先をUiStateで分離して保持する。
- selected candidateとactive model identityを別々に永続化し、未Applyのcandidateは再起動後も候補表示だけに留める。active checkpointが未配置・未検証でも自動downloadや旧model fallbackを行わず、明示Applyを要求する。
- 候補選択だけではnetwork、model load、既存解析の無効化を起こさない。ユーザーが明示的に`Download & Verify`を完了し、`Apply and Re-analyze`を実行した場合だけ、適用処理へ進む。
- retained Whisper timingにmodel key、manifest identity、rebuild reasonを保持する。rebuild reasonは少なくとも `transcription_edit` と `model_changed` を区別する。
- 同一active model key / manifest identityのvoice-only結果を使った書き起こし編集だけ、保持済みWhisper timingを再利用できる。`Apply and Re-analyze`成功後のactive identity変更では保持済みtimingを再利用せず、新しいactive modelでWhisper timingを再実行する。
- 適用成功後だけactive model identityを候補へ更新し、旧解析結果は新identityでの再解析成功までPreview、診断success、VMD保存不可とする。適用失敗時はactive model、既存成功解析、Preview、VMD saveabilityを変更せず、候補をactive modelへ戻せる状態を返す。旧modelへの暗黙fallback loadは行わない。
- 設定メニューStubを全面実装せず、既存RightPaneの拡張点に専用のWhisperモデル管理UIを配置する。表示名はモデルプロファイルと混同しないものにする。
- UIにはsmall / medium / turboの用途、概算VRAM、概算速度、保存状態、選択中のモデル、保存先を表示する。
- 「選択」と「ダウンロード」「削除」「適用済み解析」を分離し、選択しただけでネットワーク処理を開始しない。
- 起動時のavailability確認は、全件SHA256検証をUIスレッドで同期実行せず、B3専用のread-only scan workerで行う。初期状態は`availability_scan_status=pending`（表示は「確認中」）として投影し、`availability_scan_job_id` / `availability_scan_generation` / shutdown guardでlate resultを破棄する。候補選択用の`panel_revision`はscan結果のguardに流用しない。workerはdaemonとし、close時はjobを失効させ、UIスレッドからjoinしない。既存AudioWorkerとB4 download workerは使用しない。
- B3のstartup / availability worker testsではB2の既定root解決を使わず、temporaryな`whisper_models_dir`またはtemporary B2 store/rootを明示注入し、repositoryのruntime `models`を読まない。
- 明示設定された`whisper_models_dir`の`StorageRootResolution`が失敗した場合、B3は既定`models`へfallbackせず、`WhisperModelStore`構築・availability worker起動・root作成を行わず、B2の`failure_code` / `message`をB3のfailure code / detailへ写像してfailed stateへ投影する。通常UIはfailure codeから安全なユーザー向け通知を生成し、message由来のraw例外・絶対パスを直接表示しない。

依存: B1、B2

主な対象候補:

- `src/core/settings_store.py`
- `src/gui_wx/ui_state.py`
- `src/gui_wx/app_controller.py`
- `src/gui_wx/main_frame.py`
- `src/gui_wx/right_pane.py`
- `src/gui_wx/app.py`
- `src/gui_wx/whisper_availability_worker.py`
- `tests/test_ms24_whisper_model_settings.py`
- `tests/test_ms24_whisper_model_ui_state.py`
- `tests/test_ms24_whisper_model_availability_worker.py`

受け入れ境界:

- 起動、設定変更、再起動後でselected candidate、active model identity、保存先がそれぞれ一致する。未Apply候補は候補表示だけに留まり、active未配置・未検証時に自動download / fallbackしない。
- 候補モデルの選択変更だけではdownload、Whisper load、既存解析の無効化が起動しない。
- TEXT + 音声またはvoice-only解析中、download中、削除中はモデル選択・保存先変更・削除を適切にlockする。
- `Download & Verify`後の`Apply and Re-analyze`が成功した場合だけ、入力modeにかかわらず旧解析結果をVMD保存可能状態へ戻さず、新model identityでの再解析を要求する。適用失敗時はactive modelと既存成功解析を維持する。
- workspace resetでモデル設定を消さない。
- 全モデルartifactが存在する場合でも、起動画面が`scan_all()`のSHA256完了を待たずに表示され、scan成功・失敗・late resultが安全に状態化される。
- pending中のcandidate selectionで`panel_revision`が変化しても、job IDと`availability_scan_generation`が一致するscan結果が破棄されない。
- scan中のcloseはworker完了をUIスレッドで待たずに戻り、daemon workerのlate callbackはno-opになる。失敗時はstable failure code/detailを保持し、通常UIにはfailure code由来の安全な通知だけを表示する。
- B3のstartup / availability worker testはtemporaryな`whisper_models_dir`またはtemporary B2 store/rootだけを使い、repository既定の`models` rootとroot runtime user dataを読まないことを確認する。
- 明示設定されたrelative / UNC / remote / device pathの保存先解決失敗時に、既定rootへのfallback、store構築、worker起動、root作成がなく、selected / active identityが保持される。

### MS24-B4: 明示確認付きforeground download・cancel・削除

責務:

- ユーザーがDownload操作を押し、確認ダイアログで承認した場合だけネットワークを使用する。
- 操作はUIをブロックしない専用workerで実行する。ただし、ユーザー操作で開始されたforeground operationとして扱い、起動時・解析開始時・timer・background callbackから開始しない。
- 公式manifestのURL以外へ接続しない。
- 既存設定画面がStubであるため、Whisper管理UIから明示的にlocal-only保存先を変更できるようにする。B2の`resolve_whisper_models_dir()`で検証し、設定保存後は新rootをlocal-only scanする。保存先変更だけでnetwork、download、load、Apply、Re-analyze、active/analysis identity変更を開始しない。
- ダウンロード前に保存先の書込権限と空き容量を確認する。容量不明・不足時は開始しない。
- `.part`等の一時ファイルへ書き込み、キャンセル・失敗・プロセス終了時に不完全な重みをavailableにしない。
- Content-Length、進捗、キャンセル、SHA256、exact size、atomic renameを管理する。
- SHA256不一致時は有効ファイルへ昇格せず、原因と再試行方法を表示する。
- download完了後も、解析時のloaderが未配置時に暗黙downloadしないよう、B2のverified状態を必ず通す。
- 明示操作によるモデル重み削除を提供する。解析worker使用中またはloader ownershipが残るモデルの削除はB2契約に従い拒否し、使用終了後はB5の明示unloadと専用issuer boundaryによるopaqueなmodel-bound単回permit発行を経て削除可能にする。B4は削除操作を仲介するがpermitを生成しない。

依存: B1、B2、B3

主な対象候補:

- `src/core/whisper_model_downloader.py`
- `src/gui_wx/model_download_worker.py`（既存AudioWorkerへ混在させず、download/delete/ownership providerをUI thread外で実行するmanagement worker。完了後scanはcontrollerの`start_whisper_availability_rescan()`へ委譲）
- `src/gui_wx/worker_state.py`またはMS24専用state
- `src/gui_wx/ui_state.py`
- `src/gui_wx/app_controller.py`
- `src/gui_wx/right_pane.py`
- `src/gui_wx/main_frame.py`
- `tests/test_whisper_model_downloader.py`
- `tests/test_ms24_model_download_worker.py`
- `tests/test_ms24_whisper_model_ui_state.py`
- `tests/test_wx_ms24_whisper_model_ui.py`

受け入れ境界:

- 起動、モデル選択、音声解析、Info表示だけではネットワークアクセスが発生しない。
- 確認ダイアログで拒否した場合、ファイル・設定・解析状態を変更しない。
- cancel後にpartial fileを使用しない。late resultは現在のdownload jobでなければ破棄する。
- download失敗後もアプリを再起動せず保存先変更・再試行・既存モデル選択へ復帰できる。
- 保存先変更はDirDialogのcancel・invalid/local-only違反・save failureでold root/stateを保持し、valid pathだけを保存して`start_whisper_availability_rescan()`で新rootを再scanする。既定rootへのfallbackはしない。
- delete操作は確認後だけ実行し、B5 provider未接続・permitなし・拒否時はblockedとする。test-only provider seamではmanagement worker内のB2 delete後にcontrollerの`start_whisper_availability_rescan()`を起動し、リスト・availability・選択状態を再投影する。実B5 provider接続後のproduction Delete成功はB5連携確認とする。

### MS24-B5: 選択モデルのAnalysisWorker / pipeline / loader伝播

責務:

- `MainFrame -> AnalysisWorker -> pipeline -> whisper_timing` の全経路へ、設定・UiStateで解決済みのactive model keyを明示的に渡す。
- TEXT + 音声とvoice-onlyの両解析開始前に、active modelのverified availabilityを確認する。
- 未配置、partial、サイズ不一致、SHA256不一致、load失敗、memory errorの場合、Whisper解析を成功扱いにせず、VMD保存不可・再試行可能な状態へ戻す。
- B1で固定したnetwork-unreachable loader adapterへ、B2の`VerifiedWhisperCheckpoint` DTOだけを渡す。DTO内部のpathをadapterが一度openしてsize / SHA256とfile identityを再検証し、同一open handleからbytesへ束縛する。解析経路では公式model key + `download_root`、path再open、直接の`whisper.load_model()`を使わない。
- adapterはv20250625のversion gateと公式model key対応alignment headsを維持し、private API不一致時はload失敗としてfail closedする。
- retained Whisper timingはactive model key / manifest identityが一致し、rebuild reasonが `transcription_edit` の場合だけ再利用する。`Apply and Re-analyze`成功後の`model_changed`では必ずWhisper timingを再実行する。
- `AnalysisParameterSnapshot`または同等のrollback identityへmodel keyとmanifest identityを追加する。model unavailable、integrity mismatch、load failure、memory failureのfailure classではrollbackで旧解析結果を復元せず、VMD保存不可を維持する。
- 現行のword timestamp優先、segment fallback、同一modelでの書き起こし編集時だけの `WhisperTimingResult` 再利用、FFmpeg PATH補正、30fps、VMD形式を変更しない。
- 現行 `lru_cache(maxsize=2)` はsingle-active model cacheへ置き換える計画とする。cache identityはmodel key、保存先、manifest identityを含み、同時にstrong ownershipを持つmodel objectは1件だけとする。
- model切替・保存先変更・アプリ終了・削除前に、解析workerがmodelを使用していないことを確認して明示eviction / unloadする。loader所有参照とcache entryを明示的に解除し、必要なdevice resource cleanupを実行する。Python GCだけをownership解除手段にしない。

依存: B2、B3、B4

主な対象候補:

- `src/core/whisper_timing.py`
- `src/core/whisper_model_loader.py`
- `src/core/pipeline.py`
- `src/gui_wx/analysis_worker.py`
- `src/gui_wx/analysis_rollback.py`
- `src/gui_wx/main_frame.py`
- `src/gui_wx/app_controller.py`
- `tests/test_whisper_timing.py`
- `tests/test_ms19_b4_analysis_worker_voice_only.py`
- `tests/test_ms24_whisper_model_propagation.py`
- `tests/test_ms24_no_implicit_download.py`

受け入れ境界:

- smallを選択した旧設定・旧callerでも、TEXT + 音声とvoice-onlyの既存Whisper timingが同じmodel keyで動く。
- medium / turboをactiveへ適用した場合、解析workerと診断入力が同じkeyを持つ。
- active modelと実際にloadしたモデルが異なる場合、成功結果をUIへ返さない。
- `Apply and Re-analyze`成功後はretained timingを再利用せず、適用後modelで再解析に成功するまで旧解析結果をVMD保存可能状態へ戻さない。候補選択または適用失敗だけでは旧解析結果を破棄しない。
- model unavailable、integrity mismatch、load failure、memory failureではrollbackで旧解析結果を復元しない。
- model切替・終了・削除前にsingle-active cacheのownershipを明示解除できる。

### MS24-B6: Info・診断レポート・エラー復帰契約

責務:

- Infoに、候補選択中・active・loadedのWhisper model key、表示名、manifest / package version、保存状態、モデル保存先の表示方針を追加する。
- 診断snapshotへ専用 `WhisperDiagnosticsSummary` を追加し、selected / active / loaded / analysis model key、manifest identity、availability、rebuild reason、failure class、package versionを一元化する。`AnalysisDiagnosticsSummary`や`GenerationDiagnosticsSummary`へWhisper固有値を分散させない。
- 選択モデル未配置、download中、cancel、SHA256不一致、load失敗、memory不足、保存先書込不可を、TEXT + 音声とvoice-onlyの既存error分類に整合するrecoverabilityへ写像する。
- `analysis_rollback.py`のmodel-aware rollback判定と同じfailure classを診断へ使用し、load / integrity / memory系失敗時にold success summaryとsaveabilityを復元しない。
- 診断レポートにユーザー環境の不要な絶対パスや認証情報を過剰に露出しない。保存先は必要な診断粒度を定義する。
- 候補選択、Download & Verify完了、delete完了、Apply失敗後にRightPaneのリストとInfo表示が古い状態を残さない。
- 解析失敗・cancel・Apply and Re-analyze成功後のVMD save action state、Preview placeholder、transcription stateを既存契約に従って同期する。

依存: B3、B5

主な対象候補:

- `src/core/output_diagnostics.py`
- `src/core/diagnostic_report.py`
- `src/gui_wx/output_diagnostics_adapter.py`
- `src/gui_wx/voice_only_errors.py`
- `src/gui_wx/analysis_rollback.py`
- `src/gui_wx/right_pane.py`
- `src/gui_wx/main_frame.py`
- `tests/test_ms24_whisper_diagnostics.py`
- `tests/test_ms24_whisper_error_recovery.py`

受け入れ境界:

- Infoと診断レポートが同じresolved model keyを表示する。
- 解析失敗時に、失敗前のold modelを現在の成功モデルとして表示しない。
- model selection / availability / actual loaded model / analysis resultの不一致を検出可能にする。
- `WhisperDiagnosticsSummary`は既存 `ms21-effective-output-v1` fingerprint payloadへ含めず、fingerprint schemaを変更しない。

### MS24-B7: 統合回帰・配布影響確認・Closeout準備

責務:

- B1〜B6のcross-boundary回帰を実行し、selection、download、cancel、delete、analysis、Preview、diagnostics、report、VMD save actionを照合する。
- 既存MS17〜MS23の回帰を、特にvoice-only、Whisper timing、settings、wx worker teardown、diagnostics、profile / presetと組み合わせて実行する。
- PyInstaller specにmanifestだけを含め、モデル重みをonefileやsource管理へ誤って取り込まないことを確認する。
- `models`外部管理、配布ZIP、初回利用者向けモデル取得、license、ネットワーク例外契約をrelease manifest / README候補へ反映する。ただしpackage / release readinessの最終判定はMS27の責務として残す。
- 実MMDでのVMD / WAV読み込み・リップ同期は実施せず、MS26へ引き継ぐ。
- MS24 Closeout判定時に、P1 / P2 / P3、未検証事項、ユーザーGUI確認範囲、公開版Whisper versionを記録する。

依存: B1〜B6

主な対象候補:

- `tests/`のMS24専用test
- `MMD_AutoLipTool.spec`
- `docs/Release_Package_Manifest.md`
- `README.md`
- `docs/MS20_and_Beyond_Index.md`
- `docs/MS20_and_Beyond_Roadmap.md`

受け入れ境界:

- 自動download、cloud ASR、音声外部送信、background通信、Qt / PySide6復活がない。
- 既存の `small` 既定挙動、VMD 30fps、固定母音名契約、profile / preset優先順位、MMD用WAV契約を壊さない。
- package / releaseの最終作業へ進む前に、MS24のdownload例外と外部model storageが文書化される。

## 6. 依存順と責務境界

```text
B1 catalog / manifest / compatibility gate
 └─> B2 storage / availability / integrity
      ├─> B3 settings / state / selection UI
      │    └─> B4 explicit download / cancel / delete worker
      │         └─> B5 analysis propagation / no implicit download
      │              └─> B6 diagnostics / recovery
      └───────────────────────────────────────────────┘
                           B1〜B6 ──> B7 integration / closeout preparation
```

責務境界:

- B1は「何を許可し、network-unreachable loaderがどうalignment headsを維持するか」を所有し、downloadやUI状態を所有しない。
- B2は「どこにあり、検証済みか」を所有し、ユーザー確認付き通信を開始しない。
- B3は「何を選択し、どの理由で再解析が必要か」を所有し、選択だけでloadやdownloadを開始しない。
- B4は「ユーザー確認後にどう取得・中断・削除するか」を所有し、解析を開始しない。
- B5は「解析へ実際にどのmodel keyを渡し、single-active modelをどう所有・解放するか」を所有し、network処理を開始しない。
- B6は専用 `WhisperDiagnosticsSummary` とfailure / rollback投影を所有し、診断値を独自再計算しない。
- B7はcross-blockの検証と文書同期を所有し、MS26のactual-MMD確認やMS27のrelease実施へ越境しない。

## 7. データ契約

### 7.1 Model catalog

```text
WhisperModelSpec
  model_key: Literal["small", "medium", "turbo"]
  display_name: str
  multilingual: bool
  japanese_supported: bool
  official_url: str
  filename: str
  sha256: str
  size_bytes: int
  vram_hint: str
  speed_hint: str
  recommended_use: str
  whisper_package_version: str
```

`official_url`、`filename`、`sha256`、`size_bytes`、`whisper_package_version`はmanifest由来の不変値とし、GUI入力やINIから上書きしない。

### 7.2 Model availability

```text
ModelAvailability
  model_key: str
  storage_root: Path
  file_path: Path | None
  status: missing | partial | downloading | verified | invalid_size |
          invalid_sha256 | load_failed | delete_blocked | unsupported
  actual_size_bytes: int | None
  verified_sha256: str | None
  failure_code: str | None
```

### 7.3 Selection and analysis identity

- `selected_whisper_model_key`: ユーザーが切替候補として選択しているkey。候補選択だけではactive model・解析結果を変更しない
- `active_whisper_model_key`: `Download & Verify`と`Apply and Re-analyze`が成功し、現在適用中のkey
- `active_whisper_manifest_identity`: 現在適用中のmodelのmanifest identity
- `loaded_whisper_model_key`: 現在の解析loaderが使用したkey
- `analysis_whisper_model_key`: 解析結果に対応するkey
- `model_manifest_identity`: package version、manifest schema、model key、SHA256のcanonical identity
- `retained_whisper_timing_model_identity`: 保持済みtimingを生成したmodel keyとmanifest identity
- `analysis_rebuild_reason`: `none | transcription_edit | model_changed | input_changed`
- `whisper_failure_class`: `none | model_unavailable | integrity_mismatch | load_failure | memory_failure | transcribe_failure | cancelled`

候補選択だけでは、`active_whisper_model_key`、`active_whisper_manifest_identity`、`analysis_whisper_model_key`、既存Preview、診断success、VMD saveabilityを変更しない。

`analysis_whisper_model_key`またはmanifest identityが現在のactive identityと一致しないTEXT + 音声 / voice-only結果は、再解析が必要でありVMD保存不可とする。これは`Apply and Re-analyze`が成功した後に適用する。

retained Whisper timingは、model identityが現在のactive identityと一致し、`analysis_rebuild_reason == transcription_edit` の場合だけ再利用する。候補選択だけではactive identityが変わらないため再利用条件を壊さない。`Apply and Re-analyze`成功後の`model_changed`、identity不一致、identity欠落では再利用しない。

`model_unavailable`、`integrity_mismatch`、`load_failure`、`memory_failure`はrollback非許可classとし、旧解析結果、Preview、診断success、VMD saveabilityを復元しない。

適用失敗時は、active identityと既存成功解析を変更せず、候補をactive identityへ戻せる状態を返す。旧modelへの暗黙fallback loadは行わない。

既存 `ms21-effective-output-v1` のcanonical fingerprint schemaは変更しない。Whisper model identityは別の解析結果identityと専用 `WhisperDiagnosticsSummary` へ保持し、既存fingerprint payloadへ追加しない。

### 7.4 Single-active loader ownership

```text
WhisperModelCacheState
  loaded_model_key: str | None
  loaded_manifest_identity: str | None
  loaded_checkpoint_path: Path | None
  owner_state: unloaded | loading | worker_owned | release_pending
```

- cacheは1つのmodel objectだけをstrong ownershipする。
- model切替・保存先変更・アプリ終了・削除要求では、active workerの終了を確認してから明示unloadする。
- unloadはloader / cacheの参照解除とdevice resource cleanupを所有し、Python GCは補助に限る。
- ownership解除に失敗した場合は新model loadと対象checkpoint削除を開始しない。

### 7.5 Whisper diagnostics

```text
WhisperDiagnosticsSummary
  selected_model_key: str
  active_model_key: str | None
  loaded_model_key: str | None
  analysis_model_key: str | None
  manifest_identity: str | None
  package_version: str
  availability_status: str
  rebuild_reason: str
  failure_class: str
```

`OutputDiagnosticsSnapshot`は専用 `WhisperDiagnosticsSummary` を保持する。Whisper固有値を `AnalysisDiagnosticsSummary` / `GenerationDiagnosticsSummary` へ分散させず、`ms21-effective-output-v1` fingerprint生成はこのsummaryを参照しない。

### 7.6 Settings

既存 `MMD_AutoLipTool.ini` の互換を維持し、責務別のキーは次とする。実装時に既存命名規約と照合して確定する。

- B2-owned: `whisper_models_dir = `（空文字はB2の既定保存先）
- B3-owned: selected candidate key、active model key、active manifest identity

未指定旧INIは、B3のselected / active identityを`small`へ、B2の保存先を空文字から既定保存先へ解決する。B2とB3が同じキーを別責務で上書きしない。runtime user dataの実ファイルは計画中に変更しない。

## 8. 状態遷移と失敗時の復帰

### 8.1 Download

```text
未配置
  ├─[Download押下]─> 確認待ち
  │                    ├─[拒否]─> 未配置
  │                    └─[承認]─> 空き容量 / 保存先preflight
  │                                  ├─[失敗]─> 未配置 + recoverable error
  │                                  └─[通過]─> downloading
  │                                                ├─[cancel/error]─> B2 discard_staging(canonical .part)
  │                                                │                    ├─[cleanup success]─> 未配置
  │                                                │                    └─[cleanup failure]─> partial + recoverable error
  │                                                ├─[SHA/size不一致]─> invalid + retryable error
  │                                                └─[検証成功]─> verified
```

### 8.2 Analysis

```text
active verified + selected candidate
  ├─[候補選択]─> selected candidateだけ更新
  │              + network / load / 既存解析invalidなし
  ├─[Download & Verify]─> foreground取得・検証
  │                         ├─[拒否/cancel/error]─> active identity / 既存解析を維持
  │                         └─[成功]─> verified candidate
  ├─[Apply and Re-analyze]─> network-unreachable local bytes loading
  │                           ├─[integrity/load/alignment/memory failure]─> active identity / 既存解析を維持
  │                           │                                         + candidateをactiveへ戻せる
  │                           │                                         + 旧model fallbackなし
  │                           └─[load/head success]─> active identityを更新
  │                                                       + 旧Preview/diagnostics/VMD save disabled
  │                                                       + 新modelで再解析要求
  ├─[TEXT + 音声 / voice-only analysis]─> active model identityで解析
  │                                         ├─[integrity/load/memory failure]─> invalid result
  │                                         │                                  + rollback禁止
  │                                         │                                  + VMD save disabled
  │                                         └─[success]─> analysis result with model identity
  ├─[voice-only transcription edit + same identity]─> retained timing reuse
  └─[active identity changed]─> rebuild reason=model_changed
                               + retained timing reuse禁止
                               + new active modelでWhisper timing再実行
```

### 8.3 Delete

- Download済みモデルを選択し、削除確認を承認した場合だけ削除する。
- active workerが対象modelを使用中なら削除を拒否する。worker終了後、single-active cacheの明示unloadとloader ownership解除を完了してから削除する。
- 解析結果identityが対象modelを参照している場合は、その解析結果、Preview、診断success、VMD saveabilityを先に無効化する。Python GC待ちだけで削除可能扱いにしない。
- B4はB5のownership providerをmanagement workerから呼び出し、provider未接続・permitなし・拒否時はblockedとする。permitの発行とactive/analysis invalidationはB5が所有し、B4は生成しない。
- test-only provider seamまたはB5連携後のpermitでB2 deleteをmanagement worker内から呼び出し、削除成功後はcontrollerの`start_whisper_availability_rescan()`によるlocal-only rescanを経てavailability、リスト、Info、設定上の選択状態を同一UIターンで再投影する。

## 9. ネットワーク・セキュリティ・ライセンス境界

- 許可される通信は、ユーザーがDownloadを明示操作し、確認ダイアログで承認したforeground model downloadだけである。
- dedicated workerで実行することはbackground通信の許可を意味しない。起動時、解析開始時、選択変更時、timer、silent retryからネットワークを開始しない。
- 公式manifestにないURL、redirect、任意URL入力、cloud ASR、音声データ送信を実装しない。redirectは全面拒否する。
- HTTPS、Content-Length、timeout、cancel、B2のcanonical `.part` cleanup、SHA256、exact size、atomic renameを契約化する。
- Whisper codeとmodel weightsのMIT条件、配布時のnotice、外部model storageの扱いをB7で確認する。
- 新規Python依存を追加しない。HTTP取得は既存標準ライブラリまたは現行依存で実現可能性を先に確認する。

## 10. テスト方針

### 10.1 B1/B2 core

- manifest schema/version、許可model key、`.en`拒否、URL / SHA256 / size validation
- current official metadataとの一致
- `whisper.__version__` / manifest version gate、v20250625 private alignment-head APIの存在・model key・値形式
- `VerifiedWhisperCheckpoint`から同一open handleで検証したbytesだけを読むloader adapter、公式model key + `download_root`経路の不使用、network API未到達
- local checkpoint load後のalignment heads適用、word timestamp、segment fallback回帰
- missing、partial、directory、size mismatch、hash mismatch、verified判定
- 空き容量不足、保存先作成、書込不可、設定保存先fallback
- SHA256計算が大きなファイルを不必要に一括メモリへ読み込まないこと
- `pyproject.toml` / `requirements.txt`のWhisper version一致、Python 3.14.3開発・受入ゲート
- source `src.core.whisper_models`、PyInstaller onefile `src.core.whisper_models`のpackage-relative manifest resource解決
- installed packageのsetuptools package-data `core/whisper_models.json`対応、PyInstaller datasの`src/core`展開先、model weights非同梱

### 10.2 B3 state/settings/UI

- 旧INIのキー欠落、未知値、空値、型不正、保存・再起動
- 候補model selection、Apply and Re-analyze、analysis pending rebuildの関係
- 候補選択だけではold analysis / Preview / diagnostics / VMD saveabilityを変更せず、Apply成功後にactive identity不一致の旧結果を無効化すること
- selected / active identityの別々の保存・再起動復元、未Apply候補の候補表示維持、active未配置・未検証時の自動download / fallback禁止
- 同一active modelのvoice-only transcription editだけretained timingを再利用し、active identity変更後は再利用しないこと
- rebuild reason、retained timing model identity、selected / active identityの一致・不一致
- Busy、workspace reset、stale selection、リスト再投影
- Info表示のmodel profileとの名称混同防止
- availability failureではfailure codeから安全なユーザー向け通知を生成し、B2 `message`由来のraw例外文字列・絶対パスを通常UIへ表示しないこと。未知のfailure codeはgeneric通知へfail closedすること

### 10.3 B4 download worker

- fake HTTP sourceでprogress、Content-Length、timeout、cancel、failure、retry
- 確認拒否時にnetwork/file/settings/stateが不変
- DirDialogのcancel、invalid/local-only違反、save failure、validな保存先変更後のnew-root local-only scan
- partial fileのcleanup、atomic rename、SHA256不一致、size不一致
- 二重download、stale callback、close中のlate callback破棄
- provider未接続・permitなし・拒否時のmodel削除拒否、test-only provider seamのB2 delete、`start_whisper_availability_rescan()`によるpost-delete scan、削除後のlist refresh
- B2 delete、post-download/post-deleteの再scan、ownership providerがUI threadをブロックしないこと
- HTTP 3xx redirectを全面拒否し、network body保存・promoteへ進まないこと
- 実ネットワークへ接続しないdeterministic unit test

### 10.4 B5 analysis

- small / medium / turboの明示伝播
- MainFrameがdefault引数へ落とさず選択値を渡すこと
- TEXT + 音声 / voice-onlyの全Whisper timing経路で同じresolved model identityを渡すこと
- verified前のloader呼び出し禁止、local checkpoint以外の入力拒否、解析時network API未到達
- v20250625 alignment heads、word timestamp優先、segment fallback、同一model transcription edit時だけのtiming result再利用
- model change後のfull Whisper timing再実行とold result保存禁止
- model unavailable、integrity mismatch、load error、memory error時のrollback禁止
- single-active cache、切替・保存先変更・終了・削除前の明示eviction / unload、old object再利用禁止
- cache / loader参照解除を明示検証し、Python GCだけに依存しないこと

### 10.5 B6 diagnostics/report

- selected / loaded / analysis model identityの一致・不一致
- 専用 `WhisperDiagnosticsSummary` とInfo / diagnostic reportの同一値
- missing / downloading / cancel / hash mismatch / load failure / memory failureの分類
- 既存profile / preset / morph-name / fingerprint schema回帰
- 診断失敗時のold success情報残留防止
- `WhisperDiagnosticsSummary`を追加しても `ms21-effective-output-v1` payloadと既存fingerprint値が変わらないこと

### 10.6 B7回帰ゲート

最小順序:

1. MS24専用core tests
2. Whisper timing / voice-only / settings / diagnostics限定回帰
3. MS23 profile / preset / morph-name回帰
4. wx worker / lifecycle / RightPane回帰
5. 全体pytest
6. `compileall src tests`
7. `git diff --check`
8. package specのmanifest同梱・model重み非同梱確認
9. ユーザー手動GUI確認

各pytest commandは、pass表示だけでなくprocess exit code 0を合格条件とする。wx native teardown由来の終了コード異常が出た場合、MS24機能のpass表示だけでCloseoutへ進めず、原因をP2/P3として分類する。

## 11. 受け入れ条件

### 機能

- [ ] `small`、`medium`、`turbo`をGUIで選択できる。
- [ ] 既定値は `small` で、旧INIの欠落・旧callerでも既存挙動を維持する。
- [ ] 各モデルの名前、概算VRAM、処理負荷、推奨用途、exact download sizeを表示できる。
- [ ] 選択値がTEXT + 音声 / voice-onlyの全Whisper timing経路、設定、AnalysisWorker、pipeline、`WhisperDiagnosticsSummary`、reportへ同一identityで伝播する。
- [ ] 設定保存と再起動後復元が動作する。
- [ ] verified modelの明示download、cancel、削除が動作する。
- [ ] 同一active modelのvoice-only書き起こし編集だけretained timingを再利用し、Apply成功後のactive identity変更では新active modelでWhisper timingを再実行する。

### 安全性

- [ ] 未配置モデルを解析loaderへ渡して暗黙downloadさせない。
- [ ] 解析loaderは`VerifiedWhisperCheckpoint`の検証済みbytesだけを読み、公式model key + `download_root`経路やnetwork APIへ到達しない。
- [ ] v20250625のversion gateと公式model key対応alignment headsを維持し、private API不一致時はfail closedする。
- [ ] networkはユーザー確認済みのforeground downloadだけである。
- [ ] official manifest、SHA256、exact size、atomic file promotionを通る。
- [ ] 明示設定された保存先の`StorageRootResolution`失敗時はB2の`failure_code` / `message`をB3のfailure code / detailへ正しく写像し、failure codeから安全な通知を表示する。message由来のraw例外・絶対パスは通常UIへ表示しない。
- [ ] partial / mismatch / load failure / memory failureでrollbackにより古い解析結果をVMD保存可能へ戻さない。
- [ ] single-active cacheを明示unloadし、loader ownership解除前の削除とuse-after-deleteを防ぐ。
- [ ] cloud ASR、音声外部送信、background通信、Qt / PySide6復活がない。

### 回帰・配布

- [ ] 日本語固定モーフ `あ / い / う / え / お` とMS23 Latin profileの契約を壊さない。
- [ ] preset / model profileの責務分離、優先順位、active guard、history、diagnosticsを壊さない。
- [ ] word timestamp / segment fallback、30fps、VMD、MMD用WAVの契約を壊さない。
- [ ] 専用 `WhisperDiagnosticsSummary` を追加しても `ms21-effective-output-v1` fingerprint schema / payloadを変更しない。
- [ ] Python 3.14.3を開発・受入対象として確認し、Python 3.11 / 3.12は未検証として記録し、`pyproject.toml` / `requirements.txt` version同期を確認する。
- [ ] source / frozenの`src.core` manifest resource runtime解決と、installed packageの`core/whisper_models.json` package-data配置マッピングを確認する。installed `core.whisper_models` runtime importと既存アプリ全体のinstalled namespace補修はB1の合否に含めない。
- [ ] PyInstaller onefileへモデル重みを同梱しない。
- [ ] model storage、download例外、license、ユーザー確認手順を関連文書へ記録する。
- [ ] 実MMDでのVMD / WAV読み込み・リップ同期未確認をMS24完了と混同せず、MS26へ引き継ぐ。

## 12. リスクと対策

| ID | リスク | 判定 | 対策 |
| --- | --- | --- | --- |
| MS24-R1 | 公式CLIのturbo既定値を取り込み、small既定の回帰が発生する | P2候補 | アプリ既定値をsmallに固定し、明示的なversioned testを置く |
| MS24-R2 | 公式model key + `download_root`がTOCTOUで暗黙downloadし、ネットワーク契約を破る | P1候補 | この解析方式を禁止し、verified local checkpointだけを読むnetwork-unreachable adapterへ固定する |
| MS24-R3 | local path loadでword alignment headsが設定されず、タイミング品質が変わる | P1候補 | v20250625 version gate下で公式model key対応alignment headsをprivate APIから設定し、不一致時はfail closedする |
| MS24-R4 | medium/turboのVRAM不足でUIが固まり、古い解析結果が残る | P2候補 | worker、memory error分類、analysis invalidation、save guard、再試行導線 |
| MS24-R5 | partialまたはSHA不一致ファイルを正規重みとして使用する | P1候補 | `.part`、size、SHA256、atomic rename、fail closed |
| MS24-R6 | model storageがexe隣接で書込不可 | P2候補 | 書込権限と空き容量を事前確認し、書込可能な保存先選択を設定へ保存 |
| MS24-R7 | download workerを既存AudioWorkerへ混在させ、cancel/lifecycle回帰が出る | P2候補 | 専用worker/stateまたは明確な別kindで分離し、既存音声worker契約を変更しない |
| MS24-R8 | PyInstallerへ大容量重みが誤同梱され、配布サイズ・licenseが変わる | P2候補 | manifestだけをdatasへ含め、重みは外部models管理。specと成果物内容を検査 |
| MS24-R9 | GitHub mainの未タグ変更を採用し、再現性が失われる | P2候補 | PyPI公開版だけを候補とし、依存更新は別の互換性・承認ゲートへ隔離 |
| MS24-R10 | download完了・削除後にRightPaneが古いlistを表示する | P3候補 | status changeをsingle projectionで再構築し、delete/download後の専用回帰を追加 |
| MS24-R11 | Apply成功後のactive model変更後もvoice-onlyのretained timingを再利用する | P1候補 | retained model identityとrebuild reasonを持ち、`transcription_edit`かつ同一active identityの場合だけ再利用する |
| MS24-R12 | load / integrity / memory失敗後にrollbackで旧結果が保存可能へ戻る | P1候補 | rollback identityへmodel / manifest / failure classを追加し、対象failure classの復元を禁止する |
| MS24-R13 | 複数大容量modelをcacheし、memory不足または削除不能になる | P2候補 | single-active cache、明示eviction / unload、worker ownership解除、device cleanupを固定する |
| MS24-R14 | Python 3.11 / 3.12の未検証範囲を、Python 3.14.3の実測結果で検証済みと誤認する | P3候補 | 開発・受入対象をPython 3.14.3に固定し、3.11 / 3.12は未検証として明記する |

## 13. Out of Scope

- PMX / PMD読込、モデルファイル解析、任意モーフ名mapping
- ユーザー定義モーフセット、追加表情モーフ
- 英語音声認識・英語音素処理の本格対応
- 他ASR backend、外部クラウドASR、音声データの外部送信
- 起動時・解析開始時・選択変更時の自動download
- ユーザー操作によらない通信、telemetry、background network
- Whisper GitHub `main`直採用、未タグcommit採用、無条件のPyTorch同時更新
- Whisperモデルのonefile内蔵、Git追跡、runtime user dataとの混在
- 複数モデルの同時解析、モデル自動切替、精度ベンチマークの製品保証
- MS25一括出力
- MS26実MMD統合確認
- MS27 package / release readinessの最終判定、package生成、release、tag、push
- Qt / PySide6の復活

## 14. 実装開始前の確認ゲート（計画ベースライン）

MS24-B3の実装を開始する前に、次をread-onlyで確認する。

1. `openai-whisper`の公開版、manifest URL、SHA256、Content-Length、モデルファイル名が一致している。
2. 現行Python 3.14.3 / `openai-whisper==20250625` / PyTorch 2.13.0+cpu / PyInstaller 6.19.0を記録し、Python 3.14.3を本リポジトリの開発・受入対象として固定する。Python 3.11 / 3.12は今回のゲートに含めない。
3. verified local checkpointだけを読むnetwork-unreachable adapter、v20250625 private alignment-head API、version gate、fail-closed条件、word timestamp回帰を確認する。公式model key + `download_root`を解析時に直接渡す方式へ戻さない。
4. `models`既定保存先、source/frozen path、書込不可時の設定保存先を確定する。
5. `AudioWorker`とdownload workerを分離する責務、busy、cancel、close、late callbackを確定する。
6. 専用 `WhisperDiagnosticsSummary` のselected / loaded / analysis identity、availability、rebuild reason、failure classと、既存fingerprint非変更境界を確認する。
7. exact `size_bytes`と空き容量計算単位を確定する。確認できない値をGUIやmanifestへ仮置きしない。
8. package specへmanifestを含める方法とmodel weights非同梱の検査方法を確定する。
9. retained timing model identity / rebuild reason、model-aware rollback禁止class、single-active cache / unload / ownership解除を確認する。
10. `pyproject.toml` / `requirements.txt`の依存値同期をread-onlyで確認する。
11. MS23 Closeout A、MS22 Closeout A、runtime user data ignore、actual-MMD deferred、MS27 package / release境界を変更しないことを確認する。

ゲート未通過の場合は実装を開始せず、P1/P2/P3を分類し、必要ならMS24-B3 planへ戻す。

## 15. 計画上の採用前提とユーザー判断

現時点で実装開始を止める未解決のユーザー判断はない。次の推奨前提をMS24の計画ベースラインとして採用する。

- 既定モデル: `small`
  - 理由: 現行アプリの既定値であり、TEXT + 音声 / voice-onlyの日本語Whisper timingと既存回帰を守れる。公式CLIのturbo既定値はアプリへ持ち込まない。
- 適用範囲: TEXT + 音声とvoice-onlyを含む全Whisper timing経路
  - 理由: 現行pipelineは両input modeでWhisper timingを使用する。選択model、実load model、解析結果identityを一つの契約へ揃える。
- 解析loader: verified local checkpoint専用のnetwork-unreachable adapter
  - 理由: 公式model key + `download_root`はTOCTOUによる再download余地がある。v20250625 version gate下で公式key対応alignment headsを適用し、private API不一致時はfail closedする。
- UI配置: 既存RightPaneの専用Whisperモデル管理領域
  - 理由: 設定ダイアログがStubであるため、MS24のモデル選択・download・deleteだけを実装でき、設定ダイアログ全体の新規実装を避けられる。
- 保存先: frozen時はexe隣接 `models`、書込不可時はユーザー選択先をINIへ保存
  - 理由: Roadmapの既定保存先契約とPyInstaller onefileの外部重み管理を両立できる。
- 依存版: 初期は `openai-whisper==20250625` を維持
  - 理由: 現行固定値と公開版が一致しており、未タグmainの変更を取り込まず再現性を守れる。
- Python検証: 本リポジトリの開発・受入対象を現行 `.venv` の3.14.3とし、3.11 / 3.12は今回未検証として記録する
  - 理由: ユーザー判断により、このリポジトリ開発ではPython 3.14.3環境を必要十分な検証基準とするため。
- network: 明示Download操作と確認後のforeground downloadだけ
  - 理由: Roadmapが定める唯一のnetwork例外であり、音声外部送信やbackground通信を増やさない。

この前提を変更する場合は、該当Blockの実装開始前に変更点、回帰影響、受け入れ条件を明示する。

## 16. 次工程への引き継ぎ

- MS24-B6はproduction実装、自動検証、ユーザー手動GUI確認まで完了した。ユーザーGUI確認はユーザー報告の範囲に限定し、Codex自身のGUI実行結果とは扱わない。
- B6の自動検証は全pytest `881 passed, 2 skipped`、process exit code `0`、`compileall -q src tests`、`git diff --check`のprocess exit code `0`である。
- Python 3.14.3の開発・受入ゲートは確認済みであり、Python 3.11 / 3.12は今回未検証として扱う。実MMD確認はMS26、MS27 package / release readinessはMS27へ引き継ぐ。
- B6のproduction code・test code変更は`1f1aff2 Implement MS24-B6 diagnostics and recovery`としてcommit済みであり、B6のstage / commitは完了している。push、merge、tag、releaseは未実施である。
- 現在地: MS24-B7のintegration regression、static package audit、利用者向け文書同期、Python 3.14.3 development / acceptance gateまで実施済み。MS24 Closeout Aは2026-08-28に判定済みで、P1 / P2はなく、B7-F-001 / B7-F-002は解消済みとして記録した。Python 3.11 / 3.12は今回の受入対象外として未検証扱いを維持する。実MMD確認はMS26、package / release readinessはMS27へ引き継ぐ
