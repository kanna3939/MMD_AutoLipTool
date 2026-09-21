# MS24-B2 Implementation Plan

## 1. 文書情報

- 対象マイルストーン: `MS24 Whisper Model Selection`
- 対象Block: `MS24-B2 モデル保存先・availability・整合性検証`
- 作成日: 2026-08-22
- 作成時branch: `feature/MS23-implementation`
- 作成時HEAD: `eafdc16 Implement MS24-B1 Whisper model contract`
- 直接依存: `MS24-B1 Whisperモデル契約・versioned manifest・互換性ゲート`
- 後続依存: MS24-B3、MS24-B4、MS24-B5
- 文書状態: **Implementation Plan / Implemented at `b011b37` / Targeted Verification Passed**
- 本文書の権限: 本文書だけ。production code、test code、GUI、依存関係、runtime user dataは変更しない

MS24-B2の実装開始時には、B1が実装済みであり、次の契約が正本であることを前提とする。

- `src/core/whisper_models.json` の `small / medium / turbo` catalog
- manifest identity、公式filename、exact `size_bytes`、SHA256
- `VerifiedWhisperCheckpoint` DTO
- verified local checkpointの再検証とnetwork-unreachable bytes loader
- `openai-whisper==20250625`、v20250625 alignment heads、fail-closed loader

## 2. 背景

MS24-B1で、モデル重みを解析loaderへ安全に渡すためのmanifestとverified-local loaderが固定された。B2では、実際にモデル重みを保存するローカル領域を決め、保存済みファイルの物理状態を検査し、B1の`VerifiedWhisperCheckpoint`を生成する。

現行コードとの照合で確認した事実は次のとおりである。

- `src/core/settings_store.py` はfrozen時にexe隣接、source時にrepo rootを設定ファイルの基準位置として解決する。
- `src/resource_utils.py` は`sys._MEIPASS`またはsource配置から読み取り用resourceを解決する。onefileの展開先であり、永続モデル保存先の基準には使用できない。
- `SettingsStore` は同一directoryのtemporary fileをcloseしてから`os.replace()`するatomic保存パターンを持つ。
- `src/core/whisper_models.py` は公式filenameからmanifest identityを構築できる。`turbo`のmodel keyと`large-v3-turbo.pt`のfilenameは別フィールドである。
- `src/core/whisper_model_loader.py` はB2が作成したDTOを受け取り、loader直前に同一open handleから再検証する。B2の検証結果だけを永続的な安全保証として扱わない。
- 現行`.gitignore`には`presets.json`、`profiles.json`、`MMD_AutoLipTool.ini`のroot限定ignoreはあるが、モデル保存先`models`のignoreはない。
- 現行にはWhisper専用の保存先、availability、download staging、モデル重みの検証storeは存在しない。

したがって、B2はUIやHTTP処理を追加せず、B4以降が再実装しないfilesystem境界をUI非依存coreへ固定する。モデル重みはsource、repo rootの追跡対象、PyInstaller onefileへ追加しない。

## 3. 目的

1. source実行とfrozen実行で、ユーザーが理解できる決定的なモデル保存先を解決する。
2. `whisper_models_dir`だけを設定へ保存し、空文字を安全な既定保存先として扱う。
3. canonical filename、通常ファイル、exact size、streaming SHA256、file identityを検査する。
4. 検証済み重みだけからB1の`VerifiedWhisperCheckpoint`を生成する。
5. `.part`、不正ファイル、異なるmanifestの重みをavailable扱いしない。
6. B4のforeground downloadが、B2のpreflight・検証・atomic promoteを通らなければfinal modelへ到達できない境界を作る。
7. モデル削除はownership解除の証明がない場合にfail closedする。

## 4. In Scope

- `src/core/whisper_model_store.py`の新規作成
- source/frozenの既定保存先解決
- test用storage root注入
- `whisper_models_dir`のSettingsStoreへの後方互換追加
- ローカル固定ドライブまたはローカルremovable driveの保存先検査
- UNC、remote drive、URL、relative path、device namespaceの拒否
- canonical final pathと`.part` staging pathのmanifest由来解決
- missing、partial、verified、invalid path、invalid size、invalid SHA256、read failureの分類
- final artifactとpartial artifactを別々に表現するavailability DTO
- 通常ファイル、symlink、Windows reparse point、directoryの検査
- streaming size / SHA256検証と読取中のfile identity変化検出
- B1の`VerifiedWhisperCheckpoint`生成
- `size_bytes + 64 MiB`の空き容量preflight
- ユーザー確認後かつdownload開始前に呼び出せるstorage準備・write probe
- close-before-`os.replace()`による同一directoryのatomic promote primitive
- promote後のfinal再検証
- promote失敗、検証失敗、cancel後のcanonical `.part` cleanup primitive
- existing verified final fileを、new verified artifactのpromote失敗で壊さない契約
- ownership release permitがないモデル削除のfail-closed判定
- root限定`/models/`のGit ignore追加
- B2専用core testとSettingsStore追加回帰

## 5. Out of Scope

- HTTP、HTTPS、Content-Length取得、redirect、timeout、progress表示、download worker、cancel UI（MS24-B4）
- ユーザー確認ダイアログ、RightPane、UiState、selected/active model UI（MS24-B3/B4）
- `selected_whisper_model_key`、`active_whisper_model_key`、`active_whisper_manifest_identity`の永続化（MS24-B3）
- `MainFrame -> AnalysisWorker -> pipeline -> whisper_timing`へのmodel identity伝播（MS24-B5）
- single-active model cache、loaded model ownershipの実装、明示unload、device resource cleanup（MS24-B5）
- Info、`WhisperDiagnosticsSummary`、diagnostic report、rollback projection（MS24-B6）
- 実モデル重みのdownload、実ネットワーク、実モデルを使用した解析
- 保存先の自動fallback、起動時の自動directory作成、暗黙download
- partial downloadのresume、HTTP Range、複数同時download
- UNC、mapped remote drive、network shareへのモデル保存
- `presets.json`、`profiles.json`、`MMD_AutoLipTool.ini`のruntime実体の読込・変更・生成・stage
- Qt / PySide6、cloud ASR、音声外部送信、background通信
- 実MMDでのVMD / WAV読込・リップ同期確認（MS26）
- package生成、onefile build、release、tag、push、merge、branch操作（MS27または明示承認時）

## 6. 前提条件

### 6.1 保存先

- frozen時の既定保存先は`Path(sys.executable).resolve().parent / "models"`とする。
- source時の既定保存先は、現行`SettingsStore.default_settings_path()`と同じrepo rootを基準にした`<repo root>/models`とする。
- `sys._MEIPASS`はonefileの一時展開先であるため、永続モデル保存先に使用しない。
- 設定値が空文字、未指定、または保存先として不正な場合は、ユーザーに無通知で別の場所へ移さず、既定保存先または保存先選択要求へfail closedする。
- ユーザー指定の保存先は絶対パスだけを許可する。URL、relative path、UNC path、device namespace、Windows remote driveは拒否する。
- ローカル固定ドライブと、ユーザーが明示的に選択したローカルremovable driveは許可対象とする。ドライブ種別はWindowsのdrive type検査で確認する。
- 保存先が書込不可でも、別の場所へ自動移動しない。B3/B4がユーザーへ保存先変更を促す。

### 6.2 設定責務

B2は保存先だけを所有する。

- B2が追加する設定キー: `whisper_models_dir`
- 空文字: B2の既定保存先を使用
- 非空文字: `WhisperModelStore`が絶対ローカルパスとして検証
- B2が追加しないキー: selected model、active model、manifest identity

B3は二段階切替の候補・active identityを別々に永続化する。B2の保存先設定をB3が利用しても、B3がB2のpath validationやatomic promoteを再実装しない。

### 6.3 容量・整合性

- 必要空き容量は、対象manifestの`size_bytes + 64 MiB`とする。
- `size_bytes`はB1 manifestのexact value以外を使用しない。
- free spaceが必要量未満、または取得できない場合はdownload開始可能と返さない。
- streaming検証は、実読取byte数とSHA256の両方を確認する。
- B2検証後も、B1 loaderは同じopen handleからbytesを再検証する。B2 DTOだけを長期的なfile immutability証明としない。

### 6.4 依存・配布

- `openai-whisper==20250625`、PyTorch、PyInstallerのversionは変更しない。
- 新規Python依存は追加しない。`pathlib`、`hashlib`、`shutil.disk_usage`、`tempfile`、`os.replace`、Windows標準API検査を使用する。
- `/models/`はroot限定でGit ignoreする。runtimeモデル重み、`.part`、temporary artifactはGit管理しない。
- PyInstaller spec、package data、LICENSE、NOTICE、THIRD_PARTY_LICENSESはB2では変更しない。manifest配布はB1で固定済みであり、重みは配布しない。

## 7. 対象ファイル

### 7.1 主変更対象

| 区分 | ファイル | 責務 |
| --- | --- | --- |
| 新規 | `src/core/whisper_model_store.py` | 保存先解決、availability、検証、preflight、atomic promote、削除可否境界 |
| 変更 | `src/core/settings_store.py` | `whisper_models_dir`のdefault、load、normalize、merge save |
| 変更 | `.gitignore` | root限定`/models/` ignore |
| 新規 | `tests/test_whisper_model_store.py` | B2 storage、availability、integrity、promote、delete guard |
| 変更 | `tests/test_settings_store.py` | 新規保存先設定の後方互換・正規化回帰 |

### 7.2 関連確認対象

- `src/core/whisper_models.py`: catalog、filename、manifest identityの利用境界
- `src/core/whisper_model_loader.py`: `VerifiedWhisperCheckpoint`の入力契約、B2検証後のloader再検証
- `src/resource_utils.py`: 読み取りresource解決であり、永続モデル保存先へ再利用しないことの確認
- `src/gui_wx/worker_state.py`: B4 download workerとB2 core stateを混在させない境界確認
- `tests/test_whisper_model_catalog.py`: manifest exact metadataの既存証拠
- `tests/test_whisper_model_loader.py`: verified DTO、partial、integrity、network-unreachableの既存証拠
- `docs/Implementation_Plan/MS24_Block_Breakdown.md`: B2〜B5責務、ModelAvailability、二段階切替契約
- `docs/Implementation_Plan/MS24-B1_Implementation_Plan.md`: B1 DTO、loader、package、failure code
- `docs/MS20_and_Beyond_Roadmap.md`: MS24の保存先、foreground network、local model policy
- `docs/Error_Handling_Specification.md`: 設定保存失敗、読み取り失敗、再試行可能状態の整合

### 7.3 変更禁止対象

- `presets.json`
- `profiles.json`
- `MMD_AutoLipTool.ini`
- 実モデル重み、`.part`、runtime model directoryの実体
- `src/core/whisper_timing.py`、GUI、AnalysisWorker、pipeline

## 8. 実装方針

### 8.1 Model storage API

`src/core/whisper_model_store.py`はUI非依存のimmutable DTOと明示的な操作結果を公開する。実装名は既存命名規約と照合して確定するが、責務は次へ固定する。

```text
WhisperModelStore
  catalog: WhisperModelCatalog
  storage_root: Path

default_whisper_models_dir() -> Path
resolve_whisper_models_dir(configured_value: str | None) -> StorageRootResolution
scan(model_key: str) -> ModelAvailability
scan_all() -> tuple[ModelAvailability, ...]
verify_checkpoint(model_key: str) -> VerifiedWhisperCheckpoint | StoreFailure
preflight_download(model_key: str) -> StoragePreflight
staging_path(model_key: str) -> Path
discard_staging(model_key: str) -> StagingCleanupResult
promote_verified_staging(model_key: str) -> VerifiedWhisperCheckpoint | StoreFailure
delete_model(model_key: str, permit: OwnershipReleasePermit | None) -> DeleteResult
```

`promote_verified_staging()`のpublic APIは`model_key`だけを受け取り、caller-suppliedな`staging_path`を受け取らない。実装内部でmodel keyからcanonical `.part`を解決する。内部helperへpathを渡す場合も、canonical pathとの完全一致、同一directory、通常ファイル、非symlink、非reparse pointを開く前に検証し、不一致をfail closedする。

public entryはmodel keyとcatalogに基づいてcanonical pathを解決し、任意filename、任意URL、raw checkpoint pathを受け取らない。test専用のtemporary root注入は許可する。

### 8.2 Canonical path

- final: `<storage_root>/<manifest.filename>`
- staging: `<storage_root>/<manifest.filename>.part`
- `small`、`medium`、`turbo`のpathはmanifestのfilenameからだけ生成する。
- 別名、拡張子差し替え、directory traversal、外部pathはcanonical artifactとして扱わない。
- 保存先rootと、rootが未存在の場合に使用するnearest existing parentまでの既存各要素をcanonical化して検査する。symlink、junction、Windows reparse point、networkへ解決される要素はlocal-only境界違反として拒否する。
- drive type検査はreparse/junction検査とcanonical化の後に行い、local fixedまたは明示選択されたlocal removable driveだけを許可する。
- finalとstagingは同一directoryに置き、Windowsのatomic replaceを成立させる。

### 8.3 Availabilityの軸

単一のenumへ物理ファイル状態、download worker状態、Whisper load結果、削除guardを混在させない。

`ModelAvailability.artifact_status`は次を扱う。

```text
missing
partial
verified
invalid_path
invalid_size
invalid_sha256
read_failed
unsupported
```

追加情報として次を保持する。

- `model_key`
- `manifest_identity`
- `storage_root`
- `file_path`
- `partial_path`
- `partial_present`
- `actual_size_bytes`
- `observed_sha256`
- `failure_code`
- `verified_checkpoint`

`downloading`と`cancelled`はB4のdownload worker state、`load_failed`と`memory_failure`はB5/B6のanalysis failure、`delete_blocked`はownership guardの結果として別軸で扱う。canonical finalがverifiedであってもstale `.part`が残る場合は、finalのverifiedを壊さず`partial_present=True`として表示できる。

`changed_during_verification`はartifact statusの独立値にはしない。物理的な読取・identity検査の失敗として`artifact_status=read_failed`へ写像し、`failure_code=model_changed_during_verification`で原因を保持する。表示用の物理状態分類と、再試行・診断用の詳細原因を分離する。

### 8.4 Initial verification and DTO generation

`verify_checkpoint(model_key)`は、次の順序で処理する。

1. catalogからmodel spec、canonical filename、manifest identityを解決する。
2. storage rootとcanonical pathを検査する。
3. `.part`しか存在しない場合はpartialとして返し、DTOを生成しない。
4. finalが存在しない場合はmissingとして返す。
5. directory、symlink、Windows reparse point、非通常ファイルをinvalid pathとして返す。
6. canonical fileをbinaryで一度開き、streamingで実byte数とSHA256を計算する。
7. 読取前後のpath/file descriptor identity、size、mtimeを比較し、truncate、replace、rename、同一path差し替えを検出する。
8. 実byte数がmanifestのexact `size_bytes`と異なる場合は`invalid_size`、SHA256が異なる場合は`invalid_sha256`とする。
9. 全検査成功時だけ、B1の`VerifiedWhisperCheckpoint`へmodel key、canonical path、manifest identity、SHA256、sizeを渡す。

B2の検証はhashとsizeを保持するが、bytesをmodel構築へ渡さない。B1 loaderはDTOを受け取り、B1自身の同一open handle再検証とbytes bindingを行う。

### 8.5 Storage preflight

download開始前のpreflightは、B4がユーザー確認を完了した後だけ呼び出す。起動時、候補選択時、解析開始時に自動実行しない。

- 保存先がない場合は、nearest existing parentのdrive type、write可否、free spaceを検査する。
- 保存先rootとnearest existing parentまでの既存各要素をcanonical化し、symlink、junction、Windows reparse point、networkへ解決されるpathを拒否してからdrive typeを検査する。
- 明示的なdownload準備操作では、必要なdirectoryを作成し、同一directoryへのclose-before-delete write probeを実行する。
- write probeやdirectory作成に失敗した場合は`storage_not_writable`として返し、自動fallbackしない。
- free spaceは`shutil.disk_usage()`で取得し、`free_bytes >= size_bytes + 64 MiB`を必須とする。
- free spaceを取得できない場合も開始可能とは返さない。
- preflightはHTTPを呼ばず、official URLへ接続しない。

### 8.6 Atomic promote

B2はfilesystem操作の正本、B4はdownload orchestrationの正本とする。

- B4はfinal fileへ直接書かず、B2の`staging_path(model_key)`が返すcanonical `.part` pathへforeground downloadする。
- B4がdownloadを完了した後、B2は閉じた`.part`をexact size / SHA256で検証する。
- 検証成功後、同一directoryで`os.replace(partial, final)`を実行する。
- replace前にfinalが既に存在しても、new artifactの検証が成功するまでは既存finalを変更しない。
- replace失敗時は既存finalを保持し、new `.part`は`discard_staging()`でcleanupする。cleanupに失敗してもavailableにはしない。
- replace成功後にcanonical finalを再走査し、verified DTOを返す。
- cancel、通信失敗、short read、overrun、size mismatch、SHA mismatchではpromoteを実行しない。
- `promote_verified_staging(model_key)`はcaller-supplied pathを受け取らず、canonical `.part`だけを検証・promoteする。内部helperへpathを渡す場合も、canonical pathとの一致確認をopen、hash、replaceより前に行う。
- `discard_staging(model_key)`はcanonical `.part`だけを対象にし、任意pathを受け取らない。missingはidempotentな成功、通常fileの削除成功はcleanup済み、reparse point・directory・削除失敗はstructured failureとして返す。
- partialのresumeは行わず、失敗後は`discard_staging()`でpartialを削除して再取得する。cleanup失敗時はpartialをavailableにせず、次回scanでpartialまたはcleanup failureとして表示する。

### 8.7 Delete guard

B2はcanonical model fileの削除primitiveを持つが、ownershipをfilesystem状態やPython GCから推測しない。

- `delete_model()`はB5が発行する`OwnershipReleasePermit`がない場合、`delete_blocked_ownership`でfail closedする。
- B4は確認ダイアログとdelete操作のworker orchestrationを所有するが、B5のpermitがない段階では削除拒否を表示する。
- permitがある場合だけcanonical finalを削除し、`.part`は`discard_staging()`でdownload operationのcleanup契約に従う。
- 削除成功後の物理状態は`deleted`として永続化せず、再scan結果の`missing`として返す。
- active worker、loaded cache、release pending、解析結果identityが残る場合はpermitを発行しない。

`OwnershipReleasePermit`の生成はB5の責務であり、B2は生成しない。permitはB5がownership解除を完了した直後に発行する、永続化しないrequest-scoped capabilityとする。production codeではpermitを公開fieldの組み合わせから構築できないopaque objectとし、B5専用issuer boundaryだけが発行する。B2はそのissuer boundaryに対応するverifierで検証・単回消費する。

- permitは`model_key`、`manifest_identity`、canonical final artifactへの対象識別、内部一意nonceを束縛する。
- permitは単回使用であり、B2が削除要求の直前に消費済みへ遷移させる。削除失敗時も再利用せず、再試行にはB5の再発行を要求する。
- permitは設定、INI、JSON、ログ、worker callbackへシリアライズしない。有効期限はプロセス内の一回の削除要求までとし、再起動後は無効である。
- B4はpermitを作成、複製、model identity変更してはならない。B2はissuer boundaryを通らないfield-shaped object、`None`、対象不一致、消費済み、形式不正のpermitを常に拒否する。
- B2のtestはB5本体を実装せず、test-only issuerから発行したopaque permitで、対象一致・不一致・再利用・削除失敗後の再利用を検証する。productionのpublic APIからpermitを偽造できる形のfakeは使用しない。

## 9. 詳細ステップ

### Step 1: B2 contractを定義する

- storage root resolution result、`ModelAvailability`、`StoragePreflight`、`StoreFailure`、`DeleteResult`を定義する。
- artifact、transfer、load、ownershipの状態軸を分離する。
- B1の`VerifiedWhisperCheckpoint`をDTO生成の唯一の下流契約とする。
- failure codeを次へ固定する。
  - `storage_path_invalid`
  - `storage_path_remote`
  - `storage_not_writable`
  - `storage_free_space_unknown`
  - `storage_free_space_insufficient`
  - `model_missing`
  - `model_partial`
  - `model_invalid_path`
  - `model_size_mismatch`
  - `model_sha256_mismatch`
  - `model_read_failed`
  - `model_changed_during_verification`
  - `model_promote_failed`
  - `delete_blocked_ownership`
  - `delete_failed`

### Step 2: 保存先を解決する

- frozen/sourceの既定rootを実装する。
- `whisper_models_dir`の空文字、absolute path、local drive検査を実装する。
- rootとnearest existing parentまでの既存各要素をcanonical化し、symlink、junction、Windows reparse point、networkへ解決されるpathを拒否する。root作成後も作成した各要素がlocal-only境界を満たすことを再検査する。
- UNC、remote drive、URL、relative path、device pathをfail closedする。
- `src/resource_utils.py`の`_MEIPASS`を永続保存先へ使用しない。
- root未存在時のscanは自動作成せず、明示preflightだけが作成できるようにする。

### Step 3: SettingsStoreへ保存先だけを追加する

- `SettingsStore.default_settings()`へ`whisper_models_dir: ""`を追加する。
- `[ui]`のload/save/mergeへ追加する。
- 旧callerが新keyを省略したpartial saveで、既存の保存先を既定値へ戻さない。
- invalid typeや空白は安全な空文字へ戻す。ただしrelative/UNC/remoteの最終判定はstore側で行う。
- 設定保存失敗は既存SettingsStoreのstructured resultとsave-disabled契約を維持する。

### Step 4: availability scanを実装する

- model keyからmanifest filenameだけを使ってcanonical pathを作る。
- final、`.part`、directory、symlink、reparse pointを分類する。
- finalのsize / SHA256をstreaming検査する。
- file identity変化、read error、size mismatch、hash mismatchを安定したfailure codeへ写像する。
- valid finalだけに`VerifiedWhisperCheckpoint`を生成する。
- final verified + partial presentを別軸で返す。

### Step 5: explicit download preflightを実装する

- B4が明示確認後に呼ぶpreflight APIを定義する。
- `size_bytes + 64 MiB`をfree-space gateへ適用する。
- directory creation、write probe、free-space取得を分け、失敗理由を混同しない。
- canonical `.part`だけを対象とする`discard_staging(model_key)`を定義し、cancel・通信失敗・検証失敗時のcleanup入口を一つにする。
- preflightからnetwork、Whisper load、解析、UI state mutationを呼ばない。

### Step 6: atomic promote primitiveを実装する

- B4のHTTP書込先を`staging_path(model_key)`が返すcanonical `.part`へ限定する。
- closed same-directory temporary file、exact verification、`os.replace()`、post-promote scanを実装する。
- public `promote_verified_staging(model_key)`はcaller-supplied pathを受け取らず、内部で解決したcanonical `.part`だけを検証・promoteする。内部helperへpathを渡す場合も、canonical pathとの一致確認をopen、hash、replaceより前に行う。
- replace失敗時にold finalを保護し、`discard_staging()`でpartial cleanupを行う。
- partial resume、自動fallback、直接final書込を禁止する。

### Step 7: delete guardを実装する

- ownership permitなしを必ず拒否する。
- B5専用issuer boundaryが発行したopaqueなmodel-bound・manifest-bound・request-scoped単回permitだけを検証し、消費済みへ遷移させてからcanonical finalを削除する。公開fieldの組み合わせやB4由来のfield-shaped objectはpermitとして受理しない。
- permitの生成、ownership解除、active worker / cache / unload判定はB2で実装しない。
- delete後の再scan結果を`missing`へ正規化する。
- B4/B5が異なる状態を渡した場合も、B2は安全側へ倒す。

### Step 8: テストとコード再照合を行う

- §11の順序でテストを実行する。
- 実モデル、実ネットワーク、root runtime user dataを使用しない。
- `git diff --check`、`compileall`、process exit codeを別々に記録する。
- B1 loader、MS23 profile、preset、fingerprint、固定モーフ、VMD / WAV境界に差分がないことを確認する。

## 10. 状態遷移 / データ契約

### 10.1 保存先状態

```text
configured_value == ""
  -> source/frozen default models root

configured_value is absolute local path
  -> configured models root

configured_value is relative / UNC / remote / URL / device path
  -> storage_path_invalid or storage_path_remote
  -> automatic fallbackなし
  -> user-selected local path required
```

### 10.2 Artifact状態

```text
root missing / final missing / no .part -> missing
only canonical .part exists            -> partial
final exists but non-regular/reparse   -> invalid_path
final regular but size differs         -> invalid_size
final size matches but SHA differs     -> invalid_sha256
read / identity check fails            -> read_failed + specific failure_code
final size + SHA + identity all pass   -> verified + VerifiedWhisperCheckpoint
```

`final verified + .part exists`は`verified`と`partial_present=true`を同時に保持できる。partialを理由に既存verified finalを暗黙削除しない。

### 10.3 Download / promote状態

```text
user-confirmed foreground operation
  -> storage preflight
     -> failure: no file promotion, recoverable error
     -> success: B4 writes canonical .part
        -> cancel / HTTP failure
           -> discard_staging(model_key)
              ├─[cleanup success]─> no promotion, partial not available
              └─[cleanup failure]─> partial remains, no promotion, recoverable error
        -> B2 exact verify success
           -> same-directory atomic replace
              -> replace failure: old final preserved
              -> replace success: final rescan -> verified
```

起動、候補選択、解析開始、timer、background callbackからこの遷移を開始しない。

### 10.4 B2 to B1/B4/B5 contract

- B2 -> B1: `VerifiedWhisperCheckpoint`だけを渡す。B1は同一open handleから再検証してbytes loadする。
- B2 -> B4: preflight、canonical `.part` path、`discard_staging()`、promote result、availability resultを渡す。B4はHTTP/worker/cancel/delete orchestrationだけを所有し、permitを生成しない。
- B2 -> B5: canonical verified DTOとownership delete guard、permit消費契約を渡す。B5はpermit発行、active model/cache/unloadを所有する。
- B2は`whisper.load_model()`、`download_root`、model key loader、HTTP client、UI stateを呼ばない。

### 10.5 failure code handoff

`StoreFailure.failure_code`、`StoragePreflight.failure_code`、`StagingCleanupResult.failure_code`、`DeleteResult.failure_code`はB2のUI非依存coreでの安定した内部codeとする。B2では`Error_Handling_Specification.md`のユーザー向け文言や既存Whisper error classへ直接投影しない。

- B4はpreflight、download、cancel、cleanup、promoteの結果へB2のfailure codeを保持し、HTTP failureやcancelと混同しない。
- B5/B6はmodel unavailable、integrity mismatch、load failure、ownership blockedなどの上位failure classへ投影する際、B2のfailure codeをdiagnostic detailとして失わない。
- `Error_Handling_Specification.md`の新規ユーザー向けcode追加・文言決定はB4/B6の該当Implementation Planで行い、B2では先行して変更しない。

## 11. テスト方針

### 11.1 B2専用core test

`tests/test_whisper_model_store.py`を新規作成し、すべてtemporary directoryと小さなfake bytesで検証する。

- source default root、frozen default root、`_MEIPASS`を保存先に使わないこと
- custom root注入、empty config、absolute local path
- relative、UNC、URL、device namespace、remote drive拒否
- rootとnearest existing parentのsymlink、junction、Windows reparse point、network redirect拒否
- missing rootのscanが起動時にdirectoryを作成しないこと
- explicit preflight後のdirectory creationとwrite probe
- `size_bytes + 64 MiB`のfree-space判定、free-space取得不能、容量不足
- manifest filenameからのcanonical final / `.part` path生成
- missing、partial、verified、final verified + stale partial
- directory、symlink、Windows reparse point、非通常ファイル拒否
- exact size mismatch、SHA256 mismatch、read PermissionError / OSError
- streaming中のtruncate、same-path replace、identity / metadata変化の拒否
- valid fake artifactからの`VerifiedWhisperCheckpoint`生成
- DTOのmodel key、manifest identity、sha256、sizeの正確な保持
- B4が書くcanonical `.part`への限定、caller-supplied promote path・任意filename・任意checkpoint pathの拒否
- closed same-directory `os.replace()`とpost-promote rescan
- replace失敗時のexisting final保護と`discard_staging()`によるcanonical temporary cleanup
- cancel / short read / overrun / hash mismatchでpromoteせず、canonical `.part`だけをcleanupすること
- partial resumeを行わず、失敗後のpartialをavailableにしないこと
- issuer boundaryを通らないfield-shaped object、ownership permitなし・対象不一致・再利用permitのdelete拒否、test-only issuerが発行した対象一致の単回opaque permitによるcanonical delete、delete後missing
- B2実行中にnetwork API、Whisper loader、analysis pipelineへ到達しないこと

### 11.2 SettingsStore回帰

`tests/test_settings_store.py`へ次を追加する。

- `whisper_models_dir`未指定時の空文字default
- custom local pathのsave/load round trip
- 旧callerが新keyを省略したpartial saveでも既存保存先を保持すること
- non-string、空白、invalid inputの安全なdefault
- same-directory temporary、close-before-replace、既存INI内容の保持
- save failure後の既存save-disabled / first-failure通知契約

runtime rootの`MMD_AutoLipTool.ini`はテストで使用しない。すべてtemporary pathを注入する。

### 11.3 関連回帰

- `tests/test_whisper_model_catalog.py`
- `tests/test_whisper_model_loader.py`
- `tests/test_whisper_timing.py`
- `tests/test_settings_store.py`
- `tests/test_ms19_b4_analysis_worker_voice_only.py`
- `tests/test_ms19_b5_transcription_edit_state.py`
- `tests/test_pipeline_and_vmd.py`
- `tests/test_ms21_b7_analysis_rollback.py`

B2はUI非依存coreであるため、手動GUI確認はB2の必須gateとしない。B4のdownload確認、B5のanalysis伝播確認、MS26の実MMD確認を先行実施しない。

### 11.4 実行順

1. `tests/test_whisper_model_store.py`
2. `tests/test_settings_store.py`
3. `tests/test_whisper_model_catalog.py`
4. `tests/test_whisper_model_loader.py`
5. `tests/test_whisper_timing.py`
6. MS19 voice-only関連回帰
7. pipeline / rollback関連回帰
8. `compileall src tests`
9. `git diff --check`

各テストはpass表示だけでなくprocess exit code `0`を必須とする。実ネットワーク、実モデルdownload、GUI、実MMDは実行しない。

## 12. 受け入れ条件

### Storage / path

- [ ] sourceの既定保存先はrepo root隣接の`models`である。
- [ ] frozenの既定保存先はexe隣接の`models`であり、`_MEIPASS`ではない。
- [ ] empty設定は既定保存先へ解決される。
- [ ] absolute local fixed/removable driveだけを許可し、UNC、remote drive、URL、relative、device pathは拒否する。
- [ ] rootとnearest existing parentまでの既存各要素をcanonical化し、symlink、junction、Windows reparse point、network redirectを拒否してからdrive typeを確認する。
- [ ] 書込不可時に自動fallbackせず、保存先変更へ戻れるstructured resultを返す。
- [ ] `/models/`がroot限定でignoreされ、モデル重みと`.part`がGit管理対象にならない。

### Availability / integrity

- [ ] canonical filenameがmanifestからだけ解決される。
- [ ] missing、partial、verified、invalid path、invalid size、invalid SHA256、read failureを区別できる。
- [ ] 読取中のidentity変化は`artifact_status=read_failed`、`failure_code=model_changed_during_verification`へ安定写像する。
- [ ] final verifiedとpartial残留を別軸で表現できる。
- [ ] exact sizeとstreaming SHA256を検証し、file identity変化をfail closedする。
- [ ] valid artifactだけがB1の`VerifiedWhisperCheckpoint`を生成する。
- [ ] `.part`、directory、symlink、reparse point、異なるmanifestの重みをDTOへ変換しない。

### Preflight / promote

- [ ] ユーザー確認後、明示的foreground download開始前だけpreflightを呼べる契約である。
- [ ] 必要空き容量は`size_bytes + 64 MiB`で判定される。
- [ ] free space不明・不足、directory作成失敗、write probe失敗は開始不可になる。
- [ ] B4がfinalへ直接書かず、B2のcanonical `.part`とpromote primitiveだけを使う。
- [ ] promoteはcaller-supplied pathを受け取らず、model keyから解決したcanonical `.part`だけを検証・replaceする。
- [ ] cancel・通信失敗・検証失敗時は`discard_staging(model_key)`だけがcanonical `.part`をcleanupし、任意pathを削除しない。
- [ ] `os.replace()`は同一directoryのclose済みartifactへ限定される。
- [ ] promote失敗時も既存finalを保護し、partialをavailableにしない。
- [ ] post-promote rescanがverifiedでなければ成功を返さない。
- [ ] partial resume、silent retry、auto fallback、network callをB2が行わない。

### Settings / downstream boundary

- [ ] B2は`whisper_models_dir`だけをSettingsStoreへ追加し、selected/active identityを追加しない。
- [ ] 旧SettingsStore callerが新keyを省略しても既存保存先を壊さない。
- [ ] B1 loaderはB2 DTOを再検証し、B2の初回verificationをloader内で省略しない。
- [ ] B3のselected/active identity、B4のHTTP/worker、B5のcache/unloadはB2へ混在しない。
- [ ] B5だけがmodel key・manifest identityへ束縛されたrequest-scoped単回permitを発行し、B2が対象一致・未消費を検証してからcanonical deleteする。
- [ ] permitはopaqueなB5専用issuer boundaryからだけ発行され、公開fieldの組み合わせやB4由来のobjectをB2が受理しない。
- [ ] ownership permitなし・対象不一致・再利用permitの削除は常に拒否される。
- [ ] delete後の物理状態は`missing`へ再投影され、`deleted`を永続availabilityとして残さない。

### 回帰・境界

- [ ] `openai-whisper==20250625`、B1 manifest、B1 loader、word timestamp / segment fallbackを変更しない。
- [ ] MS23の固定モーフ、Latin profile、preset、diagnostics、fingerprint、VMD 30fps、MMD用WAV契約を変更しない。
- [ ] `presets.json`、`profiles.json`、`MMD_AutoLipTool.ini`のruntime実体を読込・変更・stageしない。
- [ ] GUI、実ネットワーク、実モデル、実MMDの未実施をB2完了と混同しない。
- [ ] pytest、compileall、diff checkのprocess exit codeを記録する。

## 13. リスクと対策

| ID | リスク | 重要度 | 対策 |
| --- | --- | --- | --- |
| MS24-B2-R1 | partialまたは不正重みがavailableになる | P1候補 | canonical path固定、`.part`分離、exact size / SHA256、atomic promote、post-promote rescan |
| MS24-B2-R2 | B4がfinalへ直接書き、途中ファイルをloaderが読む | P1候補 | B2がstaging / verify / replace primitiveを所有し、B4へfinal writeを許可しない |
| MS24-B2-R3 | B2 DTO生成後の差し替えをB1 loaderが信頼する | P1候補 | B1 loaderが同一open handleからsize / SHA256を再検証し、bytesへ束縛する |
| MS24-B2-R4 | exe隣接保存先がProgram Files等で書込不可 | P2候補 | write probe、free-space preflight、silent fallback禁止、ユーザー選択へ復帰 |
| MS24-B2-R5 | 空き容量ぎりぎりでdownloadが失敗する | P2候補 | manifest exact sizeに64 MiB reserveを加え、free-space取得不能も拒否 |
| MS24-B2-R6 | UNC / mapped remote drive経由の予期しないnetwork I/O | P2候補 | UNCとremote driveをdrive type検査で拒否し、local fixed/removableに限定 |
| MS24-B2-R7 | B2とB3が同じINIキーを別責務で上書きする | P2候補 | B2は`whisper_models_dir`のみ、B3はselected/active identityのみと明記 |
| MS24-B2-R8 | B2/B4がatomic renameを重複実装する | P2候補 | B2をfilesystem正本、B4をHTTP/worker orchestration正本に分離 |
| MS24-B2-R9 | B4のdelete UIがB5 ownership前に削除する | P1候補 | B2のmodel-bound・manifest-bound・request-scoped単回permit必須、permitなし・不一致・再利用は常にdelete blocked |
| MS24-B2-R10 | `deleted`、`downloading`、`load_failed`をartifact availabilityへ混在させる | P2候補 | artifact / transfer / load / ownershipを別軸DTOへ固定 |
| MS24-B2-R11 | `/models/`の重みがGitへ誤追加される | P2候補 | root限定ignore、static test、runtime実体をplan/testで作成しない |
| MS24-B2-R12 | B2がB4のHTTP処理やB5のcacheを先行実装する | P2候補 | no-network core、対象ファイル表、public API境界、関連回帰を固定 |
| MS24-B2-R13 | caller-supplied pathによりcanonical外のartifactがpromoteされる | P1候補 | promote public APIからpathを除き、内部でもcanonical一致をopen前に検証 |
| MS24-B2-R14 | B4がfield-shaped permitを偽造してownership未解除fileを削除する | P1候補 | B5専用issuer boundary、opaque permit、B2 verifier、test-only issuerを固定 |
| MS24-B2-R15 | local path下のjunction / reparse pointがnetwork shareへredirectする | P2候補 | rootと既存親要素をcanonical化・reparse検査してからdrive typeを確認 |
| MS24-B2-R16 | B2独自failure codeがB4/B5/B6で上位分類時に失われる | P3候補 | B2はstable internal codeを保持し、B4/B5/B6の上位投影とdiagnostic detail保存へhandoffする |

### 13.1 計画段階のP1 / P2 / P3判定

- P1: 現時点で確定したP1はない。partial / unverified artifact、finalへの直接書込、ownership未解除削除は、実装時にP1へ発展し得るため、受け入れ条件とfail-closed testで防ぐ。
- P2: B2/B3の`whisper_models_dir`責務、B2/B4のatomic promote責務、物理状態とworker/load/ownership状態の混在、B4/B5のdelete依存を本planで分離した。今回の再チェックで確認されたcaller-supplied promote path、permit issuerの実装境界、root reparse/junctionのlocal-only境界を本文へ反映した。P2は残存しない。
- P3: `src/resource_utils.py`を永続保存先へ再利用しないこと、`deleted`を永続availabilityにしないこと、単一`whisper_model_name`を二段階切替の正本にしないこと、B2 failure codeをB4/B5/B6へ保持して上位投影するhandoffを本文で明示した。P3は残存しない。

## 14. 実装・検証記録

- 2026-08-22にMS24-B2を実装し、`b011b37 Implement MS24-B2 model storage core`へ記録した。`whisper_models_dir`のlocal-only解決、availability、canonical `.part`、preflight、atomic promote、B5発行permitの検証付きdeleteを実装範囲とし、B3のselected / active identity、B4のHTTP / worker、B5のloaded ownership / cacheは先行実装していない。
- 2026-08-23の実装前確認で、B2 / B1 / SettingsStore関連の指定テストは40 passed、2 skipped（Windows symlink capability依存）だった。これはB2のtargeted baselineであり、B3の実装完了や手動GUI確認を意味しない。
- B2はUI非依存Blockのため、B2の手動GUI確認、実ネットワーク、実モデル、実MMD確認は実施対象外とし、B3以降およびMS26へ残す。

## 15. 実装時の注意

- コマンドは一つずつ実行し、parallel、pipeline、`&&`、`||`、`;`で連結しない。
- 実装開始時にlive Git state、MS20 routing、MS24 Block Breakdown、B1 plan、B1実装、関連testを再確認する。
- `presets.json`、`profiles.json`、`MMD_AutoLipTool.ini`のruntime実体は読み取り・変更・削除・stageしない。設定テストにはtemporary pathを注入する。
- `sys._MEIPASS`をモデル保存先に使わない。onefile展開先と永続モデルrootを分離する。
- B2のlocal-only policyを、単なる文字列prefix判定だけで済ませず、rootと既存親要素のcanonical化、symlink/junction/reparse検査、WindowsのUNC/device/drive typeを確認する。
- `is_file()`だけでverified扱いしない。symlink、reparse point、directory、identity change、size、SHA256を確認する。
- B2の初回verificationとB1 loaderのload直前再検証を一方へ統合して省略しない。
- B4のforeground downloadはユーザー確認後だけ許可する。B2のpreflight・promoteがnetworkを開始してはならない。
- B4からfinal pathへ直接書かせない。B2がcanonical `.part`、caller-supplied path拒否、closed handle、atomic replaceを管理する。
- ownership解除をPython GCの完了だけで推測しない。permitがなければ削除を拒否する。
- ownership permitはB5専用issuer boundaryのopaque capabilityとし、B4が公開fieldから偽造できる形にしない。
- B2 failure codeはB4/B5/B6の上位failure classへ投影してもdiagnostic detailとして保持する。
- `selected`、`active`、`loaded`、`analysis` identityの意味をB2へ追加しない。二段階切替はB3以降の責務である。
- `openai-whisper==20250625`、B1 private alignment heads、network-unreachable loader、word / segment fallback、MS23のfixed morph / Latin profile / preset / diagnostics / fingerprintを壊さない。
- B2でGUI、実ネットワーク、実モデル、実MMDを確認済みと報告しない。B4、B5、MS26の検証境界を維持する。
- 実装後は、変更ファイル、availability state、failure code、ownership guard、テストprocess exit code、未実施確認を報告する。
