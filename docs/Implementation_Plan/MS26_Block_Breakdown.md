# MS26 Block Breakdown

## 1. 文書情報

- 文書名: `docs/Implementation_Plan/MS26_Block_Breakdown.md`
- 対象マイルストーン: MS26 Final Feature Integration / Actual MMD Closeout
- 作成日: 2026-09-04
- 対象ブランチ: `feature/MS26-implementation`
- 計画作成時HEAD: `c881264 Record MS25-B7 closeout A`
- 計画作成時のGit状態（2026-09-04）: `docs/MMD_Audio_WAV_Compatibility_Specification.md` と `docs/MS20_and_Beyond_Index.md` がmodified、`docs/Implementation_Plan/MS26-B1_Implementation_Plan.md` と本文書が未追跡。stage / commitは未実施
- B1実施時のlive Git状態（2026-09-06）: `feature/MS26-implementation`、HEAD `e2d63ad1d1469f6a74ee09d508c26c1c4b47ba08`、開始時working tree clean、upstream tracking未設定。`c881264..HEAD`はAGENTS / skill・MS26計画・仕様 / Indexなどの文書差分のみで、`src`、`tests`、`pyproject.toml`、`uv.lock`の差分はない。Python `3.14.3`、主要import、リポジトリ内FFmpeg / ffprobeのversion確認はいずれもexit code `0`。
- 状態: **MS26 CloseOut A（2026-09-12）**。B2の自動gate、B3のユーザー報告によるGUI・実MMD受入（実MMD上の音声・モーフ同期を含む）、追加GUI / recovery / Whisper手動gate、生成物一組のread-only確認、B4 targeted revalidation、最終文書監査を完了した。CodexによるGUI / 実MMD操作は未実施で、ユーザー確認として記録する。PMX hashの独立取得不可は補助identityの制限として記録し、未解消P1 / P2 / P3はない。MS27はdeferred
- 前提となる完了状態: MS25 Closeout A
- 本文書の権限: MS26の責務分割、検証順、状態契約、手動受入契約、受入条件を定義する。本文書の作成自体ではproduction code、test code、runtime user data、依存関係、build設定を変更しない
- サブエージェント監査: Newtonへ読み取り専用のBlock Breakdown / B1プラン監査を委任し、P2/P3の指摘と修正結果を回収済み。最終的な採否判断と現行リポジトリとの照合はメインエージェントが担当する

### 1.1 判断の優先順位

MS26の判断は、次の順で行う。

1. live Git、現行production code、現行test、実行commandのprocess exit code、実際のWindows 11 / MMD確認結果
2. 本文書と、MS26-Bx個別Implementation Plan
3. `docs/MS20_and_Beyond_Roadmap.md` §13〜§15
4. `docs/Pipeline_Data_Contract_Specification.md`、`docs/GUI_State_Theme_Specification.md`、`docs/Error_Handling_Specification.md`、`docs/VMD_Output_Specification.md`、`docs/MMD_Audio_WAV_Compatibility_Specification.md`
5. MS20〜MS25のBlock Breakdown / Implementation Plan
6. `README.md`、`readme_mmdautolip.txt`、Index、milestone / version-control履歴

過去の計画に残る「未実装」「未検証」「後続へ延期」は、live Gitまたは新しい検証結果で更新された場合には履歴記録として扱い、現在状態と混同しない。

## 2. 参照した正本文書と現行ベースライン

### 2.1 正本文書

- `docs/MS17_and_Beyond_Index.md`（legacy routingであることを確認するための参照）
- `docs/MS20_and_Beyond_Index.md`
- `docs/MS20_and_Beyond_Roadmap.md` §13〜§15
- `docs/Implementation_Plan/MS24_Block_Breakdown.md`
- `docs/Implementation_Plan/MS24-B7_Implementation_Plan.md`
- `docs/Implementation_Plan/MS25_Block_Breakdown.md`
- `docs/Implementation_Plan/MS25-B7_Implementation_Plan.md`
- `docs/Pipeline_Data_Contract_Specification.md`
- `docs/GUI_State_Theme_Specification.md`
- `docs/Error_Handling_Specification.md`
- `docs/VMD_Output_Specification.md`
- `docs/MMD_Audio_WAV_Compatibility_Specification.md`
- `README.md`
- `readme_mmdautolip.txt`

### 2.2 現行実装の確認対象

#### production code

- `src/core/pipeline.py`
- `src/core/audio_convert.py`
- `src/core/mmd_wav_export.py`
- `src/core/output_diagnostics.py`
- `src/core/diagnostic_report.py`
- `src/core/delivery_package.py`
- `src/core/delivery_artifacts.py`
- `src/gui_wx/app_controller.py`
- `src/gui_wx/main_frame.py`
- `src/gui_wx/right_pane.py`
- `src/gui_wx/ui_state.py`
- `src/gui_wx/audio_worker.py`
- `src/gui_wx/worker_state.py`
- `src/gui_wx/output_diagnostics_adapter.py`
- `src/gui_wx/playback_controller.py`
- `src/gui_wx/playback_context.py`
- `src/gui_wx/preview_panel.py`
- `src/gui_wx/waveform_panel.py`
- `src/vmd_writer/writer.py`
- `src/vmd_writer/validator.py`

#### test code

- `tests/test_pipeline_and_vmd.py`
- `tests/test_pipeline_peak_values.py`
- `tests/test_ms19_b3_textless_pipeline.py`
- `tests/test_ms19_b4_analysis_worker_voice_only.py`
- `tests/test_ms19_b5_transcription_edit_state.py`
- `tests/test_ms20_b5_warning_save_policy.py`
- `tests/test_ms20_b6_diagnostic_report.py`
- `tests/test_ms20_b6_report_save_flow.py`
- `tests/test_ms20_b7_diagnostics_state_integration.py`
- `tests/test_ms21_b5_adjusted_vmd_save.py`
- `tests/test_ms21_b5_effective_output_identity.py`
- `tests/test_ms21_b7_analysis_rollback.py`
- `tests/test_ms21_b7_audio_worker_terminal.py`
- `tests/test_ms21_b7_ui_sync_context.py`
- `tests/test_ms22_b2_long_vowel_adapters.py`
- `tests/test_ms22_b3_generation_presets.py`
- `tests/test_ms22_b4_generation_history.py`
- `tests/test_ms22_b6_lifecycle_regression.py`
- `tests/test_ms23_b2_morph_name_sets.py`
- `tests/test_ms23_b2_morph_name_adapters.py`
- `tests/test_ms23_b4_model_profile_state.py`
- `tests/test_ms23_b5_model_profile_controller.py`
- `tests/test_ms23_b6_model_profile_lifecycle.py`
- `tests/test_ms24_whisper_diagnostics.py`
- `tests/test_ms24_whisper_error_recovery.py`
- `tests/test_ms24_whisper_model_apply.py`
- `tests/test_ms24_no_implicit_download.py`
- `tests/test_ms25_b1_current_state_gate.py`
- `tests/test_ms25_b1_delivery_contract.py`
- `tests/test_ms25_b2_windows_paths.py`
- `tests/test_ms25_b2_delivery_orchestration.py`
- `tests/test_ms25_b2_delivery_commit.py`
- `tests/test_ms25_b3_delivery_artifacts.py`
- `tests/test_ms25_b3_vmd_readback_validation.py`
- `tests/test_ms25_b4_delivery_report_identity.py`
- `tests/test_ms25_b5_delivery_worker.py`
- `tests/test_ms25_b5_delivery_gui.py`
- `tests/test_ms25_b6_windows_collision_faults.py`
- `tests/test_ms25_b6_delivery_failure_recovery.py`
- `tests/test_ms25_b6_delivery_gui_recovery.py`
- `tests/test_ms17_b7_mmd_wav_export.py`
- `tests/test_ms17_b7_mmd_wav_failure_cleanup.py`
- `tests/test_ms17_b7_mmd_wav_save_dialog.py`
- `tests/test_ms17_b7_mmd_wav_overwrite_confirm.py`
- `tests/test_ms17_b7_mmd_wav_button_state.py`
- `tests/test_vmd_writer_intervals.py`
- `tests/test_vmd_writer_grouping.py`
- `tests/test_vmd_writer_multipoint_shape.py`
- `tests/test_vmd_writer_peak_value.py`
- `tests/test_vmd_writer_zero_guard.py`
- `tests/test_wx_ms21_b3_preview_selection.py`
- `tests/test_wx_ms21_b4_selected_event_editor.py`
- `tests/test_wx_ms21_b6_undo_redo.py`
- `tests/test_wx_ms21_b7_state_integration.py`
- `tests/test_wx_ms21_b7_sync_efficiency.py`
- `tests/test_wx_ms22_b5_long_vowel_override.py`
- `tests/test_wx_ms22_b5_preset_ui.py`
- `tests/test_wx_ms22_b6_lifecycle_regression.py`
- `tests/test_wx_ms23_b4_profile_runtime.py`
- `tests/test_wx_ms23_b5_model_profile_ui.py`
- `tests/test_wx_ms24_whisper_model_ui.py`

### 2.3 現行ベースラインの事実

- 現在のMS26実装用ブランチは `feature/MS26-implementation` であり、MS25 Closeout Aを記録した `c881264` から開始している。
- MS25で、現在の有効な編集結果からVMD、元の入力音声からMMD用WAV、同じ開始snapshotから診断レポートを再生成し、専用directoryへtransactionalに確定する導線が実装済みである。
- 個別VMD保存、個別MMD用WAV出力、個別診断レポート保存は一括出力とは別の導線として残っている。一括出力は個別保存済みファイルを流用しない。
- `EffectiveShapePlan`は現在の調整結果を表す出力正本であり、Preview表示やwriterの既存出力を正本として扱わない。PreviewとVMDは同じeffective shape意味を共有する。
- 出力モーフ名は、プロファイル未選択時の日本語セット `あ / い / う / え / お`、またはMS23のLatin組み込みプロファイルによる `A / I / U / E / O` に解決される。任意のユーザー定義モーフ名セットはMS26で追加しない。
- Whisperには selected / active / loaded / analysis identity の区別があり、解析時の暗黙downloadは禁止されている。MS26はこの選択契約を再実装せず、既存の統合結果を確認する。
- MMD用WAVは内部解析WAVと役割が異なる。解析用WAVは内部のmono音声、MMD用WAVはMMD用の16-bit / 44.1kHz / stereo PCM WAVとして扱う。解析用WAVとMMD用WAVのduration差は正文仕様どおり0.05秒以内を許容範囲とする。
- `docs/MMD_Audio_WAV_Compatibility_Specification.md`のMMD用WAV検証項目をchannel count 2（stereo固定）へ同期した。現行`MMD_WAV_SPEC`、validator、正文仕様の主要固定記述、MS25契約が一致しており、mono許容や音声形式変更の根拠にはしない。
- MS25 Closeout Aで、自動テスト、Python 3.14.3開発・受入gate、package静的監査、MS25文書同期は完了している。一方、実MMDでのVMD / WAV読込・再生・リップ同期は未検証としてMS26へ引き継がれている。
- PyInstaller onefile、ZIP、最終artifact、package / release readinessはMS27の責務であり、MS26の受入証拠には含めない。
- 計画作成時点では、実MMDの実行ファイル、受入対象PMX / PMD、実受入用音声、voice_only用の検証済みWhisperモデルを、リポジトリの固定fixtureとして採用したという状態は確認していない。実機確認で使用する素材はMS26-B1で明示的に記録する。

## 3. 背景

MS20〜MS25では、解析、voice_only、Preview、再生、イベント補正、Undo / Redo、プリセット、モデルプロファイル、Whisperモデル管理、診断、個別保存、一括出力が段階的に実装された。個別Blockの自動テストは各責務を確認しているが、MMD利用者が行う最終的な「同じ入力音声・同じVMD・対象モデル」での読み込みと再生、リップ同期は、コード単体の検証からは判定できない。

MS26は新機能を広げる工程ではなく、既存機能の統合状態を一つの基準で確認し、実MMDで確認できた事実と、なお自動生成の補助出力に留まる事項を分離して記録する工程とする。

## 4. 目的

1. MS20〜MS25の確定契約が現行コード、テスト、GUI状態、個別保存、一括出力で一貫していることを確認する。
2. TEXTあり入力と `voice_only` 入力、Preview / writer / diagnostics / report / Warning、プリセット / profile / morph set、Whisper identity、再生を横断回帰する。
3. Windows 11実機上でGUIの主要導線を確認し、実MMDでVMDとMMD用WAVの読み込み・再生・リップ同期を確認する。
4. 不具合や契約不整合が見つかった場合の修正範囲、再検証条件、既存機能の保護条件を固定する。
5. README、配布用readme、正文仕様、Index、Roadmap、milestone / version-control記録を、実施済み・未検証・保留・MS27移管の状態へ同期する。
6. P1 / P2 / P3を解消またはユーザー判断付きで処理し、MS27 release readinessへ進めるかを判定する。

## 5. In Scope

- MS20〜MS25の成果と受入条件のrequirement-to-evidence ledger
- TEXTあり入力の解析、Preview、再生、個別VMD保存、一括出力の横断確認
- `voice_only` 入力のWhisper timing、書き起こし編集・再解析、Preview、VMD / report / 一括出力の横断確認
- プリセット適用、モデルプロファイル適用、resolved morph-name set、長音設定、イベント補正、Undo / Redoの整合確認
- selected / active / loaded / analysis Whisper identity、diagnostics snapshot、Warning / ERROR、保存可否の整合確認
- Preview、waveform、playback context、VMD writer、diagnostic reportの同じ時間軸・同じeffective output意味の確認
- MMD一括出力の親directory、編集可能folder名、既定folder名、3成果物、collision、失敗保護、個別保存との共存確認
- Windows 11上のGUI起動、入力、処理、保存、再生、close / cancel / Busyなどの手動確認
- 実MMDでのVMD import、MMD用WAV import、再生、音声と口パクの同期、対象morphの対応確認
- 既存自動テストの対象回帰、full pytest、compileall、diff whitespace gate
- MS26で実際に見つかった問題の最小修正、修正後の影響回帰、受入証拠の再生成
- README、`readme_mmdautolip.txt`、Pipeline / GUI State / Error Handling / VMD / MMD WAV正文仕様、Index、Roadmap、milestone / version-controlの必要最小限の同期
- Ver.1以降に保留する事項とMS27へ引き継ぐrelease readiness項目の明示

## 6. Out of Scope

- GitHub Release公開、tag作成、remote push、branch削除
- PyInstaller onefile build、SmokeLaunch、ZIP生成、配布artifactの最終作成
- package manifest、LICENSE、NOTICE、THIRD_PARTY_LICENSESを含むrelease readinessの最終監査
- installer新規導入
- `.autolip`等のsession file、MMD project file、MMD本体のdirectory構成管理
- VMD、WAV、reportの新しいファイル形式や命名規則の設計
- 新しいmorph-name set、任意モーフマッピング、phoneme精度保証、MMD側の自動起動
- Whisperモデル選択、download、loader、identity契約の再実装
- cloud ASR、音声外部送信、telemetry、background通信
- Qt / PySide6の復活
- 既存の個別保存導線を一括出力へ置換すること、個別保存済み成果物を一括出力へ流用すること
- runtimeの `presets.json`、`profiles.json`、`MMD_AutoLipTool.ini` の直接読取り、編集、コピー、fixture化、stage
- テスト削除、skip追加、assertion緩和、対象縮小による合格化
- MS26で確認した問題を、根拠なく大規模リファクタリングや依存関係変更で解消すること

## 7. Block分割

### MS26-B1: 統合ベースライン・受入素材・契約gate

#### 責務

- MS25 Closeout Aのcommit、現行branch、working tree、Python実行環境、依存関係を再確認する。
- MS20〜MS25の要求、実装commit、既存test、ユーザー手動確認、未検証事項を、`docs/Implementation_Plan/MS26-B1_Implementation_Plan.md` §16のevidence ledgerへ対応付ける。B1〜B4のID、所有Block、実行HEAD、HEAD変更時の失効条件を同節で固定する。
- 実MMD確認で使用するMMD実行環境、MMD version、Windows 11 build、PMX / PMD model、入力audio、必要なTEXT、profile、preset、Whisper modelのidentityを固定する。未提供項目は推測せず、B3 material / environment gateの未充足項目として記録する。
- MMD側で確認する対象morph名が、選択したprofileのresolved output namesと一致することを事前確認する。
- MMD WAVのchannel count、chunk、sample rate、durationに関する正文仕様と`MMD_WAV_SPEC` / validatorの対応を照合する。durationは解析用WAVとの差0.05秒以内をB2の自動検証契約とし、現行testまたはvalidatorで証明できない場合はB2所有findingとして分類する。
- B2〜B4で採用する必須テスト群、process exit code gate、手動証拠フォーマット、修正後の再実行条件を固定する。

#### 完了条件

- 計画対象の実在ファイルと現行状態を確認し、履歴記述とcurrent stateを分離できている。
- B2開始に必要なbaseline、contract、必須test群、evidence ledgerが固定されている。
- 実機・実MMDの受入素材が固定されているか、未提供項目がB3 material / environment gateの開始条件として明示されている。
- 不足する仕様またはコード境界が、推測ではなくP1 / P2 / P3または未確定事項として記録されている。

#### 禁止事項

- 実MMD結果を、素材未固定のまま「確認済み」と記録しない。
- runtime user dataや外部音声・モデルをリポジトリへコピーしない。
- B1のbaseline確認を理由にproduction codeを変更しない。

#### B1実施記録（2026-09-06）

- B1-01: live branch、HEAD、`origin/main`、working tree、履歴、Python `3.14.3`、主要import、FFmpeg / ffprobeを確認した。開始時working treeはcleanで、`c881264..e2d63ad`のruntime code / test / dependency / lock差分はない。
- B1-02: MS20〜MS25の要求、実装履歴、既存testの所在、ユーザー報告、未検証事項を現行Index、MS25-B7記録、現行code / testへ対応付けた。旧HEADのtest totalsとユーザー報告は歴史証拠として保持し、現行HEADのpassへ転用しない。
- B1-03: input audio、internal analysis WAV、MMD用WAV、EffectiveShapePlan、resolved morph names、selected / active / loaded / analysis Whisper identityの分離を現行実装で確認した。日本語 `あ / い / う / え / お` とLatin `A / I / U / E / O`を別profileとして記録し、B3素材が未提供のため実MMD適用結果は未確定とした。
- B1-04: `MMD_WAV_SPEC`を`pcm_s16le`、44100 Hz、2 channel（STEREO固定）として、validatorおよび正文仕様と照合した。内部解析WAVはmono、`mmd_wav_export`の返却durationはinput probe由来、validatorは解析WAVとMMD用WAVのduration差を比較しないことを記録した。
- B1-05: B2必須testの順序、process exit code、skip理由、修正後HEADでの再検証条件を固定した。duration差`<= 0.05秒`の取得・比較・超過・取得不能はB2所有findingとして残し、B2自動回帰自体は実施していない。
- B1-06: B3のmanual GUIとactual MMDを、GUI、VMD / WAV load、play、morph mapping、timing、visual resultに分離する証拠様式を固定した。今回のCodex GUI / 実MMD操作は未実施で、過去のユーザー報告はMS26実績へ転用しない。
- B1-07: Indexと本計画のcurrent stateを同期し、B1 baseline / contract gate passed、B2未着手、B3 material / environment gate未通過、B4未実施、MS27 deferredを明示した。B1のpassedは自動test成功の宣言ではない。

#### B1実装後チェック（2026-09-07）

メインがB1計画の受入条件、3文書の差分、evidence ledger、関連仕様・コード・テスト入口を照合し、B1成果物を受け入れ可能と判定した。P1 / P2 / P3残存なし。台帳の13列構造、回帰入口12ファイルの実在、`git diff --check`のprocess exit code `0`を確認した。詳細はB1計画§16.2を正とする。

B1実装後チェック（2026-09-07）時点では、B1 baseline / contract gate passed、B2未着手を維持した。duration検証はB2所有課題、未提供素材はB3開始条件であり、同チェックではpytest・GUI・実MMDを実行していない。現在はB2実装・自動回帰を完了したが、B4およびMS27は未実施 / deferredのままとする。

### MS26-B2: 自動横断回帰・状態整合

個別計画: [MS26-B2 Implementation Plan](MS26-B2_Implementation_Plan.md)（2026-09-08作成、2026-09-09実装・自動回帰・実装内の計画 / 契約照合完了）。ユーザー判断Aにより、duration差0.05秒以内はテスト側の実測・合否判定に限定する。個別保存・一括出力へ保存時duration検証や新しい保存拒否条件を追加しない。以下のduration取得不能・超過時のfailureは、自動テストの不合格を指す。

#### 責務

- MS19のTEXT / `voice_only` / transcription edit、MS20のdiagnostics / report / Warning、MS21のeffective output / adjustment / rollback、MS22のpreset / lifecycle、MS23のprofile / morph set、MS24のWhisper identityを、現行HEADで横断回帰する。
- MS17-B7の個別MMD用WAV export / validation / failure cleanup / save dialog / overwrite confirmation / button stateを、個別保存導線の必須回帰として現行HEADで再実行する。
- MS25-B1〜B6のdelivery direct testを再実行し、3成果物の再生成、同一snapshot、source audio identity、VMD read-back、MMD WAV validation、collision、cleanup、cancel、close、late result discardを確認する。
- 解析用WAVとMMD用WAVのduration差が0.05秒以内であることを自動検証し、取得不能、超過、比較対象の取り違えを成功扱いにしない。
- Preview、writer、diagnostics、reportが別々にeffective outputを再計算していないことを、既存testと必要最小限の追加testで確認する。追加testが必要な場合は、変更理由と所有Blockを記録する。
- individual VMD / MMD WAV / report保存が引き続き利用でき、一括出力によって個別保存履歴や既存出力が変更されないことを確認する。
- full pytest、`compileall -q src tests`、`git diff --check`をprocess exit code `0`のgateとして実行する。

#### 完了条件

- 必須testが同一検証HEADでpassし、skipは件数・理由・受入影響を記録している。
- TEXTありと`voice_only`の両方で、入力identity、analysis identity、effective output、saveability、diagnosticsが矛盾しない。
- deliveryの3成果物が現在状態から生成され、個別保存済みファイルの流用がないことをtestまたはコード照合で確認できる。
- 不合格、未検証、環境依存の項目がP1 / P2 / P3または明示的なdeferredとしてledgerに残っている。

#### 修正境界

- B2で不具合が見つかった場合は、最小のproduction / test / GUI修正を行ってよい。ただし新しいcommitまたはworking tree変更後は、修正対象test、影響cross-boundary、full pytest、compileall、diff監査を新HEADに対して再実行する。
- 依存関係、lock file、PyInstaller、runtime user dataはB2の修正対象にしない。

#### B2実装・main統合レビュー補修・自動回帰記録（2026-09-09）

- 実装・検証・main統合レビューはCurie、Agent ID `01a08405-19f5-7b11-a814-62570eea666b`がメインとして実施した。サブエージェントは起動せず、シェルもメインが単独実行した。`config v2`のwait設定はmin `300000` / default `600000` / max `1800000` ms、実行API v1の待機値は`600000` msとして区別し、詳細なcommand IDはB2計画§15.2へ記録した。
- `tests/ms26_wav_duration_helpers.py`、`tests/test_ms26_b2_wav_duration.py`、`tests/test_ms26_b2_wav_duration_integration.py`の3ファイルを追加・補修した。helperは`wave`の実frames/rate/data read-back、RIFF data chunkのblock alignment、SHA-256 source identity、Fractionによる`<= 0.05秒`判定だけを担当し、production保存導線へ接続していない。
- 初回結果はMS17-B7 `14 passed`、MS25 `160 passed, 2 skipped`、MS19〜MS24 `497 passed`、duration unit `22 passed`、実FFmpeg matrix `20/20`、pipeline/VMD `13 passed`、vmd_writer `98 passed`、full suite `1064 passed, 4 skipped`、compileall exit `0`だった。mainレビューではpartial-tail mono/stereo、source replacement、runner matrix、locator/tool identity、executor/wait記録、hash/command/cross-reference/diff evidenceの6指摘をP2/P3へ分類し、補修前24件中2失敗と中間regex失敗を保持した。補修後の固有ID・結果はB2計画§15.2 / §15.5、7対象pathの最終SHA-256は同計画§15.5と最終報告に記録する。
- 補修後の実FFmpeg matrixは20通常runner + 4 cancellable runner = 24測定case。WAV stereo 48000 HzとM4A stereoの両方を通常・cancellableの各経路で確認し、locatorは既存`locate_ffmpeg_tools()`の`repo_local`解決、resolved path、versionを記録した。両出力の実測duration差は全件`0.000000000`秒である。
- `MS26-B2-001` automated cross-boundary regressionと`MS26-B2-002` test-only duration findingはB2範囲で補修後もpassed / resolved。P2/P3のレビュー指摘6件は解消済み。Windows 11 GUI、実MMD load / play / morph / timing / visual、B4 Closeout、MS27 package / release readinessは未実施・deferredのままとする。

### MS26-B3: Windows 11実機・実MMD受入

#### 責務

- Windows 11上で配布前の現行開発環境からGUIを起動し、B3 material / environment gateで固定した入力とprofile / preset / Whisper条件で主要導線を確認する。
- TEXTあり入力について、音声とTEXT読み込み、解析、Preview / waveform / playback、diagnostics、個別保存、一括出力を確認する。
- `voice_only` 入力について、検証済みWhisper modelの選択・適用、書き起こし表示、編集・再解析、Preview、保存可否、report / deliveryを確認する。モデル未配置時に暗黙downloadや外部送信が発生しないことも確認する。
- 生成された一括出力directoryから、VMDとMMD用WAVを対象MMDへ読み込む。VMDが対象モデルの解決済みmorph名を使い、音声がMMDで再生可能で、同じ時間原点から口パクが追従することを確認する。
- 日本語profileとLatin profileの双方を実MMDで確認できる場合は、別々のモデルまたは同等のmorph名を持つ検証対象で確認する。対象素材がない場合は、実施できなかった範囲を未検証として記録し、推測で合格にしない。
- 一括出力のcollision、既存directory保護、個別保存との共存、キャンセル・失敗後の復旧を、GUIで確認可能な範囲で確認する。

#### B3手動GUI確認記録（2026-09-11）

- ユーザーから、手動GUIテスト通過・問題なしとの報告を受領した。これはユーザー報告として記録し、Codex自身のGUI実行結果とは扱わない。
- 実MMDでのVMD / WAV読み込み、再生、morph対応、時間同期、見た目は未確認であり、B3のactual-MMD完了条件は未充足のままとする。

#### 手動テスト追加報告（2026-09-12）

- ユーザーから手動テスト通過・問題なし、AC03 / AC04確認済みとの報告を受領した。Codex自身のGUI / 実MMD操作結果とは扱わない。
- ケース別ログ、artifactのpath・size・SHA-256、GUI / 実MMDの内訳は未提示のため、ユーザー報告として記録し、B3の詳細受入条件と実MMD個別判定は未完了として保持する。

#### B4部分実施記録（2026-09-12）

- メインエージェントがHEAD `fe4c95c`で、B2実装コミット以降にproduction code / test codeの変更がないこと、B3承認素材5件のSHA-256がB3計画の記録と一致することを確認した。MMD画面version、実PMX morph名、実MMD4主要ケースはメイン側では未確認だが、ユーザーからAC03 / AC04をチェックし問題なしとの報告を受領している。個別結果・artifact情報は未提示である。
- Whisper availability worker / runtime / no-download / local-storeのtargeted testは25 passed、2 skipped、exit `0`（skipはsymlink作成権限不足 `WinError 1314`）。controllerは3 passed、UIは4 passed、いずれもexit `0`。B2-R05のdaemon headerは再現せず、原因・影響は未確定で、推測によるコード補修は行っていない。
- B4は確定finding補修・全面再検証・Closeout判定まで到達していない。`MS26-B4-002`の証拠はB1計画§16へ記録し、AC03 / AC04のユーザー報告を保持しつつ、B3ケース別追跡可能性と必要なCloseout条件を未完了として保持する。

#### ユーザー追加確認・生成物対応（2026-09-12）

- ユーザーからMMD `Ver 9.32`、model `D:\Visual Works\MMD Folder\MikuMikuDance64\UserFile\Model\Kanna\Mobco\_V4B\Mobco\_v2\_2024B3\_edit2.pmx`、入力音声 `D:\Visual Works\Kanna Work\Voice\MMD_AutoLipTool説明1.wav`、出力MMD用WAV `D:\Visual Works\Kanna Work\Voice\MMD_AutoLipTool説明1B_MMD\MMD_AutoLipTool説明1_mmd.wav`を受領した。
- ユーザー報告として、日本語・ラテンおよび`B3-T-JP`、`B3-T-LA`、`B3-V-JP`、`B3-V-LA`を確認し、問題なしと記録する。これはユーザー側の実MMD確認であり、CodexのGUI / 実MMD操作結果ではない。
- 生成物directory `D:\Visual Works\Kanna Work\Voice\MMD_AutoLipTool説明1B_MMD`のVMD、MMD用WAV、reportをread-onlyで確認した。当時点では一組のartifact内容のみを独立確認し、4ケースごとのartifact対応、PMX hash / morph一覧、report設定とケースの対応は未確定として記録した。その後のユーザー受入報告は最終受入整理へ反映した。

#### 追加手動gate確認（2026-09-12）

- ユーザーから、GUI再生、voice-only編集・再解析、状態・保存可否、deliveryのcollision・cancel・failure recovery・close、Whisper未配置・no-download、profile / preset適用と復帰をすべて確認し、主な不具合なし・正常作動との報告を受領した。
- `MS26-B3-004`として、ユーザー側の追加手動gateをPass報告として記録する。CodexによるGUI操作は未実施で、詳細操作ログ・画面記録・実施回数は未提示である。
- 4ケースごとのartifact対応もユーザー確認済みとして扱うが、個別path・設定・ログは本会話へ転記されていないため、Codexが確認した一組のartifactを4ケース共通の証拠とは扱わない。

#### 最終受入整理（2026-09-12）

- ユーザーは、MMD Ver 9.32、指定model、入力音声、出力MMD用WAVを用いた実MMD確認で、音声と対象モーフの同期状態が良好であることを確認した。4主要ケース、日本語・ラテン、追加GUI / recovery / Whisper gateの確認結果と合わせ、B3-AC03 / AC04をユーザー実施の受入結果として確定する。
- B4の最終監査では、B1 / B2の自動gate、B3 user evidence、B4 targeted revalidation、MS27のscope boundaryを照合した。B2-R05は再現なし・機能影響未観測の非確定観測として分類し、確定P1 / P2 / P3にはしない。再現なしを無害性の証明とは扱わない。
- PMX hashは本環境から独立取得していないが、ユーザーのmodel pathと実MMD上のmorph同期確認を受入根拠とする。MS26の機能受入を阻害するfindingとは分類しない。
- B4-AC01〜08を充足し、MS26 CloseOut Aを確定する。PyInstaller onefile、SmokeLaunch、配布物、license / package / release readinessはMS27へ移管する。

#### 完了条件

- MMD version、model名、morph名、入力audio、TEXT、profile / preset、Whisper model identity、出力directory、実施日時、実施者、結果が記録されている。
- VMD import、MMD用WAV import、再生、リップ同期について、成功・失敗・部分確認を個別に判定できる。
- 「VMDがバイナリとして生成できた」ことと、「実MMD上で口が動き音声と同期した」ことを別の証拠として扱っている。
- 手動確認を行っていない項目は、ユーザー報告・Codex実行・自動testのどれに該当するかを混同せず、未検証として残す。

#### 禁止事項

- MMDの見た目を、コード上のVMD read-back passだけで合格としない。
- MMDモデルに存在しないmorph名を、入力素材やコードを変更して黙って別名へ置き換えない。
- MMD本体やモデル、音声を自動配布物やリポジトリへ追加しない。

### MS26-B4: finding解消・再検証・文書同期・Closeout

#### 責務

- B1〜B3のevidence ledger、test結果、Windows 11実機結果、実MMD結果を相互照合する。
- P1 / P2 / P3を、最小修正、追加証拠、仕様上の明示判断、またはユーザー判断のいずれかで処理する。未解消のfindingを「許容」とだけ記録しない。
- 修正があった場合は、修正後HEADを基準に対象test、cross-boundary、full pytest、compileall、diff監査を再実行する。手動結果へ影響する修正なら、B3の該当手動確認もやり直す。
- README、`readme_mmdautolip.txt`、Pipeline / GUI State / Error Handling / VMD / MMD WAV正文仕様、Index、Roadmap、milestone / version-controlを実到達状態へ同期する。
- MS26 Closeout A、条件付き継続、または不合格を、P1 / P2 / P3、未検証範囲、MS27境界とともに判定する。

#### 完了条件

- 必須の自動test、Windows 11実機、実MMD確認が、同じ最終到達状態に対応付けられている。
- 実装済み、検証済み、ユーザー報告、未検証、deferred、out of scopeの記述が文書間で一致している。
- P1 / P2 / P3の未解消がなく、MS27へ進める条件と残課題が明示されている。

## 8. 依存順と責務境界

```text
MS26-B1 plan / precheck complete
        |
        v
MS26-B1 baseline / contract gate passed
        |
        v
MS26-B2 automated cross-boundary regression passed
        |
        v
MS26-B3 material / environment gate passed
        |
        v
MS26-B3 Windows 11 / actual MMD acceptance
        |
        v
MS26-B4 finding repair / revalidation / docs / closeout
        |
        v
MS27 package / release readiness
```

- B1はbaseline、contract、証拠形式を固定するが、機能実装を所有しない。B1 plan / precheckの完了とB1 baseline / contract gateの通過を区別する。
- B2はコード・test・GUIの統合不整合を自動検証し、必要時の最小repairを所有する。実MMDの見た目判定は所有しない。
- B3はWindows 11 / MMDの利用者境界を所有する。B3 material / environment gateはB2実行中まで未充足であってよいが、B3のGUI・実MMD操作を開始する前に通過しなければならない。MMD内部のモデル改変やMMDプロジェクト管理は所有しない。
- B4はfindingの解消確認、証拠の再実行、文書のcurrent-state同期、Closeout判定を所有する。
- MS27はpackage / release readinessを所有する。MS26はonefileや配布artifactを合格証拠にしない。

修正commitがB2またはB4で追加された場合、修正前のtest結果や手動結果を修正後HEADへ自動的に転用しない。影響範囲を再評価し、必要な自動・手動gateを新しい到達状態で再実行する。

## 9. 状態・データ・実MMD受入契約

### 9.1 解析と出力の正本

- 入力TEXT、元の音声identity、解析用WAV、選択済みWhisper identity、解析timing plan、generation state、profile resolution、adjustment snapshotを現在状態の構成要素として扱う。
- Preview data、writer input、diagnostics、report、一括出力VMDは、現在のtiming planと`EffectiveShapePlan`から派生する。
- Preview表示、個別VMD保存、一括出力VMD、診断reportが別の編集状態を参照してはならない。
- `analysis_pending_rebuild`、ERROR、input identity不一致、profile resolution failure、Whisper analysis identity不一致、writer input invalidの状態では、VMDとdeliveryを成功扱いにしない。

### 9.2 3つの音声role

| role | 用途 | MS26で確認する境界 |
| --- | --- | --- |
| user input audio | ユーザーが選択した元音声 | source path / size / mtime等のidentityとMMD用WAV生成元 |
| analysis WAV | 内部正規化音声 | Whisper、RMS、waveform、timing plan、Previewの時間軸。MMDへ直接渡さない |
| MMD-use WAV | ユーザー向け出力 | 16-bit / 44.1kHz / stereo PCM、MMD import / playback対象 |

MMD用WAVのdurationは、元音声および解析用WAVと同じ開始位置・長さを基本とする。B2では解析用WAVとMMD用WAVのduration差0.05秒以内を自動gateとして確認する。音量正規化、無音trim、意図しない開始位置変更を追加しない。

### 9.3 VMDとmorph name

- VMDは30fpsのmorph-only outputであり、writerのread-back validatorを通過したことを自動gateとする。
- VMDへ書き込むmorph名は、resolved morph-name setの順序・名前と一致し、対象MMD modelのmorph名と一致する必要がある。
- 日本語profileでは `あ / い / う / え / お`、Latin profileでは `A / I / U / E / O` を使う。意味順を変えず、MMD側にない名前を暗黙に補完しない。
- 口の動きの自然さは自動testの証明範囲外であり、実MMD確認の観察結果としてのみ記録する。

### 9.4 delivery package

- 既定directory名は `<audio_stem>_MMD`。成果物名は `<audio_stem>_lip.vmd`、`<audio_stem>_mmd.wav`、`<audio_stem>_report.txt`。
- 親directoryとfolder名はsession-onlyであり、INIへ保存しない。
- finalと同じ親directory内のowned stagingで3成果物を生成・検証し、全成功時だけ公開する。
- 同名のdirectory、file、symlink、broken symlink、reparse pointはcollisionとし、merge・replace・delete・automatic renameを行わない。GUIは別名の入力を要求する。
- failure / cancel / stale / source audio changed / cleanup failureでは、既存のfinal outputを保護し、terminal resultのprimary statusとcleanup statusを分離して記録する。
- 一括出力は個別保存済み成果物を読み戻さず、現在のeffective output、元音声、同じ開始snapshotから再生成する。

### 9.5 diagnostics / report

- Reportは一括出力開始時の同一snapshotから生成し、preset、model profile、resolved morph-name set、Whisper selected / active / loaded / analysis identityを記録する。
- `ms21-effective-output-v1` fingerprintは出力意味のguardとして維持し、Whisper管理情報やUIのprojection generationを混入させない。
- UI表示用のsafe messageと、診断・handoff用のdetailを混同しない。通常UIや利用者向け説明へraw exception、絶対path、秘密情報を出さない。

### 9.6 evidence ledger

- MS26のevidence ledgerは`docs/Implementation_Plan/MS26-B1_Implementation_Plan.md` §16へ保存し、別ファイルへ分散させない。
- B1はledger schemaとbaseline行、B2は自動回帰行、B3はGUI・実MMD行、B4はfinding解消・再検証・Closeout行を所有する。
- evidence IDは`MS26-B1-*`、`MS26-B2-*`、`MS26-B3-*`、`MS26-B4-*`を使用し、同一IDを再利用しない。
- 各行を実行HEADへ束縛する。production code、test code、GUI、または対象契約の変更後は、B4が影響を受ける行を`stale`とし、新HEADで再実行する。意味を変えない文書補正だけの場合は、非失効の根拠と新HEADをledgerへ追記する。

## 10. 状態遷移と検証gate

```text
baseline fixed
    |
    v
automated regression ---- failure ----> finding / repair / re-run
    |
    v
Windows 11 GUI smoke ---- failure ----> finding / repair / re-run
    |
    v
actual MMD acceptance --- failure ----> finding / material review / repair / re-run
    |
    v
document sync / closeout
```

- baseline固定後にproduction code、test code、GUI、dependency、build設定の変更が入った場合、変更前の合格値を最終証拠へ転用しない。
- 自動testのpass表示だけでは不十分で、process exit code `0`を必須とする。
- skipは件数、理由、対象受入条件への影響を記録する。実MMD確認の代替としてskipを追加しない。
- manual GUIや実MMDの結果は、実施者、環境、素材、操作、期待結果、実結果、再現性、証拠ファイルの所在を記録する。
- 既存の処理Busy、cancel、close、late callback discard、rollback、既存出力保護を壊す変更は、機能が見える場合だけでなく失敗時にも検証する。

## 11. テスト・検証方針

### 11.1 B1 baseline gate

- `git status --short --branch`
- `git branch --show-current`
- `git log --oneline -n 10`
- `git rev-parse HEAD`
- Python executable path / version / process exit code
- 受入素材とMMD / model / Whisper identityの記録

### 11.2 B2 targeted regression

最初に責務別の小さい群を実行し、失敗時は原因を分類してから広い回帰へ進む。

- pipeline / VMD / writer / Preview / effective output
- MS17-B7 individual MMD WAV export / validation / failure cleanup / save dialog / overwrite confirmation / button state
- TEXT / `voice_only` / transcription edit / rollback
- diagnostics / report / Warning / save policy
- preset / model profile / morph set / long vowel / Undo / Redo
- Whisper selection / identity / no implicit download / recovery
- MS25 delivery direct、Windows path / collision / cleanup / terminal / GUI worker
- MMD WAV individual export / validation / failure recovery
- analysis WAV / MMD-use WAV duration差0.05秒以内と、比較不能・超過時のfailure

### 11.3 B2 full gates

```powershell
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe -m compileall -q src tests
git diff --check
```

各commandのpass数、skip数、failure / error、process exit code、実行HEADを記録する。未追跡の計画・文書を検査する場合も、stageせずに対象ファイルのwhitespaceを別途検査し、stageやcommitを検証の前提にしない。

### 11.4 B3 Windows 11 / GUI manual gate

- 起動、TEXT / 音声読み込み、解析、voice_only、transcription apply / re-analysis
- Preview / waveform / playback position / stop / close
- preset / profile / morph set / Whisper model identityの表示と適用
- `voice_only`で検証済みmodelが未配置の場合に、暗黙download、cloud ASR、音声外部送信、background通信が発生しないこと
- Info / Warning / ERROR、VMD saveability、report saveability
- individual VMD / MMD WAV / report保存
- MMD delivery destination、folder名、3成果物、collision、cancel / failure recovery

手動確認はユーザー報告とCodex実行結果を区別する。Codex自身がGUIを起動していない場合、手動確認済みとは記録しない。

### 11.5 B3 actual MMD gate

- MMDで対象modelを読み込む。
- MMD用WAVを読み込み、先頭・中間・終端を再生する。
- VMDを対象modelへmorph motionとして読み込む。
- 口が対象morphにより動くか、音声と大きくずれていないか、VMDのフレーム原点とWAVの再生開始が対応しているかを確認する。
- 入力audioとTEXT、profile / preset、Whisper identity、出力artifactを記録する。
- 「読み込み可能」「再生可能」「morph対応」「時間同期」「見た目の妥当性」を個別に判定する。見た目の完全性や自然さを自動保証として記録しない。

### 11.6 B4 revalidation gate

- 修正なしの場合でもB2/B3の最終結果を最終HEADへ対応付ける。
- production / test / GUI修正後は、修正対象test、影響cross-boundary、full pytest、compileall、diff checkを再実行する。
- output format、morph mapping、音声時間軸、playback、delivery GUIに影響する修正では、該当する実機・実MMD確認をやり直す。
- Closeout前に未解消finding、未検証、deferred、MS27へ移管する項目を一覧化する。

## 12. 受け入れ条件

### 12.1 自動検証

- 必須のMS20〜MS25横断回帰が同一最終HEADでpassする。
- full pytestがpass表示だけでなくprocess exit code `0`で完了する。
- `compileall -q src tests`と`git diff --check`がprocess exit code `0`で完了する。
- skipがある場合は理由と受入影響が記録され、実MMD確認をskipで代替していない。

### 12.2 機能統合

- TEXTありと`voice_only`で、入力、解析、timing、Preview、writer、diagnostics、report、保存可否が同じ契約で連携する。
- profile / preset / morph-name set / Whisper identityが、解析・表示・VMD・report・delivery間で矛盾しない。
- 個別保存導線が維持され、一括出力は3成果物を現在状態から再生成し、既存出力をmerge / replaceしない。
- cancel、failure、stale、close、late result、source audio変更時に既存出力と復旧可能な状態が保護される。

### 12.3 Windows 11 / 実MMD

- Windows 11実機のGUI確認結果が、環境・素材・操作・結果とともに記録されている。
- 実MMDでVMDとMMD用WAVを読み込めること、再生できること、対象morphが対応すること、音声と口パクの時間同期を確認できることが記録されている。
- 日本語・Latinの両方を確認できない場合は、確認できたprofileと未確認profileを明確に分ける。
- 実MMDで確認できなかった項目を「自動testで代替確認済み」と言い換えない。

### 12.4 Closeout

- P1 / P2 / P3が解消済み、またはユーザー判断・根拠・影響・期限付きで明示処理されている。MS26 Closeout Aとする場合、未解消findingを残さない。
- 実装済み、検証済み、ユーザー報告、未検証、deferred、out of scopeが全正本文書で一致する。
- MS27 package / release readinessへ進めるか、進めない場合の具体的な残課題が判定されている。

## 13. リスクと対策

| リスク | 判定方法 | 対策 |
| --- | --- | --- |
| 個別testは通るが機能間でstateがずれる | TEXT / voice_only / profile / Whisper / deliveryの横断結果を比較 | B2のevidence ledgerとcross-boundary回帰を必須化する |
| PreviewとVMDの見え方がずれる | 同じeffective plan、VMD read-back、Preview表示、実MMD結果を比較 | Preview / writerの派生元を`EffectiveShapePlan`に固定し、片方だけの修正を避ける |
| 解析用WAVをMMD用WAVとして扱う | report、WAV spec、出力実体、MMD importを確認 | 3 audio roleを分離し、MMD用WAVのformat / durationを検証する |
| profileのmorph名が対象modelにない | resolved namesとmodel morph一覧を照合 | import前に不一致を記録し、profileやmodelを黙って置換しない |
| 実MMD素材が不足し受入範囲が曖昧になる | B3 material / environment gateでMMD / model / audio / Whisper identityを固定 | 未提供範囲を未検証として明示し、推測でCloseoutしない |
| 修正後に過去の合格値を転用する | commit / working tree / evidence HEADを照合 | 修正後の影響test、full gate、該当手動確認を再実行する |
| GUIのBusy / cancel / close境界が壊れる | 成功、失敗、cancel、close、late callbackを確認 | worker binding、terminal gate、existing output保護を回帰対象にする |
| MMD見た目の問題をコードの成功扱いにする | 「読み込み」「再生」「同期」「見た目」を分離記録 | 自動testとactual MMD evidenceを別gateとして扱う |
| release工程をMS26へ混入する | diff、依存関係、build設定、artifactを監査 | onefile、ZIP、manifest、license、releaseはMS27へ残す |

## 14. 手動確認の証拠フォーマット

MS26-B3では、少なくとも次を一つの記録へ残す。

```text
実施日時:
実施者:
操作:
期待結果:
実結果:
再現性:
OS / Windows build:
MMD version:
MMD executable path:
Model file / model name:
Model morph names used:
Input audio path / format / duration:
TEXT path or voice_only:
Whisper model key / manifest identity / analysis identity:
Applied preset:
Applied model profile / morph-name set:
Delivery output directory:
VMD artifact:
MMD-use WAV artifact:
Report artifact:
GUI result:
VMD import result:
MMD-use WAV import result:
Playback result:
Morph mapping result:
Lip-sync result:
Observed limitations:
Evidence location:
再実施の要否:
```

ユーザーから受領した手動確認は、実施者をユーザーとして記録し、Codex自身が実行した確認とは区別する。スクリーンショットや出力ファイルをリポジトリへ追加する場合は、ユーザーの明示承認と保存先のscope確認を別途必要とする。

## 15. 対象ファイル整理

### 15.1 主変更候補

MS26-B2またはB4で実際のfindingが確認された場合だけ、次を候補とする。計画作成時点で変更を確定しない。

- `src/core/pipeline.py`
- `src/core/audio_convert.py`
- `src/core/mmd_wav_export.py`
- `src/core/output_diagnostics.py`
- `src/core/diagnostic_report.py`
- `src/core/delivery_package.py`
- `src/core/delivery_artifacts.py`
- `src/gui_wx/app_controller.py`
- `src/gui_wx/main_frame.py`
- `src/gui_wx/right_pane.py`
- `src/gui_wx/ui_state.py`
- `src/gui_wx/audio_worker.py`
- `src/gui_wx/worker_state.py`
- `src/vmd_writer/writer.py`
- `src/vmd_writer/validator.py`

### 15.2 test候補

- 既存のMS19〜MS25 direct / cross-boundary test
- `tests/test_pipeline_and_vmd.py`
- `tests/test_ms17_b7_mmd_wav_*.py`
- `tests/test_vmd_writer_*.py`
- 既存wx integration test

不足するテストを追加する場合は、未検証の契約、所有Block、期待するfailure / success、process exit code gateを個別計画へ記載する。テストを弱める変更は認めない。

### 15.3 文書候補

- `docs/Implementation_Plan/MS26_Block_Breakdown.md`
- `docs/Implementation_Plan/MS26-Bx_Implementation_Plan.md`
- `docs/MS20_and_Beyond_Index.md`
- `docs/MS20_and_Beyond_Roadmap.md`
- `docs/Pipeline_Data_Contract_Specification.md`
- `docs/GUI_State_Theme_Specification.md`
- `docs/Error_Handling_Specification.md`
- `docs/VMD_Output_Specification.md`
- `docs/MMD_Audio_WAV_Compatibility_Specification.md`
- `README.md`
- `readme_mmdautolip.txt`
- `docs/repo_milestone.md`
- `docs/Version_Control.md`

既に現行挙動を正しく説明している文書は、意味のない言い換えをしない。「確認した結果、変更不要」も到達状態の証拠として記録できる。

### 15.4 変更禁止対象

- `presets.json`
- `profiles.json`
- `MMD_AutoLipTool.ini`
- ユーザーの実音声、MMD実行ファイル、PMX / PMD、外部Whisper model weights
- PyInstaller spec、build script、dependency lock、license / package artifact。ただしMS27へ移管するfindingの記録は可能

## 16. 文書同期とMS27への引き継ぎ

- READMEは、現行の入力、個別保存、一括出力、MMD用WAV、profile / Whisper、実MMD確認の説明を実測状態に同期する。
- 配布用readmeは、MMD利用者向けの3成果物、音声role、morph名、collision、失敗保護、実MMD確認の説明をREADMEと同じ意味へ同期する。
- 正文仕様は、実装済み契約を変えず、MS26で見つかった相違だけを根拠付きで補正する。
- Index / Roadmap / milestone / version-controlは、MS26の各Block、実行HEAD、test結果、手動結果、未検証、Closeout判定、MS27移管を時系列で記録する。
- MS27へは、MS26で確定した機能基準と、package / release readinessでまだ確認していない事項だけを引き継ぐ。MS26でonefileやZIPの合格を主張しない。

## 17. MS26実装時の共通指示

- 実装前に、対象Blockの個別Implementation Plan、現行code、test、仕様、live Gitを再確認する。
- 実装・修正は、確認済みのfindingまたは承認済み受入条件に限定する。新しい依存関係や外部通信を追加しない。
- MMD利用者向けの成功条件と、自動testで証明できる条件を分ける。
- `EffectiveShapePlan`、diagnostics snapshot、source audio identity、resolved morph names、Whisper identity、delivery fingerprintを同じ開始状態に束縛する。
- 個別保存済みartifactの流用、MMD用WAVと解析用WAVの混同、既存directoryのmerge / replace、暗黙download、session stateの永続化を行わない。
- GUIの長時間処理はUI threadを塞がず、Busy、cancel、close、late callback discard、terminal callbackを維持する。
- runtime user dataを直接編集・コピー・stageせず、必要なテストはtemporary pathとmanaged persistenceを使う。
- テストを削除、skip、弱化して失敗を回避しない。pytestはpass表示とprocess exit codeの両方を記録する。
- stage、commit、merge、push、tag、releaseはユーザーの明示承認なしに行わない。

## 18. 次工程への引き継ぎ

MS26-B1実施後の引き継ぎとして、B1-01〜07の記録と、B2以降の未実施境界を維持する。

1. `feature/MS26-implementation`のlive Git状態、B1実施HEAD `e2d63ad`、MS25 Closeout Aの基準HEAD `c881264`
2. 現行IndexのMS26 routing、本文書リンク、B1 plan §16 evidence ledger
3. B3開始前に使用するWindows 11、MMD、model、audio、TEXT、profile / preset、検証済みWhisper modelの具体的な組み合わせ、または未充足のB3 material / environment gate項目
4. B2の自動test群とskip / process exit codeの記録様式
5. 実MMDで「読み込み」「再生」「morph対応」「時間同期」「見た目」を分離して記録する手動確認表
6. P1 / P2 / P3 findingを修正後HEADへ再対応付ける手順

B1 plan / precheckは、未確定項目をB3開始条件として記録した時点で完了できる。2026-09-06のB1-01〜07では、baseline、evidence ledger、未解決のblocking contract境界、B2〜B4の証拠境界を固定したため、`B1 baseline / contract-gate-passed`へ遷移した。これはB2自動testの成功を意味せず、B2は別工程として未着手のまま維持する。実MMD素材・環境が未確定の場合はB3 material / environment gateを未通過のまま維持し、B3のGUI・実MMD操作とMS26 Closeoutへ進まない。MS27 package / release readinessもdeferredのままとする。

上記はB1実施時点の引き継ぎ記録であり、現在状態を示すものではない。2026-09-12の最終受入整理では、ユーザーの実MMD上の音声・モーフ同期確認を含むB3受入、B4最終監査、MS26 CloseOut Aを確定した。MS27 package / release readinessは引き続きdeferredである。
