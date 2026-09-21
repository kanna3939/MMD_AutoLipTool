# MS24-B1 Implementation Plan

## 1. 文書情報

- 対象マイルストーン: `MS24 Whisper Model Selection`
- 対象Block: `MS24-B1 Whisperモデル契約・versioned manifest・互換性ゲート`
- 作成日: 2026-08-20
- 更新日: 2026-08-22（P2 / P3レビュー指摘、メイン再チェック指摘、再起動時selected / active分離契約、package resource namespace / 配置先契約、installed package runtime import受け入れ範囲の計画補正、二段階切替・検証済みbytes load方針の採用、B1実装状態同期）
- 作成時branch: `feature/MS23-implementation`
- 作成時HEAD: `3ba84f0 Document MS24 block breakdown`
- 実装コミット: `eafdc16 Implement MS24-B1 Whisper model contract`
- 直接依存: なし。MS23 Closeout A、MS22 Closeout Aを前提とする
- 次の依存先: MS24-B2 Model Storage / Availability / Integrity
- 文書状態: **Implementation Completed / B2 Handoff**
- 本文書作成時の変更権限: 本文書だけ。production code、test code、GUI、依存関係、runtime user dataは変更しない

現行環境の確認値は、Python `3.14.3`、`openai-whisper==20250625`、PyTorch `2.13.0+cpu`、PyInstaller `6.19.0`である。Python 3.14.3は`openai-whisper==20250625`の公式classifier外であるため、補助的な現行実測環境として記録するだけとし、Whisper互換性の受け入れ対象はPython 3.13系列とする。

2026-08-21の`eafdc16`で、B1のmanifest、catalog、verified-local bytes loader、package/spec境界、B1専用test、word / segment fallback回帰が実装対象へ反映された。本同期では実装状態だけを記録し、B2〜B6の未実装責務、Python 3.13互換性確認、GUI、実モデル、実MMD確認を完了扱いにしない。

## 2. 背景

MS24 Block Breakdownでは、MS24のモデル選択肢を`small / medium / turbo`に限定し、モデル取得物の識別情報と、解析時の暗黙download禁止を固定している。B1は、その後の保存先管理、ユーザー確認付きdownload、GUI選択、AnalysisWorker伝播が再発明されないように、モデルcatalogと解析loaderの安全境界を先に定義するBlockである。

現行コードとの照合で確認した事実は次のとおりである。

- `src/core/whisper_timing.py`の`_load_whisper_model()`は`lru_cache(maxsize=2)`であり、`whisper.load_model(model_name)`へmodel keyを渡す。未配置時は公式Whisper loaderの既定download挙動を受ける。
- v20250625の公式`whisper.load_model()`は、model keyを受けた場合に`_download()`へ進む。一方、local checkpoint pathを受けた場合はalignment headsを設定しない。
- B2でsize / SHA256検証済みDTOを作成しても、その後に同じpathのファイルが差し替えられ得る。現行Whisperのlocal-path loaderは検証後にpathを再openするため、B1では検証済みbytesを同じload処理へ束縛し、path再openを禁止する。
- `src/core/pipeline.py`は`whisper_model_name`を受け取るが、現行の解析入口では既定値`small`が使われる。`src/gui_wx/main_frame.py`から`AnalysisWorker`を生成する箇所でも、model nameを明示的には渡していない。
- `src/gui_wx/analysis_worker.py`はvoice-onlyの新規解析で`recognize_audio_timing()`を呼び、書き起こし編集の再解析では保持済み`WhisperTimingResult`を再利用する。保持結果には現在、model keyやmanifest identityがない。
- `recognize_audio_timing()`の現行実装には、複数word anchorの優先、同一の`word_timestamps=True`結果でwordが疎な場合のsegment選択、初回実行失敗またはword / segment双方のanchorなし時の`word_timestamps=False`再試行がある。
- 現行`tests/test_whisper_timing.py`が直接確認するのは、複数word anchorの優先と、同一初回結果内での疎wordからsegmentへの選択である。`word_timestamps=False`へ再試行する分岐の明示的回帰testはまだない。
- `MMD_AutoLipTool.spec`はWhisper Python packageのデータを収集するが、モデル重みを同梱する設定ではない。B1ではmanifestだけを配布可能なデータとして扱い、重みをsourceやonefileへ追加しない。
- `pyproject.toml`と`requirements.txt`はともに`openai-whisper==20250625`で一致している。B1の初期方針では依存値を変更しない。

したがって、B1で現行解析経路全体を新loaderへ切り替えることはしない。B1は、B5が呼び出し経路へ接続するための検証済みlocal checkpoint専用adapterと、そのversioned contractを所有する。B2が作成するavailability / integrity結果を受け取れる形にし、B3〜B6の責務を先取りしない。

## 3. 目的

次の契約を、UI非依存のcatalog / loaderとして固定する。

1. 解析対象として許可するmodel keyを`small / medium / turbo`だけに限定する。
2. 公式URL、filename、SHA256、Content-Length由来のexact `size_bytes`、package version、表示用目安をrepo内manifestへ固定する。
3. `openai-whisper==20250625`とmanifest versionの不一致、private alignment-head APIの不一致、未知model key、未検証pathをfail closedする。
4. 解析loaderは検証済みlocal checkpoint参照だけを受け取り、同一readでsize / SHA256を確認したbytesを直接model loadへ渡し、model key + `download_root`経路、path再open、ネットワークAPIへ到達しない構造にする。
5. local path loadで失われるv20250625のmodel key対応alignment headsを、version gate通過後だけ公式private mappingから適用する。
6. 既存のword timestamp、segment fallback、FFmpeg PATH補正、30fps、VMD、MS23 profile / preset / diagnostics / fingerprint契約を変更しない。

## 4. In Scope

- versioned manifest schema v1の定義
- `small / medium / turbo`の厳密なcatalogとvalidator
- `WhisperModelSpec`相当のimmutable UI非依存DTO
- model key、display name、official metadata、manifest identityの分離
- verified local checkpointを表すloader入力DTO
- v20250625のpackage version gate
- `whisper._ALIGNMENT_HEADS`、公式model key、`set_alignment_heads()`のprivate API契約
- local checkpoint専用loader adapter
- B2検証後の差し替えを拒否し、検証済みbytesだけをloadするloader内のstreaming size / SHA256検証
- adapterのfail-closed error分類
- B1専用catalog / loader contract test
- 既存Whisper timingのword / segment fallback回帰確認
- 初回word timestamp実行の失敗またはanchorなしから、`word_timestamps=False`へ再試行する明示的回帰test
- manifestをsource / frozen package resourceとして読める配置契約と、installed package-dataの配置マッピングの固定
- `pyproject.toml` / `requirements.txt`のWhisper依存値一致のread-only確認
- manifestのみをPyInstaller配布対象へ含め、model weightsを含めないpackage境界の計画化

## 5. Out of Scope

- `models`保存先の作成、書込権限、空き容量、partial、availability管理、およびavailable判定用の初回size / SHA256実ファイル検証と`VerifiedWhisperCheckpoint`生成（MS24-B2）。ただし、B2検証結果を永続的に信頼せず、loader内で検証済みbytesへ束縛してloadする契約はB1が所有する
- `MMD_AutoLipTool.ini`へのmodel key /保存先追加、UiState、RightPane、選択・適用UI（MS24-B3）
- 明示確認付きforeground download、cancel、delete、HTTP処理、worker（MS24-B4）
- `MainFrame -> AnalysisWorker -> pipeline -> whisper_timing`への実model identity伝播、解析時loader切替、single-active cache、unload（MS24-B5）
- Info、`WhisperDiagnosticsSummary`、diagnostic report、error recovery、rollback投影（MS24-B6）
- MS24全体回帰、README / release manifestの最終同期、Closeout判定（MS24-B7）
- モデル重みのdownload、実重みを使った解析、実ネットワーク通信
- 新しいPython依存、PyTorch更新、GitHub `main`や未tag commitの採用
- cloud ASR、音声外部送信、background通信、telemetry
- `presets.json`、`profiles.json`、`MMD_AutoLipTool.ini`の内容確認・変更・生成・stage
- Qt / PySide6復活、PMX / PMD解析、任意モーフmapping、英語ASR
- 実MMDでのVMD / WAV読込・リップ同期確認（MS26）
- package生成、release、tag、push、merge、branch操作（MS27または明示承認時）
- 現行の`src.core` / `core`混在import namespaceをアプリ全体で統一する変更。B1のinstalled package gateは`core/whisper_models.json`のpackage-data配置マッピングだけを対象とし、`core.whisper_models`のruntime importおよびinstalled entry point全体のnamespace補修は別のpackage工程で扱う

## 6. 前提条件

### 6.1 公式metadataの基準

公式Whisper v20250625の`whisper/__init__.py`にあるmodel URL、SHA256相当値、model key対応alignment headsを基準とする。2026-08-20に公式Azure配布先へHEADを行い、`Content-Length`を確認した。manifestへ入れる値は次のとおりとする。

| model key | filename | exact `size_bytes` | SHA256 | VRAM目安 | 公式相対速度目安 | 用途表示の初期値 |
| --- | --- | ---: | --- | --- | --- | --- |
| `small` | `small.pt` | `483617219` | `9ecf779972d90ba49c06d968637d720dd632c55bbf19d441fb42bf17a411e794` | `~2 GB` | `~4x` | 標準・既定モデル |
| `medium` | `medium.pt` | `1528008539` | `345ae4da62f9b3d59415adc60127b97c714f32e89e936602e85993674d08dcb1` | `~5 GB` | `~2x` | 高負荷モデル |
| `turbo` | `large-v3-turbo.pt` | `1617941637` | `aff26ae408abcba5fbf8813c21e62b0941638c5f6eebfb145be0c9839262a19a` | `~6 GB` | `~8x` | 高速モデル |

公式URLは次のとおりである。`turbo`のmodel keyと配布filenameは一致しないため、`large-v3-turbo.pt`を`turbo.pt`へ改名して保存する契約にはしない。

```text
small:
https://openaipublic.azureedge.net/main/whisper/models/9ecf779972d90ba49c06d968637d720dd632c55bbf19d441fb42bf17a411e794/small.pt

medium:
https://openaipublic.azureedge.net/main/whisper/models/345ae4da62f9b3d59415adc60127b97c714f32e89e936602e85993674d08dcb1/medium.pt

turbo:
https://openaipublic.azureedge.net/main/whisper/models/aff26ae408abcba5fbf8813c21e62b0941638c5f6eebfb145be0c9839262a19a/large-v3-turbo.pt
```

`multilingual=true`、`japanese_supported=true`を3 modelへ設定する。公式READMEのVRAM・相対速度はハードウェアや音声条件で変動する目安であり、GUIは保証値として表示しない。英語専用`.en` modelはcatalogへ入れない。アプリ既定値は公式CLIの現行既定値に追従せず、既存契約どおり`small`とする。

### 6.2 依存・Python環境

- `openai-whisper==20250625`を初期実装の固定値として維持する。
- `pyproject.toml`と`requirements.txt`の値が完全一致することをB1 gateで確認する。
- Python 3.13系列を公式classifier対象の互換性確認環境とする。
- Python 3.14.3は現行実測・補助検証として記録するが、3.14.3だけで受け入れ完了とはしない。
- PyTorchをB1で更新しない。PyInstallerも現行`6.19.0`を基準とし、B1で更新しない。
- 新規HTTP client、hash library、schema libraryを追加しない。JSON、SHA256、path検査は標準ライブラリで実装する。

### 6.3 配置・配布

manifestは`src/core/whisper_models.json`に置く。現行構成ではsource実行とPyInstallerの論理package namespaceは`src.core`、setuptoolsでinstalled packageへ配布されるpackage-data namespaceは`core`である（`pyproject.toml`のpackage discoveryに従う）。`whisper_models.py`は`__package__`に対するpackage-relative resource解決（`importlib.resources`相当）だけを使い、`src.core`、repo root、`sys._MEIPASS`をハードコードしてmanifestを探さない。B1のruntime resource testはsource / frozenの`src.core`に限定する。

setuptools側は`[tool.setuptools.package-data]`の`core = ["whisper_models.json"]`を正本とし、installed treeで`core/whisper_models.json`へ対応することを静的に確認する。PyInstaller側は、現在の`src.core`論理namespaceに合わせ、`src/core/whisper_models.json`をdatasの展開先`src/core`へ明示的に追加する。現行`core/__init__.py`から`src.core`を参照するため、B1ではinstalled `core.whisper_models`のruntime importやinstalled entry point全体のnamespace補修を受け入れ条件に含めない。

model weightsは`src/`、repo root、PyInstaller onefileのいずれにも置かない。`models`ディレクトリとruntime user dataの実ファイルはB2以降で扱い、B1のtestはtemporary directoryまたはfake pathだけを使う。

## 7. 対象ファイル

### 7.1 主変更対象（B1実装時）

| 区分 | ファイル | 責務 |
| --- | --- | --- |
| 新規 | `src/core/whisper_models.json` | schema v1、3 modelの公式metadata、表示目安、package version |
| 新規 | `src/core/whisper_models.py` | manifest DTO、catalog、validator、manifest identity、resource load |
| 新規 | `src/core/whisper_model_loader.py` | verified local checkpoint専用adapter、検証済みbytes load、version / private API gate、alignment heads適用 |
| 新規 | `tests/test_whisper_model_catalog.py` | manifest・catalog・identity・入力拒否・exact metadata |
| 新規 | `tests/test_whisper_model_loader.py` | local-only load、network未到達、alignment heads、fail-closed |
| 既存変更 | `tests/test_whisper_timing.py` | 初回word timestamp実行失敗 / anchorなしからsegment-only実行へ再試行するB1必須回帰 |
| 既存変更 | `pyproject.toml` | `[tool.setuptools.package-data]`へ`core = ["whisper_models.json"]`を追加。dependency値は変更しない |
| 既存変更 | `MMD_AutoLipTool.spec` | `src/core/whisper_models.json`をdatasの展開先`src/core`へ追加。model weightsは追加しない |

### 7.2 関連確認対象（B1では原則変更しない）

- `src/core/whisper_timing.py`: 現行loader、word / segment fallback、FFmpeg PATH補正の回帰境界
- `src/core/pipeline.py`: `whisper_model_name`と`WhisperTimingResult`の既存入口
- `src/gui_wx/analysis_worker.py`: TEXT + audio / voice-onlyのWhisper呼出しとretained timing再利用境界
- `src/gui_wx/main_frame.py`: 現行のmodel name未明示伝播。実接続はB5
- `src/gui_wx/analysis_rollback.py`: model-aware rollback identityの接続先。実変更はB5/B6
- `src/core/settings_store.py`: model key /保存先の実追加はB3
- `src/gui_wx/ui_state.py`、`right_pane.py`: 選択・availability UIはB3/B6
- `src/core/output_diagnostics.py`、`src/core/diagnostic_report.py`、`src/gui_wx/output_diagnostics_adapter.py`:専用diagnosticsはB6
- `.gitignore`: model重みをtracking対象にしない境界確認。B1でruntime fileを生成しない
- `requirements.txt`: `openai-whisper`固定値のread-only一致確認

### 7.3 変更禁止対象

- `presets.json`
- `profiles.json`
- `MMD_AutoLipTool.ini`
- `FFmpeg\bin\`の実体
- MS23 Closeout A、MS22 Closeout Aを記録する文書の状態

## 8. 実装方針

### 8.1 Manifest schemaとcatalog

root objectは次の形に固定する。

```json
{
  "schema_version": 1,
  "openai_whisper_version": "20250625",
  "default_model_key": "small",
  "models": [
    {
      "model_key": "small",
      "display_name": "Whisper small",
      "multilingual": true,
      "japanese_supported": true,
      "official_url": "https://openaipublic.azureedge.net/.../small.pt",
      "filename": "small.pt",
      "sha256": "<64 lowercase hex>",
      "size_bytes": 483617219,
      "vram_hint": "~2 GB",
      "speed_hint": "~4x",
      "recommended_use": "標準・既定モデル"
    }
  ]
}
```

JSONの実体では省略記号やplaceholderを使わず、§6.1の3 URL・SHA256・exact sizeを完全記載する。validatorは次をfail closedする。

- `schema_version`が整数1でない
- `openai_whisper_version`が`20250625`でない
- `default_model_key`が`small`でない
- model key集合が厳密に`small / medium / turbo`でない
- unknown key、重複key、重複filename、重複URL、空文字、型不正
- `.en`、`large`、`large-v3-turbo`などcatalog外のmodel key
- URLがHTTPSかつOpenAI公式Azure host / `main/whisper/models/` pathでない
- URL basenameとfilenameの不一致
- URLのhash path、manifest SHA256、64桁lowercase hexの不一致
- `size_bytes`が正の整数でない、または§6.1の確定値と不一致
- `multilingual`または`japanese_supported`がtrueでない

`WhisperModelSpec`はmanifest由来のimmutable DTOとし、GUIやINIから`official_url`、`filename`、`sha256`、`size_bytes`、package versionを上書きできないようにする。表示文言はloaderへ渡さない。

### 8.2 Manifest identity

下流Blockが同じモデル取得物を識別できるよう、identityを次で固定する。

```text
whisper-manifest-v1:<openai_whisper_version>:<model_key>:<sha256>
```

例:

```text
whisper-manifest-v1:20250625:small:9ecf779972d90ba49c06d968637d720dd632c55bbf19d441fb42bf17a411e794
```

identityはprofile / preset identityや`ms21-effective-output-v1` fingerprintへ混ぜない。`size_bytes`はavailability検証で必ず確認するが、同一SHA256の取得物を同一identityとして扱う。

### 8.3 Verified local checkpoint contract

B1で次のimmutable入力DTOを定義する。B2が通常ファイル、size、SHA256の初回検証を終えた結果だけが、このDTOを生成する。ただし、このDTOは「B2検証時点のattestation」であり、そのpathの内容が将来も不変であることや、loader直前再検証の省略を保証しない。

```text
VerifiedWhisperCheckpoint
  model_key: Literal["small", "medium", "turbo"]
  checkpoint_path: Path
  manifest_identity: str
  sha256: str
  size_bytes: int
```

契約は次のとおりである。

- `checkpoint_path`はsymlink / reparse pointではない通常ファイルのlocal pathだけを受け付ける。URL、model key、directory、`.part`は拒否する。
- `model_key`はcatalogのspecと一致しなければならない。
- `manifest_identity`、SHA256、sizeはcatalogと一致しなければならない。
- B1 loaderはraw `Path`や任意文字列を受け取るpublic entryを持たない。
- B1 loaderはinput DTO / catalog metadataを再照合したうえで、checkpointを一度だけreadし、実読取byte数 / SHA256を確認した同じbytesをmodel loadへ渡す。B2でverifiedとなったことだけを理由にloader内の検証を省略しない。
- loader内部の一時`VerifiedCheckpointBytes`は、検証済みbytes、byte数、SHA256、manifest identityを保持するが、永続化せず、下流Blockへ公開しない。
- B2はavailability判定とDTO生成時の初回実ファイル検証を所有する。B5は選択済みidentityを伝播し、single-active cacheのcache miss / reload時に必ずB1 loaderへDTOを渡す。B5がraw pathを直接loadしたり、独自の簡易検証でB1 gateを迂回したりしない。
- B1のunit testは小さなfake checkpointとtest用catalog fixtureを使い、実重みを取得しない。production manifestのexact metadata検証は緩めない。

### 8.4 Network-unreachable loader

`load_verified_local_checkpoint()`相当のadapterは、次の順で処理する。

1. catalogとcheckpoint DTOのmodel key / manifest identity / SHA256 / sizeを照合する。
2. `whisper`をimportし、`whisper.__version__ == "20250625"`を確認する。
3. `whisper._ALIGNMENT_HEADS`がdictで、model keyが存在し、値が空でない`bytes`であることを確認する。bytes loadに必要なv20250625の`ModelDimensions`、`Whisper`、`torch.load`契約も確認する。
4. `lstat`相当でmissing、directory、`.part`、symlink / Windows reparse pointを拒否し、通常ファイルだけをbinary readで開く。
5. 同じopen handleを先頭から末尾までstreaming読取し、実読取byte数とSHA256をcatalog / DTOの`size_bytes` / `sha256`へ照合する。読取前後の`fstat`とpath側identityを比較し、読取中のtruncate、in-place変更、rename / replaceを検出した場合もloadしない。
6. 検証済みopen handleから得たbytesをloader内部の一時bufferへ保持し、`torch.load(io.BytesIO(verified_bytes), map_location=device, weights_only=True)`で同じbytesをloadする。検証後にcheckpoint pathを再openせず、`whisper.load_model(path)`、model key、公式URL、`download_root`は使わない。
7. v20250625の`ModelDimensions` / `Whisper`でmodelを構築し、`load_state_dict()`後に`whisper._ALIGNMENT_HEADS[model_key]`をcallableな`set_alignment_heads()`へ適用する。必要private symbolが欠落・形式不正ならfail closedする。
8. bytes loadまたはalignment heads適用の例外をstructured loader errorへ変換し、成功結果を返さない。
9. model objectとmodel identityを下流が保持できるimmutable loaded handleへ包む。cache、eviction、unloadのownershipはB5で実装する。

B1 v1で採用するTOCTOU対策は、検証済みopen handleから得たbytesをそのままmodel loadへ渡すことである。実装時の裁量で「B2のDTOは検証済みだからhash省略」「mtime / sizeだけで代替」「`is_file()`確認後にpathを再open」「`whisper.load_model(path)`へ委譲」へ弱めない。medium / turboではcheckpoint bytes分の一時host memoryを要するため、memory errorではloaded handleを返さない。旧active modelを維持するのはB3〜B6の適用統合契約であり、B1 loaderはUiStateを変更しない。将来、検証済みfile descriptorを実load完了まで拘束する方式へ変更する場合は、同じbytes bindingを失わないこと、Whisper local loaderとの互換性、Windows file sharingを別計画で再確認する。

failure codeは、missing / directory / `.part` / symlink / reparse pointを`checkpoint_path_invalid`、openまたはstreaming read中のPermissionError / OSErrorなどpath invalid以外のI/O失敗を`checkpoint_read_failed`、bytes読取時のsize / SHA256不一致を`checkpoint_integrity_mismatch`、読取中のfile identity / metadata変化を`checkpoint_changed_during_revalidation`、`torch.load` / `ModelDimensions` / `Whisper` / `load_state_dict`によるbytesからのmodel構築失敗を`checkpoint_bytes_load_failed`とする。path検査・read・integrity・file changeの失敗ではbytes loaderを0回とし、bytes構築失敗ではbytes loaderを1回試行したうえでloaded handleを返さない。全failureで公式`whisper.load_model()`、`_download()`、network API、旧model fallback、成功handle返却を行わない。

adapter内部で`whisper.load_model()`、`whisper._download()`、`urllib.request.urlopen()`などのnetwork到達経路やpath再open経路を使わない。v20250625のlocal-path branchがalignment headsを設定しないため、bytesから構築したmodelへhead適用を省略しない。

### 8.5 Error contract

B1のloaderは、少なくとも次の分類を持つ。

- `manifest_invalid`
- `model_key_unsupported`
- `checkpoint_not_verified`
- `checkpoint_path_invalid`
- `checkpoint_integrity_mismatch`
- `checkpoint_changed_during_revalidation`
- `whisper_package_missing`
- `whisper_version_mismatch`
- `alignment_heads_api_missing`
- `alignment_heads_key_missing`
- `alignment_heads_format_invalid`
- `alignment_heads_apply_failed`
- `checkpoint_read_failed`
- `checkpoint_bytes_load_failed`

これらはUI文言ではなく、B5/B6が既存`WhisperTimingError`、recoverability、rollback禁止classへ写像できる安定codeとする。B1でGUIメッセージや診断summaryを追加しない。

### 8.6 Package / dependency境界

- manifestはsource / frozen package resourceとして読めるようにし、installed packageでは`core/whisper_models.json`のpackage-data配置マッピングを静的に確認する。B1でinstalled `core.whisper_models`のruntime importは受け入れない。
- model weights、download cache、`.part`、ユーザー選択保存先はpackage dataへ含めない。
- package-data設定を追加しても依存versionは変更しない。
- `requirements.txt`は`pyproject.toml`と`openai-whisper==20250625`を一致させたままにする。
- license / release readinessの最終判定はMS27へ残す。B1ではWhisper code / weightsがMITであることを前提情報として記録し、配布文書の最終同期はB7へ委譲する。

## 9. 詳細ステップ

### Step 0: 実装開始前のread-only gate

- `git status --short --branch`、branch、HEADを一つずつ確認する。
- `MS24_Block_Breakdown`、本plan、現行`whisper_timing.py`、pipeline、worker、settings、spec、testsを再読する。
- 公式v20250625のURL、SHA256、filename、Content-Lengthを確認する。公式metadataを取得できない場合はplaceholderを入れず、B1を実装開始しない。
- `pyproject.toml` / `requirements.txt`のversion一致、Python 3.14.3のclassifier外、Python 3.13確認対象を記録する。
- runtime user dataの実体を読まず、`git check-ignore` / `git ls-files`などのpath-level確認だけに限定する。

### Step 1: ManifestとDTO

- `src/core/whisper_models.json`をschema v1で追加する。
- `WhisperModelSpec`、manifest DTO、catalog取得関数、strict validator、identity生成を追加する。
- catalogの順序を`small, medium, turbo`に固定し、defaultを`small`にする。
- display name、VRAM、速度、用途目安はmetadataとして保持するが、model loadの引数にしない。

### Step 2: Loader adapter

- `VerifiedWhisperCheckpoint`とloaded handleを追加する。
- package version、private alignment-head API、checkpoint DTO、local regular-file属性の順にgateする。
- B2検証後にpath内容が差し替えられても未検証bytesをloadしないよう、同じopen handleから実byte数 / SHA256を全量streaming検証し、そのbufferをbytes loaderへ渡す。
- v20250625の`ModelDimensions` / `Whisper` / `torch.load(io.BytesIO(...))`を使うlocal bytes loaderを実装し、local path branchの再open、公式model key、`download_root`経路を使わない。
- alignment headsを公式private mappingから明示適用し、必要なmodel constructor / `set_alignment_heads()`が欠落した場合はfail closedする。
- B1 error codeを例外またはstructured resultへ固定する。

### Step 3: Resource / package boundary

- source実行（`src.core`）とPyInstaller onefile（`src.core`）で、同じpackage-relative resource解決がmanifestを返す構造を確認する。
- `pyproject.toml`の`[tool.setuptools.package-data] core = ["whisper_models.json"]`がinstalled treeの`core/whisper_models.json`へ対応することを静的に確認し、`MMD_AutoLipTool.spec`の`(src/core/whisper_models.json, src/core)`相当のdatasを明示的に追加する。manifestだけをpackage / onefile data候補とし、model weightsは追加しない。installed `core.whisper_models`のruntime importと既存アプリ全体のinstalled entry point import補修はB1へ持ち込まない。
- model weights、root runtime user data、FFmpeg実体に触れない。

### Step 4: B1 tests

- catalogのexact metadata、schema、key、URL、SHA256、size、default、`.en`拒否をテストする。
- loaderのlocal path only、verified DTO不一致、package version不一致、private API欠落・形式不正、alignment apply失敗をテストする。
- B2検証済みDTO生成後に同一pathを別内容へreplaceした場合、size同一・size相違の双方で検証済みbytes以外がloadされず、bytes loaderが0回となる回帰を追加する。directory、`.part`、symlink / reparse point、検証中のtruncate / replaceもfail-closed対象にする。
- 検証完了後からbackend readまでの差し替えを模擬し、path再openなしで検証済みbytesだけがmodel構築へ渡ることを確認する。
- fake Whisper module / fake modelを使用し、実モデル重みを取得・ロードしない。
- `urllib.request.urlopen`、Whisper `_download`相当のnetwork seamをpatchし、loaderから呼ばれないことを確認する。
- 既存`tests/test_whisper_timing.py`のword優先・同一初回結果内の疎word時segment選択に加え、初回`word_timestamps=True`が例外となる場合と、word / segment双方のusable anchorなしを返す場合を別caseにし、どちらも`word_timestamps=False`で1回だけ再試行することを必須回帰として追加する。
- `tests/test_ms19_b4_analysis_worker_voice_only.py`の`small`既定・voice-only初回Whisper callと、`tests/test_ms19_b5_transcription_edit_state.py`の保持timing再利用を回帰する。

### Step 5: 実装後の境界監査

- B1のdiffにB2〜B7のUI、settings、download、diagnostics、report、cache/unload、runtime dataが混入していないことを確認する。
- B2の初回availability検証やDTO生成、B5の解析伝播 / cache ownershipを先行実装していないことを確認する。一方、B1 loader自身の検証済みbytes binding / bytes loadはB2/B5へ先送りしない。
- `pyproject.toml` / `requirements.txt`の依存値が変わっていないことを確認する。
- manifestがpackage dataへ入り、model weightsがspecへ入っていないことを静的に確認する。
- `git diff --check`を実行する。

## 10. 状態遷移 / データ契約

### 10.1 Catalog

```text
manifest bytes
  -> JSON parse
  -> schema / exact metadata validation
       ├─ invalid -> manifest_invalid（catalog unavailable）
       └─ valid -> CatalogReady(default=small)
```

CatalogReadyはmodelが保存済み・load済みであることを意味しない。download / availabilityはB2/B4が所有する。

### 10.2 Loader

```text
raw path / model key / URL
  -> reject（B1 loader inputではない）

VerifiedWhisperCheckpoint
  -> DTO / catalog identity check
       ├─ mismatch -> checkpoint_not_verified
       └─ match
            -> exact package version check
            -> private alignment-head API check
                 ├─ fail -> fail closed
                 └─ pass
                      -> non-symlink local regular-file check
                      -> 同じopen handleから検証済みbytesをstreaming読取
                      -> 読取前後のfile identity / metadata照合
                           ├─ open / read I/O failure -> checkpoint_read_failed / bytes loader 0回でfail closed
                           ├─ mismatch / changed -> bytes loader 0回でfail closed
                           └─ pass -> 検証済みbytesをlocal bytes loaderへ渡す
                                        -> model構築 / alignment heads apply
                                             ├─ fail -> load failure
                                             └─ pass -> LoadedWhisperModel
```

B1 adapterの状態に`downloading`や`retrying`を設けない。network処理はB4のforeground workerだけが所有する。

- B1はDTO schema、stable error code、検証済みbytesへのload bindingを含むloader入口を定義・実装する。
- B2は保存先上のartifactを通常ファイル / size / SHA256で初回検証し、その時点の`VerifiedWhisperCheckpoint`を生成する。B2のverified状態は、将来のpath内容を保証しない。
- B5はresolved model identityとB2のDTOを解析経路へ伝播し、single-active cacheのcache miss / reloadごとにB1 loaderを呼ぶ。B5はraw path load、再検証省略、別loaderへのfallbackを行わない。

### 10.3 下流へのidentity引き渡し

以下のselected / active / analysis identityと二段階切替は、B3〜B6が実装するための引き渡し契約である。B1では契約、loaded handleのidentity、stable error codeを定義するだけで、UiState変更、active modelのcommit、解析結果の無効化・復元を実装しない。

- `LoadedWhisperModel.model_key`と`manifest_identity`は、B5がAnalysisWorker / pipelineへ渡すために保持する。
- B3のselection identity、B5のanalysis identity、B6のdiagnostics identityはこの値を参照する。
- `selected_model_key`はユーザーが選んだ切替候補、`active_model_identity`はload成功後に適用中のモデル、`analysis_model_identity`は現在の解析結果を作成したモデルとして分離する。
- selected candidateとactive model identityを別々に永続化し、未Applyのcandidateは再起動後も候補表示だけに留める。再起動時にactive checkpointが未配置・未検証でも自動downloadや旧modelへの暗黙fallbackを行わず、明示`Download & Verify`と`Apply and Re-analyze`を要求する。
- 候補選択はnetwork、model load、既存解析の無効化を起こさない。`active_model_identity`は、download・検証済みbytes load・alignment heads適用がすべて成功した後だけ更新する。
- 適用失敗（integrity、bytes load、alignment heads、memoryを含む）時はactive model、既存の成功解析、Preview、VMD saveabilityを変更せず、候補をactive modelへ戻せる状態を返す。旧modelへの暗黙fallback loadは行わない。
- 適用成功後は`analysis_model_identity`とactive identityが一致するまで、旧解析結果のPreview / diagnostics success / VMD saveabilityを無効化し、active modelでの再解析を要求する。
- `analysis_rebuild_reason`、rollback禁止class、single-active ownershipはB1でDTOの予約境界だけを定義し、実装はB3〜B6で行う。
- Whisper identityを既存`ms21-effective-output-v1` fingerprintへ追加しない。

### 10.4 既存timing契約

- `recognize_audio_timing()`のword timestamp優先を維持する。
- 同一の`word_timestamps=True`結果でword anchorが1件以下かつsegment anchorがより多い場合、その初回結果のsegmentを選ぶ既存fallbackを維持する。この分岐はsegment-only再試行ではない。
- 初回`word_timestamps=True`実行が失敗した場合、または初回結果にusableなword / segment anchorがともにない場合だけ、`word_timestamps=False`で再試行する既存segment-only retryを維持する。
- model identityを追加する場合も、既存`WhisperTimingResult`のanchors / raw_result / source意味を変更しない。B5でidentityを別フィールドまたはloaded handleから保持する。
- voice-onlyの同一model・同一manifestでの書き起こし編集時だけretained timingを再利用する判定はB5が所有し、B1はloaderへretained resultを持ち込まない。

## 11. テスト方針

### 11.1 Catalog tests

- 正常な3 model、default `small`、multilingual / Japanese flags
- schema version、root / entry unknown key、duplicate key / URL / filename
- `.en`、未知model、任意URL、非HTTPS、公式host外、path外
- URL basenameとfilename、URL hashとSHA256、64桁hex
- exact `size_bytes`、0 /負数 / float / bool、未確定sizeの拒否
- display / vram / speed / recommended-useの非空metadata
- identityの決定性とmodel key / SHA256差による分離

### 11.2 Loader tests

- 成功系ではverified local checkpointを一度だけreadし、検証済みbytesがbytes loaderへ渡され、model key / manifest identityを保持したloaded handleが返ること。active modelの維持はB3〜B6の統合受け入れ条件とする。
- model key、`download_root`、公式URLをloader callへ渡さない
- `whisper.load_model(path)`、path再open、`whisper._download()`へ到達しないこと
- fake network seamが0回であること。選択・catalog load・local loadで`urlopen`等へ到達しないこと
- missing file、directory、`.part`、symlink / reparse point、DTO identity mismatchの拒否
- B2検証済みDTO作成後のsame-path replace、size同一内容差し替え、size相違差し替え、検証中のtruncate / replaceを、実byte数 / SHA256とfile identity / metadata照合で拒否すること
- 検証直後にpathを差し替えても、検証済みbytesだけが`torch.load(io.BytesIO(...))`へ渡り、差し替え後bytesやpath再open結果がloadされないこと
- package missing、version mismatch、`_ALIGNMENT_HEADS` missing、unknown key、non-bytes、empty bytes、`set_alignment_heads`欠落
- `ModelDimensions` / `Whisper` / `torch.load`のbytes構築API欠落・例外をfail closedすること
- local load exception、alignment apply exceptionのfail-closed
- open / streaming read中のPermissionError / OSErrorなどを`checkpoint_read_failed`へ写像し、bytes loader 0回・loaded handleなしでfail closedすること
- verified bytes bufferの確保またはbytes loadでmemory errorが発生した場合、`checkpoint_bytes_load_failed`としてloaded handleを返さないこと。active modelを変更しないことはB3〜B6の統合受け入れ条件とする。
- small / medium / turboそれぞれで正しいprivate alignment-head valueが選ばれること
- loaded handleがmodel key / manifest identityを失わないこと

### 11.3 Existing timing regression

- `tests/test_whisper_timing.py`の現行証拠: 複数word anchor優先、同一初回結果内の疎word時segment選択、FFmpeg PATHの一時補正。
- `tests/test_whisper_timing.py`へ追加するB1必須証拠: `recognize_audio` mockを、(a) 初回`WhisperTimingError`、(b) 初回にusableなword / segment anchorなし、の2 caseで構成する。各caseでcall順が`word_timestamps=True`、次に`False`の計2回であり、2回目のsegment結果を`source="segments"`として返すことを確認する。疎word testでは`False`再試行がないことも区別して確認する。
- `tests/test_ms19_b4_analysis_worker_voice_only.py`: `small` defaultとvoice-only初回Whisper call。retained timing再利用の現行証拠には使わない。
- `tests/test_ms19_b5_transcription_edit_state.py`: voice-only書き起こし編集時のretained timing再利用。
- `tests/test_pipeline_and_vmd.py`: Whisper失敗時に`even_fallback`、warning、observationsへ復帰する現行pipeline回帰。現行fileはmodel name伝播をassertしていない。
- model nameの`MainFrame -> AnalysisWorker -> pipeline -> whisper_timing / B1 loader`明示伝播はB5責務とし、将来の`tests/test_ms24_whisper_model_propagation.py`で`small / medium / turbo`、TEXT + 音声 / voice-only、default引数への意図しないfallthroughなしを確認する。B1の既存testをその証拠として扱わない。
- `tests/test_ms21_b7_analysis_rollback.py`: 現行rollbackの既存契約を壊さないこと。model-aware禁止classの追加はB5/B6で行う

### 11.4 Namespace / package tests

- source treeでは`src.core.whisper_models`を直接importして、package-relative resourceからmanifest catalogを読めること
- installed package treeでは`core/whisper_models.json`のpackage-data配置マッピングを静的に確認すること。`core.whisper_models`のruntime importはB1の検証対象にしない
- `whisper_models.py`が`__package__`のpackage-relative resourceだけを使い、repo rootや固定`src.core` pathへ依存しないこと
- source resource pathとfrozen resource pathの解決境界をfake rootで確認すること
- `pyproject.toml`のpackage-dataが`core/whisper_models.json`へ対応し、PyInstaller datasが`src/core/whisper_models.json`を`src/core`へ配置すること
- manifestはpackage dataへ含めるが、model weight fileをspecへ追加しないこと。既存アプリ全体のinstalled entry point起動可否はB1のpackage resource testで判定しない

### 11.5 実行順と合格基準

1. B1 catalog tests
2. B1 loader tests
3. `tests/test_whisper_timing.py`
4. `tests/test_ms19_b4_analysis_worker_voice_only.py`
5. `tests/test_ms19_b5_transcription_edit_state.py`
6. `tests/test_pipeline_and_vmd.py`
7. `tests/test_ms21_b7_analysis_rollback.py`
8. `compileall src tests`
9. `git diff --check`

各pytestはpass表示だけでなくprocess exit code `0`を必須とする。実重みdownload、外部ネットワーク、GUI、実MMDはB1の検証へ含めない。Python 3.13系列での互換性確認は別の環境実測として実施し、現行3.14.3のpassだけで代替しない。

## 12. 受け入れ条件

### Catalog / manifest

- [ ] `src/core/whisper_models.json`がschema v1で、`small / medium / turbo`だけを含む。
- [ ] defaultは`small`である。
- [ ] 3 modelのofficial URL、filename、SHA256、exact `size_bytes`が§6.1の値と一致する。
- [ ] `openai_whisper_version`が`20250625`である。
- [ ] multilingual / Japanese flags、VRAM目安、相対速度目安、用途表示がmanifestに固定される。
- [ ] `.en`、未知model、任意URL、unknown key、duplicate、size未確定、不正hashはfail closedする。
- [ ] manifest identityが決定的で、profile / preset / output fingerprintと混ざらない。

### Verified-local loader

- [ ] loaderは`VerifiedWhisperCheckpoint`だけを入力とし、raw path / model key / URLを解析loaderの入口にしない。
- [ ] B2のverified DTOだけを永続的な保証として扱わず、同じopen handleからsize / SHA256を確認した検証済みbytesだけをmodel構築へ渡す。
- [ ] B2検証後のsame-path replace、size同一 / 相違の内容差し替え、検証中のfile change、directory、`.part`、symlink / reparse pointは、差し替え後pathを再openせずfail closedする。
- [ ] loaderは`whisper.load_model()`、model key、`download_root`経路を使わず、`torch.load(io.BytesIO(verified_bytes))`を含むv20250625 bytes loaderだけを使う。
- [ ] loaderのunit testでnetwork API未到達が確認される。
- [ ] `whisper.__version__`とmanifest versionの不一致、private alignment-head API不一致、未知key、不正checkpointはload開始前またはload中にfail closedする。
- [ ] v20250625のmodel key対応alignment headsが検証済みbytesからのmodel構築後に適用される。
- [ ] model / manifest identityをloaded handleへ保持する。
- [ ] open / streaming read中のI/O failureを`checkpoint_read_failed`へ安定写像し、bytes loader 0回・loaded handleなしでfail closedする。
- [ ] `selected_model_key`、`active_model_identity`、`analysis_model_identity`を分離し、候補選択だけでは既存解析を無効化しない契約が、B3〜B6への引き渡し条件として文書化されている。B1実装はこのstate transitionを実装しない。
- [ ] `Apply and Re-analyze`成功後だけ旧解析を無効化し、適用失敗時はactive modelと既存成功解析を維持する契約が、B3〜B6の後続受け入れ条件として明示されている。B1の実装合否はloaded handle、stable error、bytes bindingで判定する。
- [ ] selected candidateとactive model identityを別々に永続化し、未Apply候補を再起動後も候補表示だけに留め、active未配置・未検証時に自動download / fallbackしない契約がB3〜B6への引き渡し条件として明示されている。

### 回帰・境界

- [ ] 複数word anchor優先、同一初回結果内の疎word時segment選択、初回失敗 / anchorなしからの`word_timestamps=False`再試行、FFmpeg PATH補正が、互いに混同されない独立した回帰で維持される。
- [ ] `tests/test_pipeline_and_vmd.py`はWhisper失敗時のeven fallback証拠として扱い、model name伝播はB5の将来専用testで確認する。
- [ ] B1 loader入口、B2の初回検証済みartifact / DTO生成、B5のidentity伝播・loader呼出しという責務境界が固定され、B1実装でB2/B5を先行実装しない。
- [ ] `pyproject.toml`と`requirements.txt`のWhisper依存値が一致し、B1でversion updateを行わない。
- [ ] `pyproject.toml`の`[tool.setuptools.package-data] core = ["whisper_models.json"]`と`MMD_AutoLipTool.spec`の`(src/core/whisper_models.json, src/core)`相当のdatasにmanifestだけを追加し、model weightsをpackage / onefileへ含めない。
- [ ] sourceの`src.core.whisper_models`とPyInstaller onefileの`src.core.whisper_models`が、package-relative resource解決で同じmanifestを読める。installed packageは`core/whisper_models.json`のpackage-data配置マッピングを静的に確認し、`core.whisper_models`のruntime importと既存アプリ全体のinstalled entry point namespace補修はB1の合否に含めない。
- [ ] Python 3.14.3は公式classifier外の補助環境として記録され、Python 3.13系列を互換性確認対象として明示する。
- [ ] manifestだけがpackage / onefile data候補となり、model weights、runtime user data、`.part`は含まれない。
- [ ] MS23の固定モーフ、Latin profile、preset、diagnostics、fingerprint、VMD 30fps、MMD用WAV契約を変更しない。
- [ ] B1の実装でUI、settings、download、analysis propagation、diagnostics、single-active cacheを先行実装しない。
- [ ] 実network、実モデルdownload、GUI、実MMD確認を実施済みと記録しない。
- [ ] pytest / compileall / diff checkがすべてprocess exit code 0である。

### 計画レビュー再確認（2026-08-21）

| 指摘 | 計画上の反映 | 実装・test状態 |
| --- | --- | --- |
| P1 | 今回提示されたレビューにP1指摘はない | B1実装後に別途判定する |
| P2-1 | 検証済みopen handleから得たbytesだけをmodel構築へ渡し、path再openを禁止するTOCTOU対策、replace / symlink / directory / `.part` / race時のfail-closed、B1 / B2 / B5責務を本文・step・data contract・test・受け入れ・riskへ固定 | B1は`eafdc16`で実装済み。B2 / B5は後続Block |
| P2-2 | word優先、同一run内の疎word時segment選択、segment-only retryを分離し、初回失敗 / anchorなしの2 caseをB1必須testへ固定 | `eafdc16`のB1 test対象へ反映済み |
| P3 | `tests/test_pipeline_and_vmd.py`の現行証拠をWhisper失敗時even fallbackへ訂正し、model name伝播をB5将来testへ移管 | B5実装は未開始 |
| Main-P2-1 | Block Breakdownに残っていた「選択変更時の即時解析無効化」とpath loader契約を、承認済み二段階切替・verified bytes loader契約と同期 | Block BreakdownのB3/B5/state/identity/受け入れ条件を同期済み。B1 loaderは`eafdc16`で実装済み |
| Main-P2-2 | B1受け入れ条件に混在していたB3〜B6のstate transitionを、B1の契約定義と後続Blockの実装受け入れへ分離 | B1実装合否をloaded handle / stable error / bytes bindingへ限定し、後続契約をhandoff条件として明記 |
| Main-P3-1 | `checkpoint_bytes_load_failed`時のbytes loader呼出し回数と公式Whisper loader 0回の意味が曖昧 | validation failureはbytes loader 0回、bytes構築失敗は1回試行・handleなし、全failureで公式loader/network 0回へ明記 |
| Recheck-P2-1 | loader成功系までloaded handleを返さないように読めるtest記述 | 成功系はidentity付きloaded handleを返し、memory / bytes構築失敗などのfailureだけhandleなしへ補正 |
| Recheck-P2-2 | 再起動時のselected candidateとactive model identityの復元契約が未定義 | 両identityを分離永続化し、未Apply候補は候補表示だけ、active未配置・未検証時は自動download / fallbackなしへ補正 |
| Recheck-P2-3 | manifest package-data / PyInstaller datas追加が条件付きで、現行設定では配置漏れを防げない | `pyproject.toml`と`MMD_AutoLipTool.spec`のmanifest追加をB1必須対象へ変更 |
| Recheck-P2-4 | checkpoint open / streaming read I/O failureのstable errorとbytes loader回数が未定義 | `checkpoint_read_failed`、bytes loader 0回、loaded handleなし、fake I/O回帰を追加 |
| Recheck-P3-1 | `tests/test_whisper_timing.py`のB1 / B5責務境界がBlock Breakdownとplanで不一致 | B1の主変更対象へ追加し、segment fallback / retry回帰をB1必須testとして同期 |
| Recheck-P2-5 | source / installed package / PyInstallerのpackage namespaceとmanifest配置先が未固定。現行setuptoolsは`core`、source / frozen importsは`src.core` | `__package__`基準のresource解決、setuptools `core = ["whisper_models.json"]`、PyInstaller `src/core`展開先、3経路のnamespace別testを明記。既存アプリ全体のinstalled entry point namespace補修はB1外へ分離 |
| Recheck-P2-6 | `core.whisper_models`のinstalled runtime importが、現行`core/__init__.py -> src.core.*`混在importのためisolated packageで成立しない | installed packageは`core/whisper_models.json`のpackage-data配置マッピングを静的確認する契約へ限定し、source / frozen runtime resource testとinstalled entry point namespace補修を分離 |

この表の「計画上の反映」は文書レビュー指摘とユーザー採用方針の計画反映を示し、production code / test codeの実装済み・検証済みを意味しない。

## 13. リスクと対策

| ID | リスク | 重要度 | 対策 |
| --- | --- | --- | --- |
| MS24-B1-R1 | model keyを公式loaderへ渡して未配置時に暗黙downloadする | P1候補 | verified local checkpoint DTOだけを受けるadapterと、network seam 0回のtestを固定する |
| MS24-B1-R2 | bytes loadでalignment headsが設定されずword timing品質が変わる | P1候補 | v20250625 version gate、private mapping存在確認、bytesからのmodel構築、`set_alignment_heads()`適用、word / segment回帰を固定する |
| MS24-B1-R3 | private APIの将来変更を同一versionと誤認する | P2候補 | package version exact match、key / bytes / callable検査、全不一致fail closed。依存更新は別gateへ戻す |
| MS24-B1-R4 | exact sizeを丸め値や推測値で固定する | P2候補 | 公式配布先Content-Lengthを実測し、manifest・test・precheckで一致確認。取得不能時は実装停止 |
| MS24-B1-R5 | `turbo` keyと`large-v3-turbo.pt` filenameを混同する | P2候補 | URL basenameをfilename正本とし、key / filenameを別fieldで検証する |
| MS24-B1-R6 | manifestがfrozen packageから欠落する | P2候補 | source / setuptools package-data / PyInstaller datasを別々に確認する |
| MS24-B1-R7 | Python 3.14.3だけで互換性完了と判定する | P2候補 | 3.14.3は補助実測、3.13系列を受け入れ対象として別実行する |
| MS24-B1-R8 | B1へUI、download、cache、diagnosticsを混ぜて責務が崩れる | P2候補 | B1/B2/B3/B4/B5/B6の依存順と変更対象表を受け入れ条件へ固定する |
| MS24-B1-R9 | model weightsやruntime user dataを誤ってGit / packageへ含める | P1候補 | B1では実体を作らず、manifestのみを対象とし、spec・Git境界を静的確認する |
| MS24-B1-R10 | loader errorを既存Whisper timing errorへ早期に潰し、B5/B6でrecoverabilityを判別できなくなる | P2候補 | B1でstable error codeを保持し、UI文言・rollback投影はB5/B6で明示的に写像する |
| MS24-B1-R11 | B2のverified DTOを永続的な保証と誤認し、検証後に差し替えられた未検証checkpointをloadする | P2候補 | B1 loaderで同じopen handleからsize / SHA256を確認したbytesだけをmodel構築へ渡し、path再openなしとB2後replace回帰を固定する |
| MS24-B1-R12 | 疎word時の同一run内segment選択と、`word_timestamps=False`へのsegment-only retryを同じ証拠として扱い、retry分岐の回帰を見逃す | P2候補 | 初回失敗 / anchorなしの2 caseでcall順と`False`再試行を直接assertし、既存疎word caseとは分離する |
| MS24-B1-R13 | `test_pipeline_and_vmd.py`をmodel name伝播の存在しない証拠として扱う | P3候補 | 現行fileはeven fallback証拠へ限定し、small / medium / turboの明示伝播はB5専用testで確認する |
| MS24-B1-R14 | 候補選択の失敗で既存解析を失い、または適用失敗後に旧modelへ暗黙fallbackする | P2候補 | selected / active / analysis identityを分離し、適用成功後だけ旧解析を無効化、失敗時はactive modelと既存成功解析を保持する |

## 14. Codex実装時の注意

- コマンドは一つずつ実行し、parallel、pipeline、`&&`、`||`、`;`で連結しない。
- 実装開始時にlive Git state、MS17 / MS20 routing、MS24 Block Breakdown、本plan、関連code / testsを再確認する。
- `presets.json`、`profiles.json`、`MMD_AutoLipTool.ini`は内容を読まず、作成・変更・削除・stageしない。
- 本plan作成セッションではproduction code / test code / GUIを変更しない。B1実装開始後は、§7.1のB1対象だけを最小変更し、B2〜B6の責務へ拡張しない。
- `openai-whisper==20250625`を維持し、GitHub main、未tag commit、PyTorch同時更新を採用しない。
- 実重みdownload、公式配布先へのGET、network smokeをB1 testへ含めない。公式metadataのread-only HEADは実装前gateでのみ行う。
- `whisper.load_model()`へmodel keyや`download_root`を渡す旧経路の置換はB5の責務であり、B1のcatalog / adapter実装だけで全アプリ解析が安全化したとは報告しない。
- local checkpoint bytes loaderのprivate API契約を緩めない。不一致時にalignment headsを既定値へ戻して続行しない。
- B2の`VerifiedWhisperCheckpoint`を受け取っても、B1 loaderは同じopen handleから得たsize / SHA256確認済みbytesをそのままmodel構築へ渡す。`is_file()`、mtime、sizeだけで代替せず、path再open、差し替え・symlink / reparse point・directory・`.part`をfail closedする。
- B5ではcache miss / reload時にB1 loaderを必ず通し、raw path loadや別loader fallbackを追加しない。B2の初回検証とB5の伝播 / cache実装はB1セッションへ混ぜない。
- `tests/test_whisper_timing.py`では、疎word時segment選択とsegment-only retryを別testとして保持する。`tests/test_pipeline_and_vmd.py`をmodel name伝播の証拠として報告しない。
- B3/B4のユーザー向け切替では、候補選択、取得・検証、適用を分離し、適用成功後だけactive modelを更新する。適用失敗時に既存解析を破棄したり、旧modelへ暗黙fallback loadしたりしない。
- package-data / spec変更が必要になった場合も、model weightsとruntime dataを絶対に追加しない。
- `git diff --check`、pytestのpass表示、process exit codeを別々に記録する。exit code非zeroをpass扱いしない。
- 実装完了後も、MS23 Closeout A、MS22 Closeout A、MS26 actual-MMD deferred、MS27 package / release境界を変更しない。
- stage、commit、push、merge、tag、releaseは別途明示承認なしに行わない。
