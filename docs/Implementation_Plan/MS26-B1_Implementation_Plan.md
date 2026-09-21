# MS26-B1 Implementation Plan

## 1. 文書情報

- 対象マイルストーン: MS26 Final Feature Integration / Actual MMD Closeout
- 対象ブロック: MS26-B1 Current Baseline / Acceptance Preparation
- 作成日: 2026-09-04
- 正本: `docs/Implementation_Plan/MS26_Block_Breakdown.md`
- 前提となるcloseout: MS25 Closeout A (`c881264 Record MS25-B7 closeout A`)
- 作成時ブランチ: `feature/MS26-implementation`
- 作成時HEAD: `c88126469407e716724c97ed8c0805732e9f84dd`
- 実装権限: 本計画ではproduction code、test code、GUI、runtime user dataを変更しない。stage、commit、merge、push、tag、releaseも行わない。
- 現在の状態: 2026-09-09にB1のbaseline / contract gateを前提としてB2のtest-only duration gate、既存横断回帰、full gate、証拠台帳更新を完了した。B1 baseline / contract gateとB2 automated cross-boundary regressionはpassed。2026-09-11〜09-12のユーザー報告として、GUI、AC03 / AC04、MMD Ver 9.32、指定model、入力 / 出力音声、日本語・ラテン、4主要ケース、実MMD上の音声・モーフ同期、追加GUI / recovery / Whisper gateは問題なしとして確認済みである（いずれもCodex実施ではない）。2026-09-12にB4 targeted revalidationと最終監査を行い、B4-AC01〜08を充足、B2-R05は非確定観測として分類した。MS26 CloseOut A、MS27はdeferred。PMX hashは本環境から独立取得できず補助identityの制限として記録する。

- 実装後チェック: 2026-09-07にメインが実施し、B1成果物を受け入れ可能と判定した。P1 / P2 / P3残存なし。詳細は§16.2。

## 2. 背景

MS25 Closeout Aでは、一括deliveryのVMDはcurrent `EffectiveShapePlan`から、MMD用WAVはoriginal source audioから、diagnostic reportは同一immutable diagnostics snapshotから、それぞれ生成する契約と、stagingから全成功時だけ確定する保護境界を確認した。MS26は、MS20〜MS25の現行HEADでの横断整合性、自動回帰、Windows 11 GUI、実MMDでの読み込み・再生・morph・同期を確認する段階である。

MS25で実施した自動テストとユーザー報告のGUI確認は、MS26の新しいHEADに対する実MMD受入証拠ではない。B1では、既存契約を再設計せず、B2〜B4で取得する証拠の対象、実行者、HEAD、素材identity、結果を混同しない台帳を定義する。

現行のMMD用WAV仕様、コードの`MMD_WAV_SPEC`とvalidator、MS25契約をchannel count 2（stereo固定）へ同期した。MS26-B1ではstereo固定を実行基準かつruntime契約として扱い、コードをmono許容へ変更しない。

## 3. 目的

1. MS25 Closeout Aを基準に、MS26-B1の現行Git、依存関係、コード、テスト、正文書の対応を固定する。
2. MS25契約を保ったまま、B2自動回帰、B3手動GUI・実MMD、B4再検証・closeoutの証拠境界を明文化する。
3. 実MMD受入に必要なWindows 11、MMD、model、morph、音声、TEXT、preset、profile、Whisper identityの必須項目を確定し、未提供項目を推測で埋めない。
4. 実装開始時に、変更対象、テスト対象、未検証事項、再実行条件を機械的に判断できる状態にする。

## 4. In Scope

- `MS26_Block_Breakdown.md`、MS25 Closeout A関連文書、現行コード、既存テストの読み合わせ。
- Gitのbranch、HEAD、remote参照、既存変更、Python実行環境、主要依存、リポジトリ内FFmpeg/ffprobeの確認。
- delivery開始時のeffective output、source audio identity、Whisper identity、fingerprint、projection generation、staging/commit境界の確認。
- TEXT + audio と `voice_only` の入力条件、解析用WAVとMMD用WAVの分離、Japanese/Latin morph set、preset/profileの受入記録項目の確定。
- MMD用WAV正文仕様と `src/core/mmd_wav_export.py` の `MMD_WAV_SPEC` / `_validate_mmd_wav_file` の照合。
- B2の自動テスト範囲・実行順・process exit code記録方法の定義。
- B3のWindows 11 GUI手動確認と実MMD確認の実行者・環境・素材・観測結果の記録形式の定義。
- B4のfinding解消、影響範囲に応じた自動テスト・手動GUI・実MMDの再実行条件の定義。
- B1計画作成後のMS20 Index current stateの同期。

## 5. Out of Scope

- production code、test code、GUIの実装または修正。
- B2〜B4のfull pytest・横断回帰、compileall、実MMD、Windows 11 GUIの実行。本B1ではテストファイルと入口の読み取りに限定し、文書修正の契約確認に必要な対象テストだけを例外的に実行する。
- MMD本体、PMX/PMD、音声、TEXT、Whisper modelのリポジトリへのコピー、runtime user dataの編集・コピー・stage。
- `presets.json`、`profiles.json`、`MMD_AutoLipTool.ini` の直接操作。
- 依存関係、lock file、`MMD_AutoLipTool.spec`、PyInstaller、ZIP、installer、license/package/release readiness。
- push、merge、tag、release、外部サービス、cloud ASR、解析時の暗黙download。
- MMD用WAVのchannel契約を、ユーザー判断なしにmono許容へ拡張すること。

## 6. 前提条件

- `feature/MS26-implementation` はMS25 Closeout Aの `c881264` から作成されている。MS26 branchのupstream trackingは未設定で、remote操作は本計画の範囲外である。
- 計画作成時（2026-09-04）の作業ツリーには、modifiedの`docs/MMD_Audio_WAV_Compatibility_Specification.md`と`docs/MS20_and_Beyond_Index.md`、未追跡の`docs/Implementation_Plan/MS26-B1_Implementation_Plan.md`と`docs/Implementation_Plan/MS26_Block_Breakdown.md`があった。これは計画作成時点の履歴であり、B1実施時のlive stateと混同しない。
- B1実施時（2026-09-06）は`feature/MS26-implementation`のHEAD `e2d63ad1d1469f6a74ee09d508c26c1c4b47ba08`で、開始時working treeはclean、upstream trackingは未設定だった。`c881264..HEAD`はAGENTS / skill・MS26計画・仕様 / Indexなどの文書差分のみで、`src`、`tests`、`pyproject.toml`、`uv.lock`の差分はなく、docs-only差分によるruntime contractの失効はない。ただし、この非失効根拠は旧HEADのtest passを現行HEAD passへ転用する根拠ではない。
- `pyproject.toml` の宣言は Python `>=3.11`、wxPython `4.2.5`、matplotlib `3.10.8`、numpy `2.4.3`、openai-whisper `20250625`、pyopenjtalk `0.4.1` である。
- B1時点で観測した開発環境は `.venv` の Python `3.14.3`。Python 3.11 / 3.12互換性は未検証として扱う。
- リポジトリ内 `FFmpeg\bin\ffmpeg.exe` と `FFmpeg\bin\ffprobe.exe` は存在し、versionコマンドが成功した。探索順はアプリケーション/リポジトリ内`FFmpeg\bin`を先、`PATH`を次とする。暗黙downloadは探索手段に含めず、解析時を含めて禁止する。
- 実MMD受入素材と外部環境は未確定である。未提供の項目は「未確定」または「B3開始条件」として記録し、既定値や過去の素材を受入証拠に昇格しない。
- 過去のpytest件数、ユーザー報告のGUI結果、旧HEADの手動確認は、B1完了後の新HEADの検証結果へ転用しない。

## 7. 対象ファイル

### 7.1 計画・状態文書

| 区分 | ファイル | 扱い |
| --- | --- | --- |
| 新規 | `docs/Implementation_Plan/MS26-B1_Implementation_Plan.md` | 本計画の作成対象 |
| 正本 | `docs/Implementation_Plan/MS26_Block_Breakdown.md` | B1責務・ブロック境界の正本として参照 |
| 状態 | `docs/MS20_and_Beyond_Index.md` | B1計画作成後のcurrent stateを同期 |
| 参照 | `docs/MS20_and_Beyond_Roadmap.md` §13〜§15 | MS26/MS27境界と完了条件を照合 |
| 参照 | `docs/Implementation_Plan/MS25_Block_Breakdown.md` | MS25契約と未検証境界を照合 |
| 参照 | `docs/Implementation_Plan/MS25-B7_Implementation_Plan.md` | MS25 Closeout Aの証拠粒度を照合 |

### 7.2 仕様・利用者向け文書

- `docs/Pipeline_Data_Contract_Specification.md`
- `docs/GUI_State_Theme_Specification.md`
- `docs/Error_Handling_Specification.md`
- `docs/VMD_Output_Specification.md`
- `docs/MMD_Audio_WAV_Compatibility_Specification.md`
- `README.md`
- `readme_mmdautolip.txt`

### 7.3 実装・テストの確認対象

- Core: `src/core/pipeline.py`, `audio_convert.py`, `output_diagnostics.py`, `diagnostic_report.py`, `mmd_wav_export.py`, `delivery_package.py`, `delivery_artifacts.py`
- GUI/worker: `src/gui_wx/app_controller.py`, `main_frame.py`, `right_pane.py`, `ui_state.py`, `audio_worker.py`, `worker_state.py`, `output_diagnostics_adapter.py`, `playback_controller.py`, `playback_context.py`, `preview_panel.py`, `waveform_panel.py`
- VMD: `src/vmd_writer/writer.py`, `src/vmd_writer/validator.py`
- MS19〜MS24のtextless/voice-only、state、warning、diagnostic、Preview、effective output、profile、Whisper関連テスト
- MS25直接テスト: `tests/test_ms25_b1_current_state_gate.py`, `test_ms25_b1_delivery_contract.py`, `test_ms25_b2_windows_paths.py`, `test_ms25_b2_delivery_orchestration.py`, `test_ms25_b2_delivery_commit.py`, `test_ms25_b3_delivery_artifacts.py`, `test_ms25_b3_vmd_readback_validation.py`, `test_ms25_b4_delivery_report_identity.py`, `test_ms25_b5_delivery_worker.py`, `test_ms25_b5_delivery_gui.py`, `test_ms25_b6_windows_collision_faults.py`, `test_ms25_b6_delivery_gui_recovery.py`, `test_ms25_b6_delivery_failure_recovery.py`
- 個別MMD用WAV回帰: `tests/test_ms17_b7_mmd_wav_export.py`, `test_ms17_b7_mmd_wav_failure_cleanup.py`, `test_ms17_b7_mmd_wav_save_dialog.py`, `test_ms17_b7_mmd_wav_overwrite_confirm.py`, `test_ms17_b7_mmd_wav_button_state.py`
- 共通入口: `tests/test_pipeline_and_vmd.py`, `tests/test_vmd_writer_*.py`

## 8. 実装方針

### 8.1 証拠優先順位

現行Git、現行コード・テストの実体、実行コマンドのprocess exit code、実際のWindows 11/MMD結果を優先する。計画書、roadmap、仕様書、README、過去の履歴は、現行実体との整合を確認するために使う。過去の結果を現在のHEADの証拠として再利用しない。

### 8.2 証拠台帳

各証拠は少なくとも次を持つ。

| 項目 | 内容 |
| --- | --- |
| evidence ID | `MS26-B1-*`、`MS26-B2-*`、`MS26-B3-*`、`MS26-B4-*` の一意ID |
| source | document/code inspection、Codex command、automated test、user manual report、actual MMD |
| HEAD | 実行時のcommit ID |
| executor | Codexまたはユーザー |
| environment | OS build、Python、依存、FFmpeg、MMD version/build |
| material identity | 音声、TEXT、model、morph set、preset、profile、Whisper identity |
| action/result | 実行内容と結果。pass数だけでなくprocess exit codeを記録 |
| expected result | 事前に定義した期待結果 |
| actual result | 実際の出力・観測結果 |
| reproducibility | 再現性、再実施回数、条件差 |
| evidence location | log、screenshot、artifact、報告の所在。未保存ならその旨 |
| limitation | 未実施、skip、未確認、再実行要否 |

保存先は本書§16とする。B1はschemaとbaseline、B2は自動回帰、B3はGUI・実MMD、B4はfinding解消・再検証・Closeoutの行を所有する。production code、test code、GUI、または対象契約の変更後は、B4が影響行を`stale`へ変更し、新HEADで再実行する。意味を変えない文書補正だけの場合は、非失効の根拠と新HEADを追記する。

### 8.3 未確定情報の扱い

外部素材や環境が提供されていない場合は、仮の音声・過去のmodel・推測したmorph名で受入を成立させない。計画上はB3開始条件として列挙し、B3開始時にidentityを確定する。

### 8.4 仕様findingの扱い

仕様書内で意図が一意でない場合は、コードを先に合わせて契約を変えない。現在のコード、MS25契約、仕様書の他の固定記述を並べ、ユーザー判断または明示された正文修正を経てからB2以降へ進む。

## 9. 詳細ステップ

### B1-01: 現行ベースラインの固定

- branch、HEAD、`origin/main`、既存変更、最近の履歴を一つずつ確認する。
- `.venv` のPython version、主要依存import、リポジトリ内FFmpeg/ffprobeのversionを記録する。
- 現在のHEADに紐づくB1計画・Index・Block Breakdownの状態を台帳へ記録する。

### B1-02: MS25契約と現行実装の照合

- `DeliveryCurrentState`、`DeliveryStartContext`、start gate、commit fingerprint、source audio identityを確認する。
- deliveryの成果物順序をVMD → MMD用WAV → reportとして確認する。
- VMDがcurrent `EffectiveShapePlan`、MMD用WAVがoriginal source audio、reportが同一diagnostic snapshotから生成されることを確認する。
- worker、Busy、cancel、close、late result、cleanup failure、destination collisionの境界をGUI実装と直接テストへ対応付ける。

### B1-03: 音声・VMD・Whisper identityの照合

- user input audio、internal analysis WAV、exported MMD-use WAVを別物として記録する。
- VMDの30fps、morph-only、model name、Japanese `あ / い / う / え / お`、Latin `A / I / U / E / O`を確認する。
- selected / active / loaded / analysisのWhisper model key、display、manifest identityを独立項目として記録する。
- voice-onlyではTEXTが入力されない場合があるため、transcription text、timing source、検証済みmodel identityを別途要求する。

### B1-04: MMD用WAV仕様findingの確定

- `MMD_WAV_SPEC` が `pcm_s16le`、44100 Hz、2 channelであることを確認する。
- validatorがRIFF/WAVE、先頭`fmt`、fmt size 16、PCM format 1、channel 2、16bit、data chunk、非空dataを要求することを確認する。
- 正文書の§3.3、§5.4、§7.2、§10.3、§14.3をchannel count 2（stereo固定）へ同期した。
- 当初のP2仕様findingは、現行`MMD_WAV_SPEC`、validator、正文仕様、MS25契約をchannel count 2（stereo固定）で一致させることで解消した。mono許容の実装変更は本計画に含めない。
- 正文仕様§8.3に従い、解析用WAVとMMD用WAVのduration差0.05秒以内をB2の自動gateとする。現行validatorまたは既存testで証明できない場合は、B2所有のcoverage / contract findingとして記録し、比較対象、取得方法、超過・取得不能時のfailureをテストする。

### B1-05: B2自動回帰の実行計画確定

- まずMS17-B7の個別MMD用WAV export / validation / failure cleanup / save dialog / overwrite confirmation / button stateを必須回帰として実行する。
- 次にMS25 B1〜B6の直接テストと、MS19〜MS24の境界テストを責務ごとに実行する。
- 次にpipeline/VMD、diagnostics/report、GUI state/worker、audio/WAV、delivery、collision/recoveryを含む横断回帰を実行する。
- 解析用WAVとMMD用WAVのduration差0.05秒以内、比較不能、許容差超過をB2所有の自動テストで確認する。
- 最後にfull pytest、`compileall`、`git diff --check`を一つずつ実行する。
- pass数だけでなくprocess exit code、skip、failure、実行HEADを記録する。B1ではB2 full pytest・横断回帰を実行しないが、修正検証として実施した対象テストは別証拠として記録する。

### B1-06: B3手動GUI・実MMD証拠様式の確定

- GUI確認は、実行者をCodexまたはユーザーとして明示する。ユーザー報告をCodex自身のGUI実行結果として記載しない。
- 各手動確認には操作、期待結果、実結果、再現性、証拠所在を記録する。
- 実MMDは、出力されたVMD/WAVの存在確認だけで終えず、MMDでの load、play、morph mapping、timing、visual resultを分けて記録する。
- `voice_only`では、検証済みmodelが未配置のnegative pathで暗黙download、cloud ASR、音声外部送信、background通信が発生しないことを確認する。
- Japanese profileとLatin profileを両方確認するかはB3開始時にユーザー判断として確定し、片方だけの場合は未実施の組み合わせを残す。

### B1-07: current state同期と計画監査

- B1計画の作成済み、B2/B3/B4未実施、実MMD素材未確定、MS27 deferredをMS20 Indexへ反映する。
- Indexや計画書が、実施済み・検証済み・未検証・deferredを混同していないか確認する。
- 既存のIndex変更と未追跡Block Breakdownを上書きせず、本計画の差分だけを確認する。

## 10. 状態遷移 / データ契約

### 10.1 B1〜B4の状態

```text
B1 plan-created
  -> B1 precheck-complete
  -> B1 baseline/contract-gate-passed
  -> B2 auto-regression-running
  -> B2 auto-regression-passed
  -> B3 material/environment-gate-passed
  -> B3 actual-MMD-evidence-recorded
  -> B4 revalidation-and-closeout-review
```

B1 plan / precheckは、未確定の実MMD素材・環境をB3開始条件として記録した時点で完了できる。B1 baseline / contract gateは、必須test群、evidence ledger、未解決のblocking contractが固定された場合だけ通過し、B2へ進む。実MMD素材または実行環境が未確定でもB2は実行できるが、`B3 material/environment-gate-passed`には遷移せず、B3のGUI・実MMD操作を開始しない。自動テストが成功しても、実MMDのload/play/morph/timing/visualを完了扱いにしない。

2026-09-06のB1実施記録では、B1-01〜07のdocumentation / static baseline、contract照合、evidence ledger、B2〜B4の証拠境界を完了した。必須test群、ledger、blocking contractはB1で固定する受入条件を満たしたため、`B1 baseline / contract-gate-passed`へ遷移する。B2必須test群はB1の実施範囲外として未着手であり、このB1 passedは自動test成功を意味しない。

### 10.2 MS25から保持するデータ契約

| 契約 | B1で固定する意味 |
| --- | --- |
| Effective output | Preview、writer、diagnostics、report、deliveryは同じeffective output意味を共有する |
| VMD | current `EffectiveShapePlan`、30fps、morph-only、model name、resolved morph namesから生成する |
| MMD用WAV | original source audioから生成し、internal analysis WAVを流用しない。現行基準はPCM signed 16-bit、44100 Hz、stereo |
| Report | 同じimmutable diagnostics snapshot、generation identity、Whisper identity、fingerprintを記録する |
| Morph | Japanese `あ / い / う / え / お`、Latin `A / I / U / E / O`。modelに実在する名前をB3で確認する |
| Whisper | selected / active / loaded / analysisのkey・display・manifest identityを混同しない。voice-onlyは検証済みmodelを要求する |
| Delivery | VMD、MMD用WAV、reportをdedicated staging directoryで生成・検証し、全成功とcommit guard通過時だけ確定する |
| Collision/recovery | 同名directoryのmerge、replace、delete、automatic renameを行わず、failure/cancel/cleanup failure時に既存出力を保護する |
| Fingerprint | `ms21-effective-output-v1` のsemantic fingerprintを保持し、projection generationをeffective meaningへ混ぜない |

### 10.3 B3受入素材・環境の必須identity

| 項目 | 必須記録 | 未提供時の扱い |
| --- | --- | --- |
| Windows | Windows 11 version/build、実行者、実行日時 | B3開始条件 |
| MMD | version/build、実行ファイルpathまたは識別情報 | B3開始条件 |
| model | PMX/PMDの識別情報、model名 | B3開始条件。repoへコピーしない |
| morph | modelに存在する対象morph名とJapanese/Latin対応 | B3開始条件。推測しない |
| audio | input path、形式、size、duration、必要なidentity | B3開始条件。repoへコピーしない |
| TEXT | 使用時のpathまたは識別情報、入力内容の扱い | 使用しない場合はN/A、voice-onlyは未入力を明記 |
| Whisper | model key、manifest identity、selected/active/loaded/analysis identity | voice-onlyのB3開始条件 |
| preset | preset ID/displayと適用結果 | B3開始条件 |
| profile | profile ID/display、morph-name set、generation settings | B3開始条件 |
| language set | Japanese、Latin、両方または対象外 | B3開始時に明示 |
| output | VMD/WAV/reportのpath、size、format/readback、MMD観測 | 生成できない場合は失敗証拠として記録 |

## 11. テスト方針

### 11.1 B1で実行する確認

- Git/status、branch、HEAD、remote参照、差分の読み取り。
- Python version、主要依存import、FFmpeg/ffprobe version。
- 仕様・コード・テストの静的な対応付け。
- `git diff --check`。未追跡Block Breakdownは差分表示のexit codeとwhitespace診断を分けて記録する。
- B2 full pytest・横断回帰、compileall、GUI起動、実MMDはB1では実行しない。修正検証として実施した対象テストは、full gateとは分けて記録する。

### 11.2 B2で実行する自動回帰

実装変更または修正が入った場合は、修正後HEADで影響範囲を再実行する。順序は次のとおりとする。

1. MS17-B7個別MMD用WAVテスト: export、validation、failure cleanup、save dialog、overwrite confirmation、button state。
2. MS25 B1〜B6直接テスト: current state gate、delivery contract、Windows path、orchestration、commit、artifact、VMD readback、report identity、worker、GUI、failure/recovery。
3. MS19〜MS24関連テスト: textless/voice-only、transcription edit、analysis worker、Preview、effective output、warning、diagnostic、profile、Whisper identity、runtime data禁止、no implicit download。
4. MMD用WAV durationテスト: 解析用WAVとの差0.05秒以内、比較不能、許容差超過時のfailure。
5. `tests/test_pipeline_and_vmd.py` と `tests/test_vmd_writer_*.py`。
6. repository全体の `.\.venv\Scripts\python.exe -m pytest`。
7. `.\.venv\Scripts\python.exe -m compileall -q src tests`。
8. `git diff --check`。

各コマンドは一つずつ実行し、終了コードを記録する。runnerがpass表示を出してもprocess exit codeが非0なら成功とは判定しない。

### 11.3 B3で実行する手動確認

- GUI: TEXT + audio、voice-only、profile/preset選択、Japanese/Latin対象、Preview、個別保存、一括出力、Busy、cancel、collision、failure、再試行、close待機を、実際に実行した範囲だけ確認する。`voice_only`の検証済みmodel未配置時には、暗黙download、cloud ASR、音声外部送信、background通信が発生しないことも確認する。
- 実MMD: VMD load、MMD用WAV load、play、morph mapping、lip timing、visual resultを別々に確認する。
- 手動結果は、Codex実行、ユーザー報告、未実施を区別する。MS25の過去のユーザー報告はMS26実績へ自動転用しない。

### 11.4 B4で実行する再検証

- P1/P2/P3 findingの修正後は、修正ファイルと契約影響を確認する。
- code、test、GUI、WAV/VMD/report、delivery commit、runtime data、packagingのどの境界に影響したかを判定する。
- 影響対象の自動テスト、全体回帰、compileall、diff checkを修正後HEADで再実行する。
- MMD出力意味、morph名、WAV形式、delivery結果、GUI状態に影響した場合は、B3の該当手動確認と実MMD確認を再実行する。

## 12. 受け入れ条件

- B1個別計画がMS26 Block Breakdownを正本として作成され、対象、除外、契約、状態、テスト、証拠様式、再実行条件を含む。
- 現行Git状態、HEAD、Python、主要依存、FFmpeg/ffprobe、MS25 Closeout A契約が計画の前提として記録されている。
- MS25の自動テスト結果、過去のユーザー報告、B2以降の新しい実行結果、実MMD結果が別の証拠sourceとして定義されている。
- 実MMDに必要な全項目がidentity付きで列挙され、未提供項目が未確定またはB3開始条件として扱われている。
- `MMD_WAV_SPEC` / validatorと正文仕様のchannel契約がchannel count 2（stereo固定）で一致し、mono許容などの実装変更を推測で開始しない。
- 解析用WAVとMMD用WAVのduration差0.05秒以内がB2所有の自動gateとして定義され、比較不能・超過時の扱いが明記されている。
- B2自動回帰、B3手動GUI・実MMD、B4再検証・closeoutの完了条件と境界が重複なく記載されている。
- evidence ledgerの保存先、B1〜B4のID、所有Block、HEAD変更時の失効条件、手動証拠の期待結果・実結果・再現性・証拠所在が定義されている。
- 本B1でproduction code、test code、GUI、runtime user data、依存、lock、PyInstaller、外部素材、Git履歴を変更していない。
- MS20 IndexがB1実施後のcurrent state、B2〜B4未実施、B3未確定事項、MS27 deferredを正しく示す。

## 13. リスクと対策

| リスク | 影響 | 対策 |
| --- | --- | --- |
| 実MMD素材が未提供 | Actual MMD closeout不能 | B3開始条件として列挙し、未検証のままcloseoutしない |
| modelのmorph名が想定と異なる | VMD load後にmorph mapping不能 | PMX/PMD上の実在名を記録し、Japanese/Latinを別判定する |
| MMD用WAVの仕様契約を誤って変更 | validatorと受入判定が分岐する | `MMD_WAV_SPEC`、validator、正文仕様、MS25契約をchannel count 2（stereo固定）で維持し、B2で自動回帰を実施する |
| MMD用WAVのduration gateが未実装・未被覆 | 音声とVMDの時間軸ずれを自動検出できない | B2で解析用WAVとの差0.05秒以内、比較不能、超過failureを自動テストへ固定する |
| 解析用WAVとMMD用WAVの混同 | 音声長・channel・MMD再生結果の誤判定 | 3つの音声roleを台帳と出力確認で分離する |
| Whisper identityの混同 | voice-onlyの再現性・診断不備 | selected/active/loaded/analysisを別々に記録する |
| 過去HEADの結果を転用 | 新HEADの回帰漏れ | 全結果にHEADと実行日時を付与し、修正後は再実行する |
| pytestのpass表示とprocess exit codeの不一致 | false pass | 終了コードを必須記録し、非0を成功扱いしない |
| staging/cleanup failureの見落とし | 既存出力または残存一時出力の扱いを誤る | terminal resultのprimary status、commit phase、cleanup statusを別記録する |
| B1からMS27へ範囲拡張 | 検証目的の散逸 | package/release readinessはMS27へ留保する |

## 14. Codex実装時の注意

- B1計画作成後に実装へ進む場合も、ユーザーが承認した対象ブロックだけを変更し、MS26-B1の計画・precheckとB2以降の実装を混同しない。
- runtimeの `presets.json`、`profiles.json`、`MMD_AutoLipTool.ini` は直接編集、コピー、stageしない。外部のMMD、PMX/PMD、音声、TEXT、Whisper modelもリポジトリへ持ち込まない。
- `EffectiveShapePlan`、resolved morph names、source audio identity、Whisper identity、diagnostics snapshot、delivery fingerprintを別々に保持する。
- VMD writer/readback validation、MMD用WAV validator、MMD本体の視覚的受入は異なる証拠である。writerまたはvalidatorのpassをMMD visual passへ置き換えない。
- GUIのBusy、cancel、late result、close待機、commit guard、cleanup failureを省略した手動確認を完了扱いしない。
- 仕様のchannel契約を変更する場合は、先にユーザー判断または明示的な仕様修正を得て、コード・テスト・README・受入証拠の全境界を同時に再評価する。
- stage、commit、merge、push、tag、releaseは別承認が必要であり、本計画の完了だけでは実行しない。

## 15. B3開始条件として未確定の事項

以下はB1で推測せず、B3開始前に確定する。

1. Windows 11の実行環境とbuild。
2. MMDのversion、build、実行ファイル。
3. 対象PMX / PMD、model name、model上の対象morph名。
4. 実受入用audioと、そのTEXTの有無。
5. `voice_only`で使う検証済みWhisper model keyとmanifest identity。
6. 適用するpreset。
7. 適用するmodel profile、morph-name set、generation settings。
8. Japanese profileとLatin profileの双方を確認するかどうか。

これらが未確定の場合、B1の計画・precheckとB2自動回帰は進められるが、B3 material / environment gateは通過させず、B3のGUI・実MMD受入とMS26 Closeout判定は未完了のまま維持する。

MMD用WAVのchannel countは未確定事項ではない。現行`MMD_WAV_SPEC`、validator、正文仕様、MS25契約をchannel count 2（stereo固定）で同期し、B1ではstereo固定を実行基準かつruntime契約として扱う。

## 16. MS26 Evidence Ledger

本節をMS26-B1〜B4のevidence ledgerの保存先とし、別ファイルへ分散させない。B1はschemaとbaseline行、B2は自動回帰行、B3はGUI・実MMD行、B4はfinding解消・再検証・Closeout行を追記する。

実施担当: Luna MAXサブエージェントCicero、Agent ID `01a07406-0408-73d1-9187-beb4d896d48e`（起動API確認済みとしてメインから提供）。初回実測は2026-09-06。2026-09-07の補正は表構造、現行回帰入口、担当ID、コマンド記録、B3適用条件に限定した文書修正である。2026-09-07にメインが3文書の最終差分を照合し、B1/B2 gate境界・証拠参照・STEREO固定を確認した。`git diff --check`はprocess exit code `0`。B1文書のP1 / P2 / P3残存はなく、B2所有のduration findingとB3未確定事項は維持する。B1 baseline / contract gate passed、B2未着手（別途依頼後）は維持する。

| evidence ID | owner | requirement | source | HEAD | executor | environment / material identity | action | expected result | actual result / exit code | reproducibility | evidence location | limitation / status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `MS26-B1-001` | B1 | B1-01 live baseline | 2026-09-06 live command set | `e2d63ad1`、`origin/main=4e85682682c6dda6ce72b0fea3e883b4ee87d5ce` | Codex main precheck; Luna MAX sub-agent Cicero（IDは本節冒頭） | PowerShell; `.venv` Python `3.14.3`; wx / matplotlib / numpy / whisper / pyopenjtalk import; repository FFmpeg / ffprobe | `git status --short --branch`、`git branch --show-current`、`git log --oneline -n 10`、`git branch -vv`、`git rev-parse HEAD` / `origin/main`、`git diff --name-status c881264..HEAD`、`git diff --quiet c881264..HEAD -- src tests pyproject.toml uv.lock`、Python version / executable / import、FFmpeg / ffprobe versionを実行 | branch、HEAD、origin/main実値、開始時clean、docs-only境界、環境versionを記録 | status / branch / log / branch -vv / rev-parse / diff / Python / import / FFmpeg / ffprobeはexit `0`。HEAD=`e2d63ad1d1469f6a74ee09d508c26c1c4b47ba08`、origin/main=`4e85682682c6dda6ce72b0fea3e883b4ee87d5ce`、upstream未設定、`src` / `tests` / `pyproject.toml` / `uv.lock`差分なし | 同一workspaceでread-only commandを再実行。pytestは実行しない | 実施時のcommand output、§6。Cicero IDは本節冒頭に記録 | 開始時clean。以後のworking tree変更は本B1文書編集。B3素材と現行test passは未確定 / pass（baseline） |
| `MS26-B1-014` | B1 | B1-01 static search / diffcheck command record | 2026-09-06 existing session log | `e2d63ad1` | Codex main precheck; Luna MAX sub-agent Cicero（IDは本節冒頭） | PowerShell; repository source/spec/test paths | `rg -n -C 3 "channel_count\|mono\|analysis WAV\|analysis_wav\|ANALYSIS" src\core\audio_convert.py src\core\ffmpeg_runner.py src\gui_wx\audio_worker.py`、`Get-Content -LiteralPath src\core\delivery_artifacts.py`、`Get-Content -LiteralPath src\gui_wx\audio_worker.py`、`rg -n -C 3 "delivery\|cancel\|closing\|late\|stale\|cleanup\|Busy\|busy\|worker\|commit\|terminal" src\gui_wx\app_controller.py src\gui_wx\main_frame.py src\gui_wx\right_pane.py src\gui_wx\audio_worker.py src\gui_wx\worker_state.py src\gui_wx\delivery_worker.py src\gui_wx\delivery_controller.py`、`git diff --check`を記録 | static code pathを確認し、missing pathを成功扱いせず、whitespaceをexit `0`で確認 | analysis WAVの`rg`、2つの`Get-Content`、`git diff --check`はexit `0`。delivery worker/controllerを含む検索は、指定範囲の`src\gui_wx\delivery_worker.py`と`src\gui_wx\delivery_controller.py`が存在せずexit `1`。これは`rg`のmissing-file診断であり、pytest / GUI結果ではない | 同一HEAD・同一pathで再実行可能。今回の補正では再実行していない | `C:\Users\visua\.codex\sessions\2026\09\06\rollout-2026-09-06T09-02-26-01a07406-0408-73d1-9187-beb4d896d48e.jsonl`のB1 command output | static inspection record。missing pathのexit `1`をpassへ変換しない / pass（record） |
| `MS26-B1-002` | B1 | B1-02 MS20〜MS25要求・履歴・既存test・ユーザー報告・未検証境界 | MS20 Index §2 / §3.1以降、MS25-B7 plan、MS20〜MS25 code / test static inspection | `e2d63ad1`（履歴証拠は各旧HEAD） | Codex historical record; Luna MAX / Cicero（今回のmapping編集）; GUI報告はユーザー | ローカル文書・現行code / test。実MMD素材なし | 実装履歴、test所在、ユーザー報告、未検証事項を分類し、MS20〜25の詳細を下記6行へ分解 | current static stateとhistorical evidenceを混同しない | MS25旧HEAD `0b25c5c`のB6 required `26 passed`、aggregate `160 passed, 2 skipped`、cross-boundary `322 passed`、full `1041 passed, 4 skipped`はいずれもexit `0`の歴史証拠。現行HEADで未実行 | 文書・既存Indexを同一current stateへ再照合。旧test totalsを転用しない | MS20 Index §2 / §3.1以降、MS25-B7 §16.1〜§16.4、本ledger | MS20〜MS25の現行HEAD横断pass、実MMD、Python 3.11 / 3.12は未検証 / pass（roll-up mapping） |
| `MS26-B1-MS20` | B1 | MS20要求・実装履歴・test・旧GUI・未検証 | MS20 Index §§3.1〜3.9 | 歴史HEAD（commit IDは節ごとに一部のみ記載） | Codex historical record; user GUI report; Cicero（mapping） | MS20開発時環境。実MMDなし | Indexの節と結果を対応付け | diagnostics / playback / report / warningの各履歴を分離 | 実装commitとして`b6f4254`（MS20-B2）を確認。B3以降の個別commit IDはIndexに記載なし（不明）。test群はB2 12件＋非正duration 1件＋限定24件、B3 12＋16＋8、B4 24、B5 17＋64＋35＋subtest 7＋pipeline/VMD 12、B6 13＋10＋50＋28＋subtest 7＋6＋12、B7 11＋97＋12＋48＋subtest 7。旧GUI報告はB3 10項目、B4、B5 13項目、B6 14項目、B7。MS20 full suiteのwx exit `1`も歴史記録 | 現行HEADでは再実行していない | `MS20_and_Beyond_Index.md` §§3.1〜3.9。現行回帰入口（本plan §7参照）: `tests/test_ms20_b2_output_diagnostics.py`、`tests/test_ms20_b6_diagnostic_report.py`。旧test総数の実行コマンドとは別の参照 | actual MMD、現行HEAD pass、Python 3.11 / 3.12は未検証 / historical mapping |
| `MS26-B1-MS21` | B1 | MS21要求・実装履歴・test・旧GUI・未検証 | MS20 Index §§3.10〜3.30 | 個別commit IDはIndexに記載なし（不明） | Codex historical record; user GUI report; Cicero（mapping） | MS21開発時環境。実MMDなし | B1〜B8の実装・closeout記録を対応付け | effective output / Preview / editor / history / lifecycleの履歴とCloseoutを分離 | test群はB2 35＋指定156＋full 511＋subtest 7、B3 22＋Preview/selection/viewport 50＋full 533＋subtest 7、B6 core 12＋wx 9＋関連99＋full 602＋subtest 7、B7 15＋61＋47＋subtest 7＋wx 97＋full 617＋subtest 7、追加補正はRightPane 3＋Preview 6＋lifecycle 12＋wx 90＋full 618＋subtest 7。旧GUI報告は§3.17、§3.20、§3.25、§3.29、Closeout再利用は§3.30 | 現行HEADでは再実行していない | `MS20_and_Beyond_Index.md` §§3.10〜3.30。現行回帰入口（本plan §7参照）: `tests/test_ms21_b5_effective_output_identity.py`、`tests/test_ms21_b7_analysis_rollback.py`。旧test総数の実行コマンドとは別の参照 | actual MMD、現行HEAD pass、個別commit IDは未確認 / historical mapping |
| `MS26-B1-MS22` | B1 | MS22要求・実装履歴・test・旧GUI・未検証 | MS20 Index §§3.31〜3.46 | B3 `4ee67af Implement MS22-B3 preset store and settings contract`。その他の個別commit IDはIndexに記載なし（不明） | Codex historical record; user GUI report; Cicero（mapping） | MS22開発時環境。runtime user dataは受入証拠にしない。実MMDなし | Contract Fixed、B2〜B6、Closeoutを対応付け | 要求・実装履歴・旧GUI報告・未検証境界を対応付ける | test群はB1 336、B2 26＋MS21 core/Preview 102＋text/pipeline/VMD 51＋full 644＋subtest 7、B3 23＋subtest 19＋SettingsStore等29＋指定21/13/35/17＋full 667＋subtest 26、B5 10＋full 694、B6 non-wx 7＋wx 9＋splash 3＋full 713、Closeout direct 93＋基盤185＋MS21 138＋MS17/19/20 158＋組合せ18＋full 713。旧GUI報告は§3.42、§3.44、Closeoutでの再利用は§3.46 | 現行HEADでは再実行していない | `MS20_and_Beyond_Index.md` §§3.31〜3.46。現行回帰入口（本plan §7参照）: `tests/test_ms22_b3_generation_presets.py`、`tests/test_ms22_b6_lifecycle_regression.py`。旧test総数の実行コマンドとは別の参照 | actual MMD、現行HEAD pass、上記B3以外の個別commit IDは未確認 / historical mapping |
| `MS26-B1-MS23` | B1 | MS23要求・実装履歴・test・旧GUI・未検証 | MS20 Index §2のMS23履歴（2026-08-12〜20） | B4B `cc23666 Implement MS23-B4B wx teardown repair`。B2/B4/B5等の全個別commit IDはIndexに記載なし（不明） | Codex historical record; user GUI report; Cicero（mapping） | MS23開発時環境。実MMDなし | profile / morph set / preset / wx lifecycle / Closeoutを対応付け | 要求・実装履歴・旧GUI報告・未検証境界を対応付ける | test群はB2 24＋関連228＋full 738、B3関連回帰とfull 759＋subtest 57、B4 12＋MS20/21/22関連52＋full 771＋subtest 57（exit `1`）、B4B既知10＋wx 129×2＋non-wx 644＋subtest 57＋full 773＋subtest 57、B5関連31＋full 785＋subtest 57、Closeout direct 82＋subtest 31＋関連90＋diagnostics等174＋lifecycle54＋subtest 7＋full 797＋subtest 57。旧GUI報告はMS23-B2 / B5等のIndex記録、Closeout再利用は同履歴 | 現行HEADでは再実行していない | `MS20_and_Beyond_Index.md` §2 MS23履歴。現行回帰入口（本plan §7参照）: `tests/test_ms23_b2_morph_name_adapters.py`、`tests/test_ms23_b6_model_profile_lifecycle.py`。旧test総数の実行コマンドとは別の参照 | actual MMD、現行HEAD pass、全commit IDは未確認 / historical mapping |
| `MS26-B1-MS24` | B1 | MS24要求・実装履歴・test・旧GUI・未検証 | MS20 Index §2のMS24履歴、§§3.47〜3.49 | B1 `eafdc16 Implement MS24-B1 Whisper model contract`、B6 `1f1aff2 Implement MS24-B6 diagnostics and recovery`。B4/B5の個別commit IDはIndexに記載なし（不明） | Codex historical record; user GUI report; Cicero（mapping） | Python 3.14.3の旧開発環境。実model / network / MMDなし | Whisper identity、local-only model、diagnostics、recovery、GUI report、Closeout境界を対応付け | 要求・実装履歴・旧GUI報告・未検証境界を対応付ける | test群はB3 full `846 passed, 2 skipped`、B4 `860 passed, 2 skipped, 77 subtests`、B5 `872 passed, 2 skipped`、B6 `881 passed, 2 skipped`、各exit `0`。旧GUI報告はB3/B4/B5/B6、Codex GUIではない。Python 3.11/3.12、3.13、実model、実Whisper解析、実MMDは未検証 | 現行HEADでは再実行していない | `MS20_and_Beyond_Index.md` §2、§§3.47〜3.49。現行回帰入口（本plan §7参照）: `tests/test_ms24_no_implicit_download.py`、`tests/test_ms24_whisper_diagnostics.py`。旧test総数の実行コマンドとは別の参照 | actual MMD、現行HEAD pass、B4/B5 commit IDは未確認 / historical mapping |
| `MS26-B1-MS25` | B1 | MS25要求・実装履歴・test・旧GUI・未検証 | MS20 Index §2、MS25-B7 plan §§16.1〜16.4 | B1 `a41f0a0`、B2 `0f018cd`、B3 `904ccae`、B5 `bb9c60d`、B6 `5300905`、Closeout基準 `c881264`。B7検証HEAD `0b25c5c` | Codex historical record; B5/B6 GUIはuser report; Cicero（mapping） | Python 3.14.3、FFmpeg、旧MS25素材。実MMDなし | B1〜B7とCloseoutのtest / GUI / 未検証境界を対応付け | 要求・実装履歴・旧GUI報告・未検証境界を対応付ける | MS25-B1〜B6 aggregate `160 passed, 2 skipped`、B6 required `26 passed`、cross-boundary `322 passed`、full `1041 passed, 4 skipped`、各exit `0`。関連test file群はMS25-B1〜B6専用test、delivery artifact / report / worker / recovery群。B5/B6 GUIはユーザー報告のみ。実MMD、Python 3.11/3.12、現行HEAD passは未検証 | 旧HEADのcommand log / plan記録を再利用し、現行HEADへ転用しない | MS25-B7 plan §16.1〜§16.4、MS20 Index §2。現行回帰入口（本plan §7参照）: `tests/test_ms25_b3_delivery_artifacts.py`、`tests/test_ms25_b6_delivery_failure_recovery.py`。旧test総数の実行コマンドとは別の参照 | historical mapping。actual MMD、現行HEAD pass、MS27は未完了 |
| `MS26-B1-003` | B1 | B1-03 audio / VMD / Whisper identity | `pipeline.py`、`audio_convert.py`、`morph_name_sets.py`、`diagnostic_report.py`、GUI adapter、関連spec | `e2d63ad1` | Codex | 入力audio / internal analysis WAV / MMD用WAVは実素材なし | audio role、EffectiveShapePlan、resolved morph names、30fps、morph set、selected / active / loaded / analysis identityを照合 | input / analysis / outputのroleとidentityが分離される | internal analysisはmono、MMD用WAVはstereo、VMDはcurrent EffectiveShapePlan、JA `あ / い / う / え / お`、Latin `A / I / U / E / O`、Whisper identity 4種を確認 | 現行code / spec / test pathを再読。B3素材確定後に実データで再確認 | 本plan §9 B1-03、§10.2〜§10.3 | 実model morph、profile / preset、voice_only model manifest、JA / Latin方針は未確定 / pass（static）・B3 pending |
| `MS26-B1-004` | B1 | B1-04 MMD WAV contract | `mmd_wav_export.py`、`audio_convert.py`、`ffmpeg_runner.py`、MMD WAV spec、MS17-B7 / MS25 tests | `e2d63ad1` | Codex | `MMD_WAV_SPEC`と現行validator、実WAV素材なし | spec / code / validator / test coverageを照合 | MMD用WAVは絶対に`pcm_s16le`・44100 Hz・2 channel（STEREO固定）; internal analysisはmono | `MMD_WAV_SPEC`一致、validatorはRIFF/WAVE・fmt・PCM・2ch・16bit・dataを検証、export返却durationはinput probe由来、validatorはanalysis/output duration差を検証しない。既存testにduration差比較はない | static code / spec / test inspection。duration gateはB2で実測 | 本plan §9 B1-04、MMD WAV spec §3.3 / §5.4 / §7.2 / §8.3 / §10.3 | channel契約はpass。`<= 0.05秒` duration取得・比較・超過・取得不能はB2所有のopen finding |
| `MS26-B1-005` | B1 | B1-05 B2 automatic regression boundary | 本plan §11.2、Block Breakdown MS26-B2、MS17-B7 / MS19〜MS25 test inventory | `e2d63ad1` | Codex（計画固定のみ）; Luna MAX / Cicero（今回の台帳補正） | Python / dependency / FFmpegはB1-001、B3素材は未確定 | MS17-B7 → MS25 B1〜B6 → MS19〜MS24 → duration → pipeline/VMD → full pytest → compileall → diff checkの順序、exit / skip / revalidation rulesを固定 | B2は各commandを単独実行し、pass表示でなくprocess exit `0`、skip理由、実行HEADを記録 | B2自動回帰、duration gate、full pytest、compileallは未実施。B2へ渡すfindingはduration差の比較不能 / 超過 / 取得不能を成功扱いしないこと | B2開始時に同じ順序で再実行。修正HEADでは影響testからfull gateまで再検証 | 本plan §11.2、Block §7 MS26-B2 | planned。B1 baseline / contract gateはpassed、B2は未着手 |
| `MS26-B1-006` | B1 | B1-06 GUI / actual MMD evidence boundary | 本plan §11.3、GUI State / Error Handling / VMD / MMD WAV spec、MS25 user report | `e2d63ad1`（user reportは旧実施時HEAD） | Codexは様式のみ; 旧GUIはユーザー | Windows 11 / MMD / model / audio / TEXT / profile / preset / Whisper未提供 | GUI manual、VMD / WAV load、play、morph mapping、timing、visual resultを分離する記録様式を固定 | Codex実行、ユーザー報告、未実施を明示し、自動testやwriter / validatorをMMD visual passへ置換しない | 今回のGUI / MMD操作は未実施。MS25 B5 / B6 GUI報告はユーザー報告としてのみ保持。MMD load / play / morph / timing / visualは未検証 | B3素材・環境・実行者を固定後、各項目を個別に実施して再現情報を記録 | 本plan §10.3、§11.3、§15、Block §7 MS26-B3 | B3 material / environment gate未通過 / pending |
| `MS26-B1-007` | B1 | B1-07 current state sync / plan audit | 本plan、Block Breakdown、MS20 Index、Roadmap §13〜§15 | `e2d63ad1` | Codex; Luna MAX / Cicero（今回の台帳補正） | 文書のみ | B1実施状態、B1 baseline / contract gate passed、B2未着手、B3〜B4未実施、MS27 deferred、未確定B3項目を同期 | current state、historical evidence、planned / pending / deferredを混同しない | 本B1実施記録・Index・Blockの状態を同期。Roadmapはcurrent state変更不要のため未編集 | B1文書変更後に`git diff --check`を実行し、P1 / P2 / P3残存と未検証範囲を再監査 | 本ledger、Block §1 / §7 / §18、Index §2 | pass（B1 baseline / contract documentation sync）。B2/B3/B4へは進まない |
| `MS26-B2-001` | B2 | automated cross-boundary regression | B1で固定したtest inventory、MS26-B2 plan §15.2 | `ff57305` + B2 working tree | Curie、Agent ID `01a08405-19f5-7b11-a814-62570eea666b`（実装・テスト）、親メイン（統合レビュー） | Python 3.14.3、repo-local FFmpeg/ffprobe、analysis mono / MMD stereo | MS17-B7 → MS25 → MS19〜MS24 → duration → pipeline/VMD → vmd_writer → full pytest → compileallを単独実行 | 初回は14 passed、160 passed + 2 skip、497 passed、duration 22 + 20/20、pipeline/VMD 13、writer 98、full 1064 passed + 4 skip。main補修後の最終値はMS26-B2 plan §15.2の`B2-R03`〜`B2-R11`へ固有ID付きで記録し、全必須exit `0`を要求 | symlink生成権限不足 `WinError 1314` の既存skip 4件。MS25 B6 collision/fault gateはskipなし | 初回失敗・中間失敗を含む履歴はMS26-B2 plan §15.2、main指摘6件と解消根拠は§15.5 | MS26-B2 plan §11.2、§15.2、Block §7 | passed（B2 auto-regression、補修後再検証済み） |
| `MS26-B2-002` | B2 | analysis / MMD WAV duration gate | MMD WAV spec §8.3、`mmd_wav_export.py`、B2 test-only helper / integration、MS26-B2 plan §15.3 | `ff57305` + B2 working tree | Curie、Agent ID `01a08405-19f5-7b11-a814-62570eea666b`（実装・テスト）、親メイン（統合レビュー） | Python 3.14.3、repo-local FFmpeg/ffprobe、analysis mono / MMD stereo | `wave`の実frames/rate/data read-back、probe前後source SHA-256、同一入力由来の比較、`<= 0.05秒`判定、超過・取得不能・role/path/source mismatchをnegative test化 | 初回unit 22 / integration 20 case。補修後unit 25 passed、実FFmpeg matrix 24/24 measured、全差0。2205 samples差はpass、2206 samples差はfailure。M4A codec実測長も両出力差0 | 保存時validator、result DTO、GUI、error codeへduration gateを接続しない判断A。実MMD / GUIはB3 | 2026-09-09にmain指摘の不合格再現・補修・独立read-backを実施 | MS26-B2 plan §8.1〜§8.2、§11.2、§15.3、§15.5 | resolved（test-only B2 finding、レビュー補修後） |
| `MS26-B3-001` | B3 | material / environment gate | 本plan §6、§9 B3-01 / §15、Block MS26-B3 | `a54e2cb`（B3開始時） | Codex（環境・素材の読み取り確認）; user（素材承認・AC03確認） | Windows 11 registry `25H2` / build `26200.9445`、MMD Ver 9.32、MMD exe / PMX / audio / TEXTの実ファイルidentity、audio `pcm_s16le` / 44100Hz / 2ch / 40.458639秒、`small` manifest identity / size / SHA-256 | 実受入の組合せをidentity付きで固定 | 適用項目確定、非適用は理由記録、model morphとresolved output names一致 | 外部ファイルidentity、音声形式、TEXT UTF-8、Whisper `small` identityは確認済み。ユーザーからAC03、日本語・ラテンの確認、MMD Ver 9.32、使用model pathの報告を受領。PMX hash、実model morph一覧、個別再現ログは未提示 | 2026-09-11に1回の読み取り確認、2026-09-12にユーザー報告を複数回受領。詳細値と再現ログは未提示 | 本plan §6、§9 B3-01、§14.3〜§14.4、同日のユーザー報告 | user-reported pass / AC03、MMD version / model path補完済み、PMX hash / morph一覧 pending |
| `MS26-B3-002` | B3 | manual GUI vs actual MMD acceptance | 本plan §11.3、§14.1〜§14.4、Block MS26-B3 | `a54e2cb`（runtime code） | user manual report（Codex GUI未実施） | `MS26-B3-001`の確認済み素材・環境。ユーザーからB3-T-JP / B3-T-LA / B3-V-JP / B3-V-LAの確認済み結果が提示された | GUI手動確認とactual MMDのload / play / morph / timing / visualを別記録する | GUI確認結果とactual MMD結果を実行者別に記録する | 2026-09-11のユーザー報告: 手動GUIテスト通過、問題なし。2026-09-12のユーザー報告: 日本語・ラテンおよび4主要ケースを確認し、問題なし。CodexによるGUI / 実MMD操作は未実施 | ユーザー報告を複数回受領。4ケースごとの詳細操作ログ・実施時刻は未提示だが、ユーザーはartifact対応を含む確認済みと報告 | 本会話のユーザー報告（2026-09-11〜2026-09-12） | user-reported pass / AC03・AC04、詳細証拠の転記 pending |
| `MS26-B3-003` | B3 | actual MMD case / artifact identity supplement | ユーザー報告、生成物の2026-09-12 read-only inspection、B3計画 §14.4 | 不明（ユーザー実MMD実施）; artifact inspectionは2026-09-12 | user（実MMD）; Codex（外部artifact read-only inspection） | MMD Ver 9.32、model `D:\Visual Works\MMD Folder\MikuMikuDance64\UserFile\Model\Kanna\Mobco\_V4B\Mobco\_v2\_2024B3\_edit2.pmx`、入力 `D:\Visual Works\Kanna Work\Voice\MMD_AutoLipTool説明1.wav`、出力directory `D:\Visual Works\Kanna Work\Voice\MMD_AutoLipTool説明1B_MMD` | ユーザーが4主要ケース、日本語・ラテンを実MMDで確認し、同じ入力 / 出力組を追跡できる | 4ケースの実MMD確認が問題なく、出力3成果物が読み取り可能 | ユーザー報告: `B3-T-JP` / `B3-T-LA` / `B3-V-JP` / `B3-V-LA`確認済み、日本語・ラテン問題なし。folder内にVMD 15,737 bytes（SHA-256 `8172E0FFB089FB255A10BDF69F5DEDE176EAF65AB2BDF8941E8134DBD3F30E94`）、MMD用WAV 7,136,948 bytes（SHA-256 `3CB803D89D475087D955BE1E484AA0D0C7E95F96585284DC8A45EAC0219227D0`）、report 3,734 bytes（SHA-256 `A7E86159414DD50800CA8B3C749F67AF9BE0C09AD9EF4B82215563DE84B9E91B`）を確認。WAVはPCM 16-bit / 44.1kHz / stereo / 約40.459秒。 | ユーザー報告とCodex read-only inspectionを各1回記録。実MMD操作自体はユーザー担当 | 本会話、外部生成物directory、B3計画 §14.4 | ユーザーは4ケースごとのartifact対応を含め確認済みと報告。一組のartifactはCodexが静的確認したが、個別directory名・PMX hash / morph一覧・reportの設定（`text_audio` / `Custom` / `decay`）と主要ケースの対応は本台帳へ未転記 |
| `MS26-B3-004` | B3 | additional GUI / recovery / Whisper manual gates | ユーザー報告、B3計画 §14.5 | 不明（ユーザー実施） | user（manual verification） | MS26-B3-001 / B3-003のMMD・model・audio環境 | `B3-G-PLAYBACK`、`B3-G-STATE`、`B3-V-EDIT`、`B3-D-COLLISION`、`B3-D-CANCEL`、`B3-D-FAIL`、`B3-D-CLOSE`、`B3-W-SELECT`、`B3-W-MISSING`、profile / preset適用と復帰を確認する | 正常、編集、保存可否、collision、cancel、failure recovery、close、未配置modelの安全停止、no-download、設定適用が問題なく動作する | ユーザーから上記項目をすべて確認し、主な不具合なし、正常作動との報告を受領。CodexによるGUI操作は未実施 | ユーザー報告1回。個別操作ログ、画面記録、再実施回数は未提示 | 本会話のユーザー報告（2026-09-12） | user-reported pass。詳細証拠は未転記。B2-R05 daemon候補の原因 / 影響は別findingとして維持 |
| `MS26-B4-001` | B4 | finding revalidation / closeout | 本plan §11.4、Block MS26-B4、Roadmap §13〜§15 | 未実行 | 未実行 | 修正後HEAD、影響test、B3素材 / environment | P1 / P2 / P3とB2 findingを修正後HEADへ再対応付けし、必要な自動・手動証拠を再取得 | 修正後の全影響証拠が同一HEADで有効、MS26 closeout条件を満たす | 未実施。B4 closeout判定を行わない | code / test / GUI / contract変更時は影響行をstale化し再検証 | 本ledger、Block §7 MS26-B4 | deferred / B4未実施。MS27 package / release readinessもdeferred |
| `MS26-B4-002` | B4 | Whisper availability worker / daemon exception candidate targeted revalidation | B4 plan §6.2、§9 B4-03、B2 plan §15.2 B2-R05 | `fe4c95c` | Codex main | Python 3.14.3、Windows、現行worker / controller / UI test、Whisper local-store test | `pytest -rs tests/test_ms24_whisper_model_availability_worker.py tests/test_ms24_whisper_model_runtime.py tests/test_ms24_no_implicit_download.py tests/test_whisper_model_store.py`、`pytest -rs tests/test_ms24_b4_controller.py`、`pytest -rs tests/test_wx_ms24_whisper_model_ui.py`を単独実行 | worker scan/runtime/no-download、controllerのrescan・stale guard、Whisper UI関連回帰がpassし、process exit 0。daemon候補の原因・影響は別途確定する | 27 items: 25 passed、2 skipped（`WinError 1314` symlink capability）、exit 0。controller 3 passed exit 0、UI 4 passed exit 0。B2-R05 daemon headerはこのテストでは再現せず、cause / impact未確定 | 3 targeted command executions、同一HEAD、`-rs`でskip詳細を取得 | 本セッションのpytest command output、B2 plan §15.2 B2-R05 | partial / candidate not reproduced; B3 material / actual MMD and full B4 closeout pending |
| `MS26-B4-003` | B4 | final acceptance audit / MS26 CloseOut | B4 plan §12、§15〜§16、B3 plan §14.3〜§14.6、Roadmap §13.5 | `fe4c95c` + current documentation working tree | Codex main（最終照合・文書同期）; user（GUI / actual MMD） | Python 3.14.3、Windows 11、MMD Ver 9.32、指定model / audio / MMD WAV、既存B1/B2 evidence | B4-AC01〜08、B1/B2自動gate、B3 user-reported GUI / actual MMD、追加手動gate、artifact read-back、MS27境界を照合 | 必須機能受入を満たし、未解消P1 / P2 / P3がなく、MS27移管範囲が明示される | B1/B2自動gateとB4 targeted revalidationは既存process exit `0`記録を再利用。ユーザーは実MMD上の音声・モーフ同期を含む確認をPass報告。B2-R05は再現なし・影響未観測の非確定観測として分類 | 今回の最終監査で文書・台帳・現在状態を照合。CodexのGUI / 実MMD操作は未実施 | 本会話、B4 plan §16、B3 plan §14.6、Roadmap §13.5 | pass / MS26 CloseOut A。MS27 package / release readiness deferred |

同一IDは再利用しない。production code、test code、GUI、または対象契約が変更された場合、B4は影響行を`stale`とし、新HEADで再実行する。意味を変えない文書補正だけの場合は、runtime evidenceを自動失効させず、非失効の根拠と新HEADを該当行へ追記する。

### 16.1 環境コマンドの既得実測記録

`MS26-B1-001`の2026-09-06実測を以下へ具体化する。2026-09-07の文書補正では再実行していない。各行は独立して実行したコマンドで、Pythonの`-c`内は当時の引数をそのまま記録した。

```powershell
.\.venv\Scripts\python.exe --version
.\.venv\Scripts\python.exe -c "import sys; print(sys.executable)"
.\.venv\Scripts\python.exe -c "import wx, matplotlib, numpy, whisper, pyopenjtalk; print('major imports ok')"
.\FFmpeg\bin\ffmpeg.exe -version
.\FFmpeg\bin\ffprobe.exe -version
```

| 上記順序 | 実測結果 | process exit code |
| --- | --- | --- |
| 1 | `Python 3.14.3` | `0` |
| 2 | `D:\Kanna_Works\MMD_AppWork\MMD_AutoLipTool-dev\MMD_AutoLipTool_Antigravity\.venv\Scripts\python.exe` | `0` |
| 3 | `major imports ok` | `0` |
| 4 | `ffmpeg version N-123549-g70537ec8e6-20260318` | `0` |
| 5 | `ffprobe version N-123549-g70537ec8e6-20260318` | `0` |

上記はversion / importの実測であり、B2の自動回帰やB3のGUI・実MMD検証の結果ではない。

### 16.2 B1実装後チェック（2026-09-07）

- 実行者: Codexメインエージェント。対象はHEAD `e2d63ad`に対する本計画、MS26 Block Breakdown、MS20 Indexの未コミット変更3文書。
- 本計画§12の受入条件を実施記録・evidence ledgerへ照合し、B1 baseline / contract gate通過とB2未着手の区別、STEREO固定、duration検証のB2引き継ぎを確認した。B1成果物は受け入れ可能で、P1 / P2 / P3の残存はない。
- 台帳21行（見出し・区切りを含む）の13列構造と、MS20〜MS25の現行回帰入口12ファイルの実在を確認した。`Get-Content` / `rg`による確認、`git status --short --branch`、`git log --oneline -n 3`、`git diff --numstat HEAD`、`git diff --check`はprocess exit code `0`。証拠所在は本セッションのメイン実装後チェック報告とコマンド出力。
- この実装後チェック自体ではファイル変更、pytest、compileall、GUI / 実MMD操作、stage / commitを行っていない。本節と関連文書への結果反映は、その後のユーザー依頼による文書同期として区別する。
- B2所有のduration差0.05秒以内・比較不能・超過の検証課題、B3素材 / 環境未確定、Python 3.11 / 3.12未検証、B4未実施、MS27 deferredを維持する。旧HEADのtest passとユーザーGUI報告を現行HEADの検証成功へ転用しない。
- 次工程はB2個別Implementation Plan策定・実装前チェックであり、本記録をもってB2の実装・回帰やMS26 Closeoutへ進まない。

### 16.3 B2計画への引き継ぎ判断（2026-09-08）

ユーザーはduration gateについてA（自動回帰の合格条件に限定）を選択した。`MS26-B2-002`の「実装 / test evidence化」はtest-only helperと実変換結果の比較テストを指し、productionの保存時validator・エラー契約・個別保存・一括出力の動作は変更しない。超過・取得不能はテスト側で不合格とする。STEREO固定は維持する。

[MS26-B2個別計画](MS26-B2_Implementation_Plan.md)を作成済み。duration findingはまだopenで、B2実装・自動回帰・実装前チェック通過は未実施。B3用素材はB2計画作成の前提にしない。B1の過去の次工程記録は上記日付の実装後チェック時点として保持する。

### 16.4 B2実装・自動回帰・実測記録（2026-09-09）

- 実装・テスト実行者: サブエージェントCurie、Agent ID `01a08405-19f5-7b11-a814-62570eea666b`。統合レビューと最終文書補正は親メインが担当した。branch `feature/MS26-implementation`、baseline HEAD `ff57305`。B2計画、Block Breakdown、MS20 Index、対象production code / test入口を再照合した。
- `.codex/config.toml` のconfig v2 wait設定は min `300000` / default `600000` / max `1800000` ms。親メインはAPI v1へ`timeout_ms=600000`を明示した。v2設定の自動適用は未確認。サブエージェントCurieの作業中はCurieがシェルを独占し、終了後に親メインが照合した。runtime JSON / INI、依存、lock、build、外部素材、ネットワークは変更・使用していない。
- 追加・補修したのはtest-onlyの3ファイルと指定文書4ファイルだけで、`src/` production code、保存validator、DTO、GUI / worker、error code、個別保存・一括出力は不変である。mainレビュー指摘6件の内容、補修前・中間失敗、補修後結果はB2計画§15.2 / §15.5に記録した。
- 必須回帰の初回値はMS17-B7 `14 passed`、MS25 `160 passed, 2 skipped`、MS19〜MS24 `497 passed`、pipeline/VMD `13 passed`、vmd_writer `98 passed`、full `1064 passed, 4 skipped`。duration初回unitは`22 passed`、実FFmpeg integrationは20/20 cases `1 passed`だった。補修後unit `25 passed`、integration `24/24`、full `1067 passed, 4 skipped`、compileall exit `0`、tracked diff check exit `0`、untracked no-index diff checkは3件とも診断なしの規定exit `1`、SHA-256は固有ID付きでB2計画§15.2 / §15.5へ記録した。
- Full suiteの4 skipは、MS25 Windows path 2件とWhisper model store 2件のsymlink生成におけるWindows `WinError 1314`（作成権限不足）で、既存環境制約である。MS25 B6 collision / cleanup fault gateにはskipがなく、新規B2 duration testにもskipはない。受入影響はsymlink固有経路に限定され、B2必須duration / cross-boundary gateの欠落ではない。
- 実FFmpeg matrixは、WAV mono / stereo / 3ch × 44100 / 48000 Hz × 1.37 / 5.11秒、MP3 mono / stereo、M4A mono / stereoの20通常runner条件に、WAV stereo 48000 Hz 2件とM4A stereo 2件のcancellable runner再測定を加えた24測定caseである。analysis / MMDとも44100 Hz、analysis mono、MMD stereo、全duration差 `0.000000000` 秒だった。全行のframes/rate/duration、locator source/path/versionはMS26-B2 plan §15.3に記録した。
- negative / boundaryは、同長・差2204/2205 samples（0.05秒境界）をpass、差2206 samplesをfailureとして検出し、invalid rate/channel/sample width、missing/unreadable/header破損/empty/truncated/non-PCM、同一path、role逆転、source identity不一致、同一DTO durationによる偽passを検出した。
- `MS26-B2-001`はmain補修後もpassed、`MS26-B2-002`はtest-only範囲でresolved。mainレビュー指摘はP2-1〜P2-3、P3-1〜P3-3としてすべて解消済みで、初回失敗は履歴として保持した。B3 Windows 11 / actual MMD、B4 revalidation / Closeout、MS27 package / release readiness、Python 3.11 / 3.12、実Whisper model解析は未検証またはdeferredのまま維持する。
- §16.2〜§16.3およびB1-005 / B1-007の「B2未着手」は、各日付時点のB1記録として保持する。現在のB2状態は本節のB2-001 / B2-002と2026-09-09の実装後記録を正とする。
