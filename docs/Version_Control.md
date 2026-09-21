# Version Control Log

## Entry 2026-09-19 / Session: ms28-b2-implementation-verification

- Date: 2026-09-19
- Scope:
  - MS28-B2の実装結果、自動回帰結果、未検証境界を関連状態文書へ反映
- Changes:
  - `src/core/pipeline.py`の隣接long source境界補修と、同一frame handoff / fail-closed / 非衝突`S=P`の回帰を実装済み状態として記録した。
  - B1 / B2計画、MS20以降Index / Roadmap、repo milestoneへ、実装内容と受け入れ条件の到達状態を反映した。
  - 版数、依存関係、spec / build設定、runtime JSON / INI、配布成果物は変更していない。
- Result:
  - B2 resolver **39 passed**、pipeline / Preview **4 passed**、adapter・spec **9 passed・21 subtests**、全suite **1100 passed、4 skipped、88 subtests**、process exit code `0`を確認した。
  - `git diff --check`はprocess exit code `0`。MS28-B2のcore実装と自動回帰検証を完了・検証済みとする。
  - 実Whisperによるユーザー提供ファイルの再解析、native GUI、実MMD、EXE、buildは未実施・未検証であり、MS27の完了状態とMS28の独立トラック定義は維持する。
- Validation:
  - B2対象テスト、関連adapter・specテスト、全suite、diff checkを実行した。stage、commit、push、merge、tag、releaseは本エントリでは実施していない。

## Entry 2026-09-19 / Session: ms27-complete-ms28-repair-track-definition

- Date: 2026-09-19
- Scope:
  - MS27を完了済みとして扱い、MS28を全体マイルストーン系列から切り離した修正実装トラックとしてrouting文書へ定義
- Changes:
  - `docs/MS20_and_Beyond_Index.md`、`docs/MS20_and_Beyond_Roadmap.md`、`docs/repo_milestone.md`を、MS27完了・MS28独立修正実装の状態へ同期した。
  - `docs/Implementation_Plan/MS28-B1_Implementation_Plan.md`へMS28の独立トラック位置づけを追記した。
  - 既存のMS27 package/readiness検証履歴は削除せず、追加のリリースパッケージ整備、公開操作、tag、push、mergeをMS27完了条件から分離した。
- Result:
  - MS27はVer.1.0実装到達状態をもって完了済みとする。
  - MS28は、報告済み不具合の原因確認・限定修正・回帰検証を主目的とする独立マイルストーンであり、MS20〜MS27の依存系列には含めない。
  - MS28-B1は計画済み、production code / test code実装は未着手である。
- Validation:
  - 状態文書の差分確認のみ。テスト、build、compileall、GUI、実MMD、push、merge、tag、releaseは実施していない。本エントリのlocal commitは今回の明示依頼で行う。

## Entry 2026-09-18 / Session: ms27-closeout-confirmation

- Date: 2026-09-18
- Scope:
  - ユーザーによるMS27 CloseOut確定を、B6のG-READY Passと未実施の公開操作を区別して状態文書へ同期
- Changes:
  - README、MS20 Index / Roadmap、MS27 Block Breakdown、MS27-B6 plan、Release Package Manifest、repo milestoneをCloseOut確定へ同期した。
  - 候補#08のEXE / ZIP、配布用readme、LICENSE、NOTICE、候補採用版の`THIRD_PARTY_LICENSES.md`、production code、test code、build設定、runtime JSON / INIは変更していない。
- Result:
  - B1〜B6および候補#08の既存証跡を前提として、ユーザーがMS27 CloseOutを確定した。Python 3.11 / 3.12のsource / build互換性は未検証の別support policyとして残り、FFmpegの規約適合はユーザー判断であってCodexの法的保証ではない。
  - GitHub Release、tag、push、merge、公開用source archive生成は未実施の別工程である。
- Validation:
  - 今回は状態文書同期であり、build、テスト、compileall、ZIP再生成、GUI / 実MMD、ネットワークは実施していない。

## Entry 2026-09-18 / Session: ms27-b6-readiness-audit

- Date: 2026-09-18
- Scope:
  - MS27-B6の候補identity、継承証跡、配布文書影響、release readinessのread-only監査と状態文書同期
- Changes:
  - B6開始時の`feature/MS27-implementation`、`840fa8b`、clean treeを記録し、候補#08 EXE / ZIP、B5 static / final verification、ZIP構成を照合した。EXE SHA-256は`AF3B8FD65E3A518F5960EB4D697BE81AA773A1DAE312703552902D97D4CE4223`、ZIP SHA-256は`D963D5F619D48C59B2287992BF6AB350B23AA8DE240686477EA59093F9DB9086`、ZIPは157 filesである。
  - 候補sourceの`MMD_AutoLipTool.spec`は現HEADと同一bytesである。候補embedded版の`THIRD_PARTY_LICENSES.md`と現HEADとの差分は、B5後の状態記録だけであり、候補bytesへ遡及させない。current版を配布に採用する場合はB4/B5の再実施が必要である。
  - Index、Roadmap、MS27 Block Breakdown、B6計画、milestone、Release Package Manifest、READMEをB6 Passへ同期した。配布用readme、LICENSE、NOTICE、候補採用版の`THIRD_PARTY_LICENSES.md`は変更していない。
- Result:
  - Python 3.11 / 3.12のsource / build互換性は未検証だが、ユーザー決定によりWindows onefile公開判定から外した。`origin/main`は`2151d7b`を指し、FFmpeg 10 entriesと通知文書を追跡し、候補branchの`FFmpeg/bin`に差分がないことを確認した。ユーザーはGitHub上の既存公開を規約上問題なしと判断しており、Codexは法的適合を独自に保証しない。
  - 以上により、B6監査報告はPass、MS27 release readinessはG-READY Passとする。exact provider archive identityは既存B3方針の非阻害provenance limitationとして維持する。
  - B5 G-PACKAGE PassとMS26 CloseOut Aを取り消していない。B6監査時点ではMS27 CloseOut、GitHub Release、tag、push、merge、公開用source archive生成は未実施だった。後続のユーザー明示決定によりMS27 CloseOutは確定し、公開操作は未実施のままである。
  - Tests、compileall、build、ZIP再生成、GUI / 実MMD、ネットワーク、stage、commit、push、merge、tag、releaseは実施していない。

## Entry 2026-09-16 / Session: ms27-b5-package-verification

- Date: 2026-09-16
- Scope:
  - MS27-B5候補#08のZIP組立・展開・配布実行、runtime除外補修、G-PACKAGE判定と状態文書同期
- Changes:
  - `MMD_AutoLipTool.spec`の過剰なtest名ベースの除外を限定補修し、NumPy / Jinja2 / Torch / SymPyのruntime importを保持した。PySide6、Matplotlib、pytest / _pytest等の不要component除外は維持した。
  - `tests/test_ms27_runtime_exclusions.py`を追加し、specの除外がNumPy、Whisper、Jinja2、SymPy、Torch Dynamoのruntime importを阻害しないことを検証した。catalog testの旧`torch.testing`除外期待値を更新した。
  - `THIRD_PARTY_LICENSES.md`へ候補別の凍結runtime / 外側license tree対応を追記し、B5計画へ候補#08の静的・GUI・process・handoff証拠を記録した。
- Validation:
  - 対象回帰: `8 passed, 21 subtests passed`、process exit code `0`。
  - 候補#08 EXE: 425824202 bytes、SHA-256 `AF3B8FD65E3A518F5960EB4D697BE81AA773A1DAE312703552902D97D4CE4223`、FileVersion / ProductVersion `1.0.0`。
  - ZIP: 423274681 bytes、SHA-256 `D963D5F619D48C59B2287992BF6AB350B23AA8DE240686477EA59093F9DB9086`。157 filesの組立・展開・実行先hash一致、必須5ファイルとlicense tree、不要data非同梱を確認した。
  - Codexはrepo外cwd、Windows標準PATHのみ、Python環境変数なしで、音声3形式、モデル未配置時の安全な停止、既存smallモデルでの両解析mode、Preview、VMD保存、通常終了・再起動・残留なしを確認した。スプラッシュ`Ver. 1.0.0`はユーザー目視確認として記録する。実MMDはB5で操作していない。
- Result:
  - MS27-B5 G-PACKAGE Pass。B6のrelease readiness、Python 3.11 / 3.12、FFmpeg exact archive provenance・公開時の対応ソース提供方式、GitHub公開は未実施または未確認である。
  - GitHubへのpush、merge、tag、releaseは実施していない。stage / commitは別途明示許可のGit操作として扱う。

## Entry 2026-09-14 / Session: ms27-b4-artifact-revalidation

- Date: 2026-09-14
- Scope:
  - MS27-B4残存finding解消、fix-03 onefile build / SmokeLaunch / archive監査、ユーザー手動確認・実MMD確認の文書同期
- Changes:
  - `MMD_AutoLipTool.spec`へmatplotlib、旧Qt、Torch test/TensorBoard、Numba TBB任意backendの除外を追加した。
  - `build_hooks/hook-torch.py`を追加し、Torch標準hookの`collect_submodules("torch")`による過剰収集を置換した。Torch data/native libraryは維持した。
  - `tests/test_whisper_model_catalog.py`へcustom hookと除外設定の静的契約を追加した。
  - B4計画、MS27 Block Breakdown、MS20 Index / Roadmap、milestone、配布・license関連文書をfix-03到達状態へ同期した。
- Validation:
  - 対象test: `7 passed`、process exit code `0`。
  - 隔離onefile build / SmokeLaunch: process exit code `0`。
  - fix-03候補: 425758214 bytes、SHA-256 `B211FA3312568C0E9067297157C63CEDA742BBFF67C5A84E62D2E1219F05965C`、FileVersion / ProductVersion `1.0.0`。
  - archive監査でmatplotlib package/data、sample_data、旧Qt、Torch test/TensorBoard、Numba TBB任意backendは0件。Whisper / Torch / Numba主要moduleは存在。
  - ユーザーから手動確認通過・実MMD問題なしの報告を受領した。Codex自身のGUI / 実MMD操作結果とは扱わない。
- Result:
  - MS27-B4 G-ARTIFACT Pass。B5 ZIP / 配布環境確認、B6 release readiness、GitHub公開は未実施。
  - 文書同期を含む変更は未stage・未commitである。No push, merge, tag, or release was performed。

## Entry 2026-09-12 / Session: ms26-closeout-a

- Date: 2026-09-12
- Scope:
  - MS26-B1〜B4最終証拠照合、ユーザー実MMD受入、MS26 Closeout A判定、MS27移管の文書同期
- Changes:
  - B1 / B2の既存自動検証記録、B4 targeted revalidation、B3のユーザー報告によるGUI・実MMD受入、追加GUI / recovery / Whisper gateを最終台帳へ対応付けた。
  - ユーザー確認として、MMD Ver 9.32、指定model、入力 / 出力音声、日本語・ラテン、4主要ケース、実MMD上の音声・モーフ同期良好を記録した。Codex自身のGUI / 実MMD操作とは扱わない。
  - 生成artifact一組のread-only確認、PMX hashの独立取得不可、B2-R05の非確定観測、MS27のpackage / release readiness移管を関連文書へ同期した。
  - `MS26-B4-003`を追加し、B4-AC01〜08の最終照合とMS26 Closeout Aを記録した。
- Validation:
  - 既存記録を再利用: B2 unit `25 passed`、実FFmpeg `24/24`、full pytest `1067 passed, 4 skipped`、B4 targeted `25 passed, 2 skipped`、controller `3 passed`、Whisper UI `4 passed`。各process exit codeは`0`。
  - 最終文書差分の`git diff --check`はprocess exit code `0`を確認した。
  - 実MMD確認はユーザー報告として記録し、CodexはGUI / 実MMD操作を行っていない。
- Result:
  - MS26 Closeout A。未解消P1 / P2 / P3なし。B2-R05は原因未確定・影響未観測の非確定観測として保持する。
  - PyInstaller onefile、SmokeLaunch、配布物、license / package / release readinessはMS27へdeferred。
  - production code、test code、GUI、runtime JSON / INI、依存関係、build設定、外部素材は変更していない。stage、commit、push、merge、tag、releaseは未実施である。

## Entry 2026-09-04 / Session: ms25-b7-regression-closeout

- Date: 2026-09-04
- Scope:
  - MS25-B7 full regression、cross-boundary回帰、文書同期、MS25 Closeout A判定
- Changes:
  - B7検証HEAD `0b25c5c Document MS25-B7 implementation plan`に対して、B6 required fault / recovery、MS25 aggregate、4群のcross-boundary、全pytest、compileallを実行した結果をB7 planへ記録した。
  - README、`readme_mmdautolip.txt`、Pipeline / GUI State / Error Handling / VMD Output正文仕様を照合し、現行挙動と一致しているため追加変更しなかった。
  - MS25-B7 plan、Block Breakdown、Index、Roadmap、milestone、Version Controlへ、実測値、skip理由、手動GUI証拠、P1 / P2 / P3判定、MS26 / MS27境界を同期した。
- Validation:
  - B6 required gate: `26 passed`、process exit code `0`。required actual Windows caseはskipなし。
  - MS25-B1〜B6 aggregate: `160 passed, 2 skipped`、process exit code `0`。
  - Cross-boundary: `60 passed`、`200 passed`、`21 passed`、`41 passed`。合計`322 passed`、各process exit code `0`。
  - Full pytest: `1041 passed, 4 skipped`、process exit code `0`。4 skipはWindows symlink作成権限不足（WinError 1314）による環境依存skip。
  - `compileall -q src tests`、`git diff --check`: process exit code `0`。
  - B5 / B6の手動GUI確認はユーザー報告として範囲限定で再利用し、B7でfresh GUIは実施していない。
- Result:
  - 新たなP1 / P2 / P3はなく、MS25 Closeout Aと判定した。
  - 実MMD確認はMS26、Python 3.11 / 3.12は未検証、PyInstaller onefile / ZIP / package / release readinessはMS27へdeferredとした。
  - B7文書変更は未stage・未commitである。No push, merge, tag, or release was performed。

## Entry 2026-09-03 / Session: ms25-b5-implementation-gui-verification

- Date: 2026-09-03
- Scope:
  - MS25-B5 GUI・worker・状態統合、false `delivery_busy` P3修正、関連文書同期
- Changes:
  - 一括出力menu、destination dialog、delivery専用worker、Busy / cancel / close lifecycle、pre-commit UI bridgeを実装した。
  - generic worker stateとworker referenceの不整合によるfalse `delivery_busy`を修正し、既存の個別保存導線を維持した。
  - B5実装状態、利用者向け導線、GUI / pipeline / error / VMDの出力境界を関連文書へ同期した。
- Validation:
  - B5および関連worker / GUI回帰: `29 passed`、process exit code `0`。
  - Full pytest: `1015 passed, 4 skipped`、process exit code `0`。
  - `compileall -q src tests`、`git diff --check`: process exit code `0`。
  - ユーザーから提示したB5手動GUIテスト通過の報告を受領した。これはユーザー確認として記録し、Codex自身のGUI実行結果とは扱わない。
- Result:
  - MS25-B5は実装・自動検証・ユーザー手動GUI確認まで完了した。変更は未stage・未commitである。
  - B6 fault matrix、B7 full cross-boundary regression / closeout、実MMD確認、Python 3.11 / 3.12、MS27 package / release readinessは未完了または未検証である。
  - No push, merge, tag, or release was performed.

## Entry 2026-08-28 / Session: ms24-closeout-a

- Date: 2026-08-28
- Scope:
  - MS24 Closeout A review and P3 documentation correction
- Changes:
  - Corrected `B7-F-002` from `P3` to `P3（解消）` and recorded the finding as resolved.
  - Synchronized the B7 plan, B6 plan status, Block Breakdown, Index, Roadmap, and milestone record with the MS24 Closeout A result.
- Evidence reviewed:
  - MS24 direct regression: `76 passed, 2 skipped`, process exit code `0`.
  - Cross-boundary regression: `163 passed`, process exit code `0`.
  - Full pytest: `881 passed, 2 skipped`, process exit code `0`.
  - `compileall -q src tests`, `git diff --check`, Python 3.14.3 gate, and package static audit passed.
  - B3〜B6 user-reported manual GUI checks passed; B7 made no GUI behavior changes.
- Result:
  - P1 / P2なし、B7-F-001 / B7-F-002解消済み。MS24 Closeout Aを合格と判定した。
  - Actual MMD verification remains MS26 scope. Onefile / ZIP / PySide6 final artifact and package / release readiness remain MS27 scope.

## Entry 2026-08-28 / Session: ms24-b7-integration-regression-static-audit

- Date: 2026-08-28
- Scope:
  - MS24-B7 integration regression, static package audit, and documentation synchronization
- Changes:
  - Updated the B7 plan with current-head regression results, manifest metadata evidence, package-data audit results, user GUI evidence reuse, and the finding ledger.
  - Synchronized README, `readme_mmdautolip.txt`, `docs/Release_Package_Manifest.md`, and `THIRD_PARTY_LICENSES.md` with the explicit `Download & Verify` model-switching flow, exact size / SHA256 verification, external model-weight boundary, and no implicit analysis download / external audio transfer contract.
  - Synchronized the MS24 Index, Roadmap, Block Breakdown, B6 plan, and milestone record with the B7 partial completion state.
  - Recorded the user decision to treat Python 3.14.3 as the sufficient development / acceptance environment and to remove the Python 3.13.x mandatory gate; the `requires-python >=3.11` metadata floor remains unchanged.
- Validation:
  - MS24 direct regression: `76 passed, 2 skipped`, process exit code `0`.
  - MS23 direct, MS19 voice-only, MS20 diagnostics, MS21 rollback / pipeline, pipeline / VMD, and MS17 MMD-use WAV regression: `163 passed`, process exit code `0`.
  - Full pytest: `881 passed, 2 skipped`, process exit code `0`.
  - `compileall -q src tests` and `git diff --check`: process exit code `0`.
  - `collect_data_files("whisper")` returned four Whisper package assets and no model weights; tracked-file search found no `*.pt`, `*.bin`, `*.part`, or `models/` entries.
  - Python 3.14.3 was verified as the development / acceptance environment. Python 3.13.x is not a required gate under the revised project policy.
- Result:
  - MS24-B7 integration regression, static package audit, and the Python 3.14.3 development / acceptance gate are complete; MS24 Closeout has not yet been declared.
  - No production code, test code, GUI behavior, dependency, or runtime user data was changed. No push, merge, tag, or release was performed.

## Entry 2026-08-28 / Session: ms24-b7-plan-p2-p3-correction

- Date: 2026-08-28
- Scope:
  - MS24-B7 Implementation Plan and related routing-document correction only
- Changes:
  - Added explicit MS23-B2 through B6 direct regression targets, retained timing targets, and pipeline / VMD / MMD-use WAV regression targets to the B7 plan.
  - Synchronized the B6 committed state (`1f1aff2`) and B7 plan-created / execution-pending state across the Index, Roadmap, Block Breakdown, B6 plan, and milestone record.
  - Clarified the `VerifiedWhisperCheckpoint` DTO, loader-owned same-open-handle revalidation, verified-bytes binding, and the distinction between the `requires-python >=3.11` metadata floor and the Python 3.13.x acceptance gate.
- Validation:
  - Document-only inspection and whitespace validation were performed; no production code, test code, GUI, dependency, or runtime user data was changed.
  - Python 3.13.x compatibility, `collect_data_files("whisper")` static audit, B7 cross-boundary regression, and B7 Closeout remain unverified.
- Result:
  - B7 Implementation Plan is created and corrected; B7 execution and Closeout are not started.
  - No push, merge, tag, or release was performed.

## Entry 2026-08-26 / Session: ms24-b6-implementation-gui-verification

- Date: 2026-08-26
- Scope:
  - MS24-B6 production implementation, automated verification, user-reported manual GUI verification
- Changes:
  - Added `WhisperDiagnosticsSummary`, selected / active / loaded / analysis identity separation, package version / gate status, safe-failure classification, projection generation, same-snapshot Info / report / RightPane projection, and model-aware rollback diagnostics integration.
  - Preserved MS23 fixed morph / Latin profile / preset / diagnostics / fingerprint contracts, no implicit analysis download, dependency values, and runtime user-data boundaries.
- Validation:
  - Full pytest: `881 passed, 2 skipped`, process exit code `0`.
  - `compileall -q src tests` and `git diff --check`: process exit code `0`.
  - User reported that the presented MS24-B6 manual GUI checks passed without issue. This is recorded as user verification, not Codex-run GUI verification.
  - Python 3.13.x compatibility, actual-MMD verification, and MS27 package / release readiness remain unverified or deferred.
- Result:
  - MS24-B6 is committed as `1f1aff2 Implement MS24-B6 diagnostics and recovery`; B6 stage / commit is complete.
  - No push, merge, tag, or release was performed. Next work is the MS24-B7 Implementation Plan / execution boundary.

## Entry 2026-08-25 / Session: ms24-b5-implementation-gui-verification

- Date: 2026-08-25
- Scope:
  - MS24-B5 production implementation, automated verification, user-reported manual GUI verification
- Changes:
  - Added verified-local model request and single-active runtime ownership with lease, explicit unload, device cleanup, and shutdown guard.
  - Connected Apply / candidate commit-reject, TEXT + audio / voice-only propagation, model-aware rollback, B5 production ownership permit, Delete, storage-root change, and retained-timing invalidation.
  - Preserved `openai-whisper==20250625`, no implicit analysis download, word / segment fallback, and MS23 fixed morph / Latin profile / preset / diagnostics / fingerprint contracts.
- Validation:
  - Full pytest: `872 passed, 2 skipped`, process exit code `0`.
  - `compileall -q src` and `git diff --check`: process exit code `0`.
  - User reported the presented MS24-B5 manual GUI checks passed without issue. This is recorded as user verification, not Codex-run GUI verification.
  - Python 3.13.x compatibility, actual-MMD verification, and MS27 package / release readiness remain unverified or deferred.
- Result:
  - MS24-B5 is implemented and verified on the working tree; no stage, commit, push, merge, tag, or release was performed.
  - Next work is the Python 3.13.x compatibility gate and MS24-B6 Implementation Plan.

## Entry 2026-08-24 / Session: ms24-b4-implementation-gui-verification

- Date: 2026-08-24
- Scope:
  - MS24-B4 production implementation, B4 automated verification, user-reported manual GUI verification
- Changes:
  - Added official-manifest-only downloader, exact-size / Content-Length / redirect / stream failure / cancel / cleanup handling, and a dedicated model management worker.
  - Connected Whisper management UI for Download & Verify, Cancel, Delete, storage-root change, progress/status, managed settings merge, and reusable availability rescan.
  - Preserved B5 ownership-permit boundary; provider-unavailable Delete remains blocked, and B4 does not change active / loaded / analysis identity.
- Validation:
  - Full pytest: `860 passed, 2 skipped, 77 subtests passed`, process exit code `0`.
  - `compileall src tests` and `git diff --check`: process exit code `0`.
  - User reported the presented MS24-B4 manual GUI checks passed without issue. This is recorded as user verification, not Codex-run GUI verification.
  - Python 3.13.x compatibility, B5 production Delete, actual-MMD verification, and MS27 package / release readiness remain unverified or deferred.
- Result:
  - MS24-B4 is implemented and verified on the working tree; no stage, commit, push, merge, tag, or release was performed.
  - Next work is the Python 3.13.x compatibility gate and MS24-B5 planning.

## Entry 2026-08-23 / Session: ms24-b4-plan-settings-theme-p3-repair

- Date: 2026-08-23
- Scope:
  - MS24-B4 Implementation Plan再チェックで確認したP2/P3の補正
- Changes:
  - `SettingsStore` managed persistenceとruntime INIの直接編集禁止の境界を明記し、`system` / `light` / `dark` theme round-trip、全設定merge、`whisper_models_dir`単独置換の回帰をB4対象へ追加した。
  - promote成功後の全体availability projectionをcontrollerの再利用可能な`start_whisper_availability_rescan()`へ一本化した。
  - Python 3.13.xの実行ファイルpath・version・process exit code記録をcompatibility gateへ追加した。
  - Index、Roadmap、repo milestone、Block Breakdownを補正後のB4 plan状態へ同期した。
- Validation:
  - 計画・関連文書の構造確認、既存MS24 B2/B3回帰、`git diff --check`を実施し、B2/B3回帰は`20 passed, 2 skipped, 5 subtests passed`、MS24-B3 wx回帰は`4 passed`、diff checkは成功した。Python 3.13.x、実ネットワーク、実モデル、GUI確認は未実施。
- Result:
  - P2 / P3は計画文書上で補正済み。次工程はMS24-B4 planのfresh read-only pre-implementation check。
  - production code、test code、GUI、依存関係、runtime user data、stage、commit、push、merge、tag、releaseは未実施。

## Entry 2026-08-23 / Session: ms24-b4-plan-p2-p3-repair

- Date: 2026-08-23
- Scope:
  - MS24-B4 Implementation Planの再チェック指摘（P2/P3）補正
- Changes:
  - 保存先変更を現在の全設定保持付きmerge保存へ固定し、`whisper_models_dir`だけのpartial saveによる既存設定上書きを禁止した。
  - B2内部の対象model verification scanとcontrollerの再利用可能な`start_whisper_availability_rescan()`による全体projectionを分離した。
  - Index、Roadmap、repo milestone、B3 plan、Block BreakdownのB3コミット済み・B4 plan作成済み状態を同期した。
- Validation:
  - 計画・関連文書の構造確認と`git diff --check`を実施し、成功した。pytest、compileall、GUI確認は未実施。
- Result:
  - P2 / P3は文書上で解消済み。次工程はMS24-B4 planのfresh read-only pre-implementation check。
  - production code、test code、GUI、依存関係、runtime user data、stage、commit、push、merge、tag、releaseは未実施。

## Entry 2026-08-23 / Session: ms24-b3-implementation-gui-verification

- Date: 2026-08-23
- Scope:
  - MS24-B3 設定・UiState・Whisperモデル選択UIの実装、自動検証、ユーザー手動GUI確認
- Changes:
  - `SettingsStore`のselected / active identity、`UiState`のWhisper selection state、RightPane専用Whisperモデルtab、startup projection、local-only availability scan worker、Busy / stale / shutdown guardを実装した。
  - B2の`failure_code` / `message`をB3のsafe user noticeとdiagnostic detailへ分離した。
  - B3計画書、MS24 Block Breakdown、MS20 and Beyond Index、Roadmap、repo milestoneを実到達状態へ同期した。
- Validation:
  - B3追加・関連の限定検証、full suite `846 passed, 2 skipped`、`compileall src tests`、`git diff --check`はprocess exit code `0`。
  - ユーザーから計画指定範囲の手動GUI確認完了・問題なしの報告を受領した。Codex自身のGUI実行ではない。
  - 実network、実model、実Whisper解析、actual-MMD確認は実施していない。
- Result:
  - MS24-B3はworking tree上で実装・自動検証・ユーザー手動GUI確認まで完了。次工程はMS24-B4 Implementation Plan策定。
  - stage、commit、push、merge、tag、releaseは未実施。

## Entry 2026-08-20 / Session: ms23-b7-closeout-execution

- Date: 2026-08-20
- Scope:
  - MS23-B7 Closeout監査、B1〜B6 / B4B証拠台帳、MS24 / MS26 handoff
- Changes:
  - B7 Implementation Plan、MS23 Block Breakdown、MS20 and Beyond Index、Roadmap、repo milestoneをMS23 Closeout Aへ同期した。
  - historical B4 wx teardown P2とB4Bによる解消chain、current revalidation、ユーザーGUI報告の主体・範囲を記録した。
  - production code、test code、GUI、runtime user data、dependency、package / build / license設定は変更していない。
- Validation:
  - MS23 direct -> 82 passed、31 subtests passed / exit code 0
  - MS21 / MS22関連 -> 90 passed / exit code 0
  - diagnostics / report / Preview / writer / VMD -> 174 passed / exit code 0
  - MS17 / MS19 / MS20 lifecycle -> 54 passed、7 subtests passed / exit code 0
  - wx aggregate -> 136 passed、661 deselectedを2回 / 各exit code 0
  - full suite -> 797 passed、57 subtests passedを2回 / 各exit code 0
  - `compileall src tests`、`git diff --check` -> exit code 0
  - runtime user data 3 pathはGit追跡対象外・root限定ignore。package / dependency / license / network / Qt境界に差分なし。
  - B2 / B5 / B6のユーザーGUI確認報告を範囲限定で再利用。Codexによる手動GUI実行とactual-MMD確認は行っていない。
- Result:
  - P1 / P2 / P3なし。MS23-B7 CloseoutはA。
  - 実MMDでのVMD / WAV読み込み・リップ同期はMS26へ引き継ぐ。次工程はMS24 Implementation Plan策定。
  - stage、commit、push、merge、tag、release、branch削除は未実施。

## Entry 2026-08-12 / Session: ms22-b7-closeout-execution

- Date: 2026-08-12
- Scope:
  - MS22-B7 Closeout監査、B1〜B6証拠台帳、MS23 handoff
- Changes:
  - B7 plan §15.2、MS22 Block Breakdown、MS20 and Beyond Index、Roadmap、repo milestoneをMS22 Closeout Aへ同期した。
  - runtime user data、dependency / package / build / license境界と、B4 / B5 / B6ユーザーGUI報告の扱いを記録した。
  - production code、test code、GUI、dependency、build / package / license設定は変更していない。
- Validation:
  - MS22 direct regression -> 93 passed / exit code 0
  - text / pipeline / Preview / writer / settings回帰 -> 185 passed / exit code 0
  - MS21 effective output / history / lifecycle回帰 -> 138 passed / exit code 0
  - MS17 / MS19 / MS20 input / diagnostics / save回帰 -> 158 passed / exit code 0
  - B4 / B5 / splash組合せ -> 18 passed / exit code 0
  - `pytest tests` -> 713 passed / exit code 0
  - `compileall src tests`、`git diff --check` -> exit code 0
  - B4 / B5 / B6のユーザー手動GUI確認報告を範囲限定で再利用。Codexによる手動GUI実行ではない。
- Result:
  - P1 / P2 / P3なし。MS22-B7 CloseoutはA。
  - `presets.json` / `MMD_AutoLipTool.ini`はGit追跡対象外・root限定ignore、local `presets.json`保持を確認した。
  - 実MMDでのVMD / WAV読み込み・リップ同期はMS26へ引き継ぐ。次工程はMS23 Implementation Plan策定。
  - MS23実装、merge、push、tag、release、branch削除は未実施。

## Entry 2026-07-31 / Session: ms21-b8-closeout-execution

- Date: 2026-07-31
- Scope:
  - MS21-B8 Closeout監査、B1〜B7証拠台帳、MS22 handoff
- Changes:
  - B8計画へB1〜B7の実装commit、test、ユーザー確認範囲、文書同期、findingを記録した。
  - MS21 Block Breakdown、MS20 and Beyond Index、repo milestoneをCloseout Aへ同期した。
  - production code、test code、GUI挙動、dependency、build / package / license設定は変更していない。
- Validation:
  - B7専用 -> 15 passed / exit code 0
  - B2〜B6 MS21回帰 -> 123 passed / exit code 0（B5専用再確認28 passed / exit code 0を含む）
  - MS17 / MS19 / MS20・既存回帰 -> 154 passed、7 subtests passed / exit code 0
  - `pytest tests` -> 618 passed、7 subtests passed / exit code 0
  - `compileall src tests`、`git diff --check` -> exit code 0
  - B1〜B7のユーザー手動GUI確認報告を範囲限定で再利用。Codexによる手動GUI実行ではない。
- Result:
  - P1 / P2 / P3なし。MS21-B8 CloseoutはA、MS22開始条件を引き継ぐ。
  - 実MMDでのVMD / WAV読み込み・リップ同期はMS26へ引き継ぐ。
  - merge、push、tag、release、branch削除は未実施。

## Entry 2026-07-27 / Session: ms21-b7-completion

- Date: 2026-07-27
- Scope:
  - MS21-B7実装・追加tab補正・手動GUI確認反映
- Changes:
  - analysis rollback、dirty入力guard、parameter snapshot、terminal callback guardを実装した。
  - single-pass UI sync contextとadjustment-only同期でUndo / Redoの重複計算・不要再描画を削減した。
  - Preview event選択時のRightPane「選択イベント」tab自動切替を追加補正した。
  - 自動testのanalysis failure経路が実MessageBoxを開く問題を、test内mockへ限定補修した。
  - README、配布用readme、Pipeline / GUI / Error仕様とMS21 routing文書を同期した。
- Validation:
  - B7本体実装時のfull suite -> 617 passed、7 subtests passed / exit code 0
  - 追加補正・MessageBox test補修後のfull suite -> 618 passed、7 subtests passed / exit code 0
  - `compileall src tests`、`git diff --check` -> exit code 0
  - 追加補正を含むMS21-B7範囲のユーザー手動GUI確認 -> 通過、問題なし
- Result:
  - MS21-B7は完了した。
  - dependency、package、build、license、固定モーフ、VMD形式、network契約に変更はない。
  - 次工程はMS21-B8 Closeout計画。merge、push、tag、release、branch削除は未実施。

## Entry 2026-07-20 / Session: ms20-b8-closeout-execution

- Date: 2026-07-20
- Scope:
  - MS20-B8 MS20 Closeout実施
- Changes:
  - B1からB7の要求、実装、テスト、ユーザー確認、README / 配布用readme / 3正本仕様、MS20差分を総合監査した。
  - pre-implementation checkで検出したBlock Breakdownの古い成果物候補表記を修正した。
  - B8 plan、Block Breakdown、Index、Roadmap、repo milestone、Version ControlをMS20 CloseOut済みへ同期した。
  - production code、test code、GUI、dependency、build/package設定は変更していない。
- Validation:
  - MS20固有テスト -> 108 passed / exit code 0
  - state / GUI / worker / voice_only回帰 -> 65 passed、7 subtests passed表示 / exit code 1
  - pipeline / VMD回帰 -> 12 passed / exit code 0
  - `pytest tests` -> 476 passed表示 / exit code 1
  - exit code 1の2系統はfailure / error / fatal stack traceなしでsummaryまで完走し、B7 baselineと一致した。
  - `compileall src tests`、`git diff --check` -> exit code 0
- Result:
  - P1 / P2なし。P3 1件は文書同期で解消し、残存findingなし。
  - B3からB7の通過済みユーザーGUI確認を再利用した。Closeout監査後、ユーザーからB8チェック通過・問題なしと報告された。
  - 自動検証とユーザー確認が揃い、MS20 CloseoutをA判定で確定した。次工程はMS21 Implementation Plan策定。
  - main merge、remote push、tag、release、branch削除は未実施。

## Entry 2026-07-13 / Session: ms19-b9-closeout-execution

- Date: 2026-07-13
- Scope:
  - MS19-B9 MS19 Closeout実施
- Changes:
  - MS19固有テスト、計画指定回帰、全体pytestを実行した。
  - B3からB9のユーザー確認記録、関連文書、MS19差分、dependency / packaging / license関連ファイルを確認した。
  - `tests/test_wx_ms14_b6_closeout.py` の終了処理を補修し、フレーム破棄前に `_cleanup_analysis_job()` を実行するようにした。
  - `AGENTS.md` のGPT環境移行由来の未コミット変更はユーザー指示により保留し、今回のステージ対象から除外する。
- Validation:
  - MS19固有テスト -> 33 passed / exit code 0
  - `test_wx_ms14_b6_closeout.py` -> 補修後 3 passed / exit code 0
  - 計画指定回帰 -> 62 passed表示 / exit code 1
  - `pytest tests` -> 368 passed表示 / exit code 1
  - `git diff --check d876397..HEAD` -> 問題なし
- Result:
  - P1なし、P2解消。
  - Production code、build/package設定は変更していない。
  - ユーザーチェック通過・問題なし。
  - MS19 CloseoutはA。次工程はpackage / release作業またはMS20計画策定。

## Entry 2026-07-12 / Session: ms19-b9-closeout-plan

- Date: 2026-07-12
- Scope:
  - MS19-B9 MS19 Closeout実装プラン作成
- Changes:
  - `docs/Implementation_Plan/MS19-B9_Implementation_Plan.md` を新規作成した。
  - B1からB8の成果、テスト、ユーザー確認、文書を再照合するCloseout手順を定義した。
  - MS19固有テスト、core / GUI回帰、通常 `pytest tests` の確認順序を定義した。
  - 既存wx終了処理について、pass表示とprocess exit codeを分離してbaseline比較する方針を明記した。
  - package / release、version bump、merge / push、MS20実装をOut of Scopeとした。
  - `docs/Implementation_Plan/MS19_Block_Breakdown.md`、`docs/MS17_and_Beyond_Index.md`、`docs/MS18_and_Beyond_Roadmap.md` をB9計画作成済みへ同期した。
- Result:
  - MS19-B9実装プラン作成済み。
  - 次作業はMS19-B9実装前チェック。
  - B9計画作成によるProduction code / test変更なし。

## Entry 2026-07-11 / Session: ms19-b8-workspace-reset-implementation

- Date: 2026-07-11
- Scope:
  - MS19-B8 Workspace Reset / New Session Flow 実装・ユーザー確認
- Changes:
  - `UiState.has_workspace_user_data` と `UiState.reset_workspace()` を追加し、設定・履歴を保持する作業データ限定resetを実装した。
  - `AppController` にaudio job ID無効化、再生停止、viewport初期化、UiState・表示同期をまとめるreset入口を追加した。
  - `MainFrame` のファイルメニューへ `新規作業... Ctrl+N`、確認ダイアログ、Busy中無効、analysis job ID無効化を追加した。
  - InfoPanel、Waveform、Preview、RightPane、playback cursor、viewportを未入力初期表示へ戻すようにした。
  - `tests/test_ms19_b8_workspace_reset.py` を追加し、確認Yes / No、Busy拒否、保持対象、late callback破棄、ファイル非削除を確認した。
  - README、配布用readme、GUI状態仕様、pipelineデータ契約、MS19進捗文書を実装・ユーザー確認済み状態へ同期した。
- Validation:
  - `tests/test_ms19_b8_workspace_reset.py` -> 8 passed / exit code 0
  - B8対象・関連回帰 -> 60 passed表示 / process exit code 1
  - `pytest tests` -> 368 passed表示 / process exit code 1
  - 2026-07-11 ユーザースモークテスト通過・問題なし。
- Result:
  - MS19-B8 Workspace Reset / New Session Flow は完了。
  - MS19 CloseoutはB9で実施する。
  - 次作業はMS19-B9 Closeout実装プランの策定。

## Entry 2026-07-11 / Session: ms19-b8-workspace-reset-plan

- Date: 2026-07-11
- Scope:
  - MS19-B8 Workspace Reset / New Session Flow 実装プラン作成
  - MS19 CloseoutのB9移動
- Changes:
  - `docs/Implementation_Plan/MS19-B8_Implementation_Plan.md` を新規作成した。
  - ファイルメニューの `新規作業... Ctrl+N`、作業データ限定reset、確認キャンセル、Busy制御、表示・playback・viewport復帰、job ID無効化、設定・履歴保持契約を定義した。
  - dedicated toolbarボタン、設定初期化、ファイル削除、Busy中workerの自動cancel + resetはB8対象外とした。
  - `docs/Implementation_Plan/MS19_Block_Breakdown.md` のB8をWorkspace Resetへ変更し、CloseoutをB9へ移動した。
  - `docs/MS17_and_Beyond_Index.md` と `docs/MS18_and_Beyond_Roadmap.md` をB8計画作成済みへ同期した。
- Result:
  - MS19-B8実装プラン作成済み。
  - 次作業はMS19-B8実装前チェック。
  - Production code / test変更なし。

## Entry 2026-07-10 / Session: ms19-b7-error-tests-docs-implementation

- Date: 2026-07-10
- Scope:
  - MS19-B7 Error Handling / Tests / Docs 実装
- Changes:
  - `src/gui_wx/voice_only_errors.py` を追加し、音声のみ解析の代表的失敗条件とユーザー向け再試行案内を分類した。
  - `MainFrame` の解析失敗表示をvoice_only向けに分岐し、失敗時入力モードを状態同期前に保持するようにした。
  - `AppController` のvoice_only VMD保存失敗表示を再試行可能な案内へ更新し、解析結果保持をテストした。
  - B7エラー処理テスト、通常pytest用 `tests/conftest.py`、旧MS14 fixture修正を追加した。
  - README / 配布用readme / 関連仕様 / MS19進捗文書をB7実装済み・ユーザー確認待ちへ同期した。
- Validation:
  - `tests/test_ms19_b7_voice_only_error_handling.py` -> 6 passed / exit code 0
  - B7対象・関連回帰テスト -> 59 passed / exit code 0
  - `pytest tests` -> 360 passed表示 / process exit code 1
- Result:
  - B7実装と自動確認は完了。
  - 2026-07-10 にユーザー確認通過・問題なし。
  - MS19-B7 closeoutはOK。
  - 次作業はMS19-B8 MS19 Closeout実装プラン策定。

## Entry 2026-07-09 / Session: ms19-b7-error-tests-docs-plan

- Date: 2026-07-09
- Scope:
  - MS19-B7 Error Handling / Tests / Docs 実装プラン作成
  - MS19-B7参照の関連文書同期
- Changes:
  - `docs/Implementation_Plan/MS19-B7_Implementation_Plan.md` を新規作成した。
  - B7の対象を、音声のみ入力に固有の失敗条件分類、状態復帰、テスト実行状態整理、README / 配布用readme / 関連docs同期に限定した。
  - Whisper失敗、書き起こし空、読み変換失敗、母音列なし、編集済みテキスト空、VMD保存失敗を、B7で扱う代表エラー条件として整理した。
  - 通常 `pytest tests` のimport path収集問題と `tests/test_wx_ms14_b6_closeout.py` の既存closeout系2件失敗は、B7実装前チェックで分類する方針とした。
  - `docs/MS17_and_Beyond_Index.md` にMS19-B7計画書をアクティブドキュメントとして追加した。
  - `docs/Implementation_Plan/MS19_Block_Breakdown.md` にMS19-B7計画作成済みのステータスを追記した。
  - `docs/MS18_and_Beyond_Roadmap.md` の次作業表記をMS19-B7実装前チェックへ更新した。
  - `docs/repo_milestone.md` にMS19-B7計画作成エントリを追加した。
- Result:
  - MS19-B7 Error Handling / Tests / Docs の実装プランは作成済みである。
  - 2026-07-10 にMS19-B7はユーザー確認通過・完了済み。現在の次作業は `MS19-B8: MS19 Closeout` の実装プラン策定。
- Notes:
  - Code changes: none for B7 planning.
  - GUI changes: none for B7 planning.
  - Test changes: none for B7 planning.

## Entry 2026-07-09 / Session: ms19-b6-vmd-preview-save-implementation

- Date: 2026-07-09
- Scope:
  - MS19-B6 VMD / Preview / Save Integration
  - 音声のみ入力のTEXTなしVMD保存有効化
  - MS19-B6関連文書同期
- Changes:
  - `src/core/pipeline.py` に `generate_vmd_from_timing_plan()` と `VmdGenerationResult` を追加し、TEXT pathなしで `current_timing_plan` からVMD保存できる入口を実装した。
  - 既存TEXTあり保存入口 `generate_vmd_from_text_wav()` と `PipelineResult.text_path` の契約は維持した。
  - `src/core/__init__.py` から新規VMD保存入口をexportした。
  - `src/gui_wx/ui_state.py` の `vmd_save_ready` を拡張し、voice_only解析成功後は保存可、編集適用直後の未再解析状態は保存不可にした。
  - `src/gui_wx/app_controller.py` のVMD保存処理をTEXTあり / voice_onlyで分岐し、voice_onlyでは `generate_vmd_from_timing_plan()` を呼ぶようにした。
  - `src/gui_wx/main_frame.py` からB4/B5時点の「TEXTなしVMD保存は未対応」ステータス文言を除去した。
  - `tests/test_pipeline_and_vmd.py`、`tests/test_ms19_b4_voice_only_gui_state.py`、`tests/test_ms19_b5_transcription_edit_state.py`、`tests/test_wx_ms14_b2_state.py`、`tests/test_wx_ms14_b5_export.py` をB6後の保存契約へ更新した。
  - `docs/Implementation_Plan/MS19-B6_Implementation_Plan.md`、`docs/Implementation_Plan/MS19_Block_Breakdown.md`、`docs/MS17_and_Beyond_Index.md`、`docs/MS18_and_Beyond_Roadmap.md`、`docs/repo_milestone.md` をB6実装済み・ユーザー確認通過状態へ同期した。
- Result:
  - MS19-B6 closeoutはOK。
  - ユーザー側B6確認は2026-07-09に通過・問題なし。
  - 音声のみ解析成功後、TEXT pathなしでVMD保存できる。
  - 編集適用直後の未再解析状態ではVMD保存不可、編集済み再解析成功後はVMD保存可。
  - 2026-07-10 にMS19-B7はユーザー確認通過・完了済み。現在の次作業は `MS19-B8: MS19 Closeout` の実装プラン策定。
- Validation:
  - `.\.venv\Scripts\python.exe -m pytest tests\test_pipeline_and_vmd.py tests\test_ms19_b4_voice_only_gui_state.py tests\test_ms19_b5_transcription_edit_state.py tests\test_wx_ms14_b2_state.py tests\test_wx_ms14_b5_export.py` -> 36 passed / exit code 0
  - `git diff --check` -> 空白エラーなし。LF→CRLF警告のみ。
  - `.\.venv\Scripts\python.exe -m pytest tests` -> 収集時に既存import path不足で停止。
  - `src` / `tests` を `sys.path` に追加した全体確認 -> `tests/test_wx_ms14_b6_closeout.py` の既存closeout系2件のみ失敗。B6保存導線の対象テストでは問題なし。
- Notes:
  - MMD用WAV出力仕様、VMD writerの全面再設計、Qt / PySide6復活、新規依存追加は行っていない。

## Entry 2026-07-08 / Session: ms19-b6-vmd-preview-save-plan

- Date: 2026-07-08
- Scope:
  - MS19-B6 VMD / Preview / Save Integration 実装プラン作成
  - MS19-B6参照の関連文書同期
- Changes:
  - `docs/Implementation_Plan/MS19-B6_Implementation_Plan.md` を新規作成した。
  - B6の対象を、音声のみ入力のVMD保存有効化、TEXT pathなし保存入口、Preview追従確認、既存TEXTあり保存導線維持に限定した。
  - 既存 `generate_vmd_from_text_wav()` の破壊的な契約変更は行わず、音声のみ入力向けに `current_timing_plan` からVMDを書き出す別入口を追加する方針とした。
  - 編集適用直後の未再解析状態ではVMD保存不可、編集済み再解析成功後はVMD保存可とする状態契約を明記した。
  - `docs/MS17_and_Beyond_Index.md` にMS19-B6計画書をアクティブドキュメントとして追加した。
  - `docs/Implementation_Plan/MS19_Block_Breakdown.md` に当時のMS19-B6計画作成ステータスを追記した。
  - `docs/MS18_and_Beyond_Roadmap.md` の次作業表記を、当時の次工程へ更新した。
- Result:
  - このエントリ作成時点では、MS19-B6 VMD / Preview / Save Integration の実装プラン作成まで完了していた。
  - 2026-07-10 にMS19-B7はユーザー確認通過・完了済み。現在の次作業は `MS19-B8: MS19 Closeout` の実装プラン策定。
- Notes:
  - Code changes: none for B6 planning.
  - GUI changes: none for B6 planning.
  - Test changes: none for B6 planning.

## Entry 2026-07-08 / Session: ms19-b5-transcription-edit-flow

- Date: 2026-07-08
- Scope:
  - MS19-B5 Review / Edit Transcription Result Flow
  - 音声のみ解析結果の書き起こし編集UI
  - 編集済みテキスト再解析時の保持済みWhisper timing result再利用
  - MS19-B5関連文書同期
- Changes:
  - `src/gui_wx/info_panel.py` に書き起こし編集欄のeditable切替、適用ボタン、元に戻すボタン、編集本文取得APIを追加した。
  - `src/gui_wx/ui_state.py` に、元の書き起こし本文、現在の書き起こし本文、編集済み状態、未再解析状態、保持済み `WhisperTimingResult` を追加した。
  - `src/gui_wx/analysis_worker.py` に `whisper_timing_result` 返却を追加し、編集済みテキスト再解析時は保持済み timing result を使ってWhisperを再実行しない契約を追加した。
  - `src/gui_wx/main_frame.py` に、書き起こし編集の適用 / 元に戻す処理、未適用編集ガード、編集済みテキスト再解析 worker 起動を追加した。
  - `tests/test_ms19_b5_transcription_edit_state.py` を追加し、B5のGUI state / worker契約を検証した。
  - `tests/test_ms19_b4_analysis_worker_voice_only.py` をB5後の `whisper_timing_result` 返却契約に合わせて更新した。
  - `docs/Implementation_Plan/MS19-B5_Implementation_Plan.md`、`docs/Implementation_Plan/MS19_Block_Breakdown.md`、`docs/MS17_and_Beyond_Index.md`、`docs/MS18_and_Beyond_Roadmap.md`、`docs/repo_milestone.md` をB5完了・次作業B6計画作成へ更新した。
- Result:
  - MS19-B5 closeoutはOK。
  - ユーザー側B5確認は2026-07-08に通過・問題なし。
  - このエントリ作成時点では、音声のみ入力のVMD保存有効化は未対応で、MS19-B6で扱う予定だった。
  - 2026-07-10 にMS19-B7はユーザー確認通過・完了済み。現在の次作業は `MS19-B8: MS19 Closeout` の実装プラン策定。
- Validation:
  - `.\.venv\Scripts\python.exe -m pytest tests\test_ms19_b5_transcription_edit_state.py` -> 6 passed / exit code 0
  - `.\.venv\Scripts\python.exe -m pytest tests\test_ms19_b4_analysis_worker_voice_only.py` -> 1 passed / exit code 0
  - `.\.venv\Scripts\python.exe -m pytest tests\test_ms19_b4_voice_only_gui_state.py` -> 5 passed / exit code 0
  - `.\.venv\Scripts\python.exe -m pytest tests\test_wx_ms14_b2_state.py` -> 5 passed / exit code 0
  - `.\.venv\Scripts\python.exe -m pytest tests\test_wx_ms14_b4_analysis.py` -> 3 passed / exit code 0
  - `.\.venv\Scripts\python.exe -m pytest tests\test_whisper_timing.py` -> 3 passed / exit code 0
- Notes:
  - B5ではVMD writer変更、TEXTなしVMD保存導線、Preview / Saveの最終連携、永続的な書き起こし履歴管理は行っていない。

## Entry 2026-07-07 / Session: ms19-b5-plan

- Date: 2026-07-07
- Scope:
  - MS19-B5 Review / Edit Transcription Result Flow 実装プラン作成
  - MS19-B5参照の関連文書同期
- Changes:
  - `docs/Implementation_Plan/MS19-B5_Implementation_Plan.md` を新規作成した。
  - B5の対象を、音声のみ解析結果の書き起こし編集、編集後のひらがな / 母音列preview更新、編集前timing planの誤用防止、保持済み `WhisperTimingResult` と明示的な worker 入力契約による編集済みテキスト再解析の最小導線に限定した。
  - 編集済みテキスト再解析で `current_timing_plan` を更新した場合、既存Previewが追従して再描画されることはB5の許容範囲とした。
  - 音声のみ入力のVMD保存有効化、Preview操作、再生タイムライン操作、VMD保存まで含む最終連携、永続的な書き起こし履歴管理、外部字幕形式出力、Qt / PySide6 GUI復活はB5のOut of Scopeとして明記した。
  - `docs/Implementation_Plan/MS19_Block_Breakdown.md` にMS19-B5計画作成済みのステータス、In Scope / Out of Scopeを追記した。
  - `docs/MS17_and_Beyond_Index.md` にMS19-B5計画書をアクティブドキュメントとして追加した。
  - `docs/MS18_and_Beyond_Roadmap.md` の次作業表記を、B5計画作成時点の次工程へ更新した。
- Result:
  - このエントリは2026-07-07のMS19-B5計画作成時点の記録である。
  - 2026-07-08 にMS19-B5 Review / Edit Transcription Result Flowは実施済み。
  - 2026-07-10 にMS19-B7はユーザー確認通過・完了済み。現在の次作業は `MS19-B8: MS19 Closeout` の実装プラン策定。
- Notes:
  - Code changes: none for B5 planning.
  - GUI changes: none for B5 planning.
  - Test changes: none for B5 planning.

## Entry 2026-07-07 / Session: ms19-b4-gui-entry-state

- Date: 2026-07-07
- Scope:
  - MS19-B4 GUI Entry Point and State Handling
  - TEXTなし音声入力のGUI解析導線
  - voice_only状態保持とInfoPanel最小反映
  - TEXTなしVMD保存無効化
  - Whisper実行時のrepo-local FFmpeg PATH補正
- Changes:
  - `src/gui_wx/ui_state.py` に `text_audio` / `voice_only` の入力モード、解析開始可否、TEXTありVMD保存可否、transcription保持フィールドを追加した。
  - `src/gui_wx/analysis_worker.py` に `AnalysisWorkerResult` とTEXTあり / voice_only分岐を追加した。
  - voice_only分岐では `recognize_audio_timing()` を1回だけ実行し、同じ `WhisperTimingResult` を `build_vowel_timing_plan(..., whisper_timing_result=...)` へ渡すことでWhisper二重実行を避けるようにした。
  - `src/gui_wx/main_frame.py` でTEXTなし音声入力時の解析ボタン有効化、解析成功時の書き起こし本文・ひらがな・母音列のInfoPanel最小反映、voice_only解析後のVMD保存無効化を実装した。
  - `src/gui_wx/app_controller.py` で `selected_text_path=None` の状態ではVMD保存ダイアログや `generate_vmd_from_text_wav()` へ進まないようにした。
  - 音声のみ解析で発生した `WinError 2` に対し、Whisper実行中だけ検出済み `FFmpeg\bin` を `PATH` 先頭へ一時追加し、実行後に元へ戻す補正を `src/core/whisper_timing.py` に追加した。
  - `tests/test_ms19_b4_voice_only_gui_state.py` と `tests/test_ms19_b4_analysis_worker_voice_only.py` を追加した。
  - `tests/test_whisper_timing.py`、`tests/test_wx_ms14_b2_state.py`、`tests/test_wx_ms14_b4_analysis.py` をB4後の契約に合わせて更新した。
  - `docs/Implementation_Plan/MS19-B4_Implementation_Plan.md`、`docs/Implementation_Plan/MS19_Block_Breakdown.md`、`docs/MS17_and_Beyond_Index.md`、`docs/MS18_and_Beyond_Roadmap.md`、`docs/repo_milestone.md` をB4完了・次作業B5計画作成へ更新した。
- Result:
  - MS19-B4 closeoutはOK。
  - ユーザー側音声のみ解析スモークテストは2026-07-07に通過・問題なし。
  - 2026-07-08 にMS19-B5 Review / Edit Transcription Result Flowは実施済み。
  - 2026-07-10 にMS19-B7はユーザー確認通過・完了済み。現在の次作業は `MS19-B8: MS19 Closeout` の実装プラン策定。
- Validation:
  - `.\.venv\Scripts\python.exe -m pytest tests\test_ms19_b4_analysis_worker_voice_only.py` -> 1 passed / exit code 0
  - `.\.venv\Scripts\python.exe -m pytest tests\test_ms19_b4_voice_only_gui_state.py` -> 表示上 5 passed。pytest process の exit code は 1。
  - `.\.venv\Scripts\python.exe -m pytest tests\test_whisper_timing.py` -> 3 passed / exit code 0
  - `.\.venv\Scripts\python.exe -m pytest tests\test_wx_ms14_b2_state.py` -> 5 passed / exit code 0
  - `.\.venv\Scripts\python.exe -m pytest tests\test_wx_ms14_b3_input.py` -> 2 passed / exit code 0
  - `.\.venv\Scripts\python.exe -m pytest tests\test_wx_ms14_b4_analysis.py` -> 3 passed / exit code 0
  - `.\.venv\Scripts\python.exe -m pytest tests\test_ms19_b3_transcription_contract.py tests\test_ms19_b3_textless_pipeline.py tests\test_whisper_timing.py tests\test_pipeline_and_vmd.py` -> 17 passed / exit code 0
  - `.\.venv\Scripts\python.exe -m pytest tests\test_app_version.py tests\test_wx_ms13_integration.py` -> 10 passed / exit code 0
  - `git diff --check` -> エラーなし。CRLF警告のみ。
- Notes:
  - B4では書き起こし編集UI、TEXTなしVMD保存導線、VMD writer変更、`generate_vmd_from_text_wav()` の `text_path` 契約変更は行っていない。
  - voice_only解析結果ができても、B4ではVMD保存ボタンを有効化しない。

## Entry 2026-07-06 / Session: ms19-b4-plan

- Date: 2026-07-06
- Scope:
  - MS19-B4 GUI Entry Point and State Handling 実装プラン作成
  - MS19-B4参照の関連文書同期
- Changes:
  - `docs/Implementation_Plan/MS19-B4_Implementation_Plan.md` を新規作成した。
  - B4の対象を、wxPython GUI上のTEXTなし音声入力状態、解析ボタン有効条件、`AnalysisWorker` のTEXTあり / voice_only分岐、InfoPanelへの最小反映に限定した。
  - 書き起こし編集UI、VMD保存導線、VMD writer変更、`generate_vmd_from_text_wav()` の `text_path` 契約変更はB4のOut of Scopeとして明記した。
  - `docs/Implementation_Plan/MS19_Block_Breakdown.md` にMS19-B4計画作成済みのステータス、成果物、受け入れ条件を追記した。
  - `docs/MS17_and_Beyond_Index.md` にMS19-B4計画書をアクティブドキュメントとして追加した。
  - `docs/MS18_and_Beyond_Roadmap.md` の次作業表記をMS19-B4実装前チェック / 実装へ更新した。
  - `docs/repo_milestone.md` にMS19-B4計画作成記録を追加した。
- Result:
  - このエントリは2026-07-06のMS19-B4計画作成時点の記録である。
  - 2026-07-07 にMS19-B4 GUI Entry Point and State Handlingは実施済み。
  - 2026-07-08 にMS19-B5 Review / Edit Transcription Result Flowは実施済み。
  - 2026-07-10 にMS19-B7はユーザー確認通過・完了済み。現在の次作業は `MS19-B8: MS19 Closeout` の実装プラン策定。
- Notes:
  - Code changes: none for B4 planning.
  - GUI changes: none for B4 planning.
  - Test changes: none for B4 planning.

## Entry 2026-07-06 / Session: ms19-b3-textless-pipeline

- Date: 2026-07-06
- Scope:
  - MS19-B3 Textless Pipeline Integration Foundation
  - Whisper raw resultからの本文抽出helper追加
  - 既存 `WhisperTimingResult` 再利用によるtiming plan生成契約追加
- Changes:
  - `src/core/whisper_timing.py` に `TranscriptionTextResult` と `extract_transcription_text()` を追加した。
  - `extract_transcription_text()` は `segments[].text` を優先し、必要時のみ `raw_result["text"]` へfallbackし、`words[].word` だけでは本文成功扱いにしない。
  - `src/core/pipeline.py` の `build_vowel_timing_plan()` に `whisper_timing_result` optional引数を追加し、指定時は `recognize_audio_timing()` を再実行しないようにした。
  - `src/core/__init__.py` にB3追加APIと既存 `WhisperTimingResult` exportを追加した。
  - `tests/test_ms19_b3_transcription_contract.py` と `tests/test_ms19_b3_textless_pipeline.py` を追加した。
  - `docs/Implementation_Plan/MS19-B3_Implementation_Plan.md`、`docs/Implementation_Plan/MS19_Block_Breakdown.md`、`docs/MS17_and_Beyond_Index.md`、`docs/MS18_and_Beyond_Roadmap.md`、`docs/Implementation_Plan/MS18_Block_Breakdown.md`、`docs/Implementation_Plan/MS18-B7_Implementation_Plan.md`、`docs/repo_milestone.md` をMS19-B3完了、次作業MS19-B4へ更新した。
- Result:
  - MS19-B3 closeoutはOK。
  - 2026-07-07 にMS19-B4 GUI Entry Point and State Handlingは実施済み。
  - 2026-07-08 にMS19-B5 Review / Edit Transcription Result Flowは実施済み。
  - 2026-07-10 にMS19-B7はユーザー確認通過・完了済み。現在の次作業は `MS19-B8: MS19 Closeout` の実装プラン策定。
- Validation:
  - `.\.venv\Scripts\python.exe -m pytest tests\test_ms19_b3_transcription_contract.py` -> 4 passed
  - `.\.venv\Scripts\python.exe -m pytest tests\test_ms19_b3_textless_pipeline.py` -> 2 passed
  - `.\.venv\Scripts\python.exe -m pytest tests\test_whisper_timing.py` -> 2 passed
  - `.\.venv\Scripts\python.exe -m pytest tests\test_text_processing.py` -> 10 passed
  - `.\.venv\Scripts\python.exe -m pytest tests\test_pipeline_and_vmd.py` -> 9 passed
- Smoke:
  - B3 core smoke: `tests/test_ms19_b3_transcription_contract.py tests/test_ms19_b3_textless_pipeline.py` -> 6 passed / exit code 0
  - Version smoke: `tests/test_app_version.py` -> 6 passed / exit code 0
  - wx MS13 integration smoke: `tests/test_wx_ms13_integration.py` -> 4 passed / exit code 0
  - wx startup splash smoke: `tests/test_wx_startup_splash.py` -> 表示上 2 passed。pytest process の exit code は 1。
  - User smoke test: 2026-07-06 にユーザー確認通過。
  - `build.ps1 -Clean -SmokeLaunch`: B3はpackaging変更ではないため未実行。
- Notes:
  - GUI changes: none.
  - VMD writer changes: none.
  - `generate_vmd_from_text_wav()` の `text_path` 契約変更: none.

## Entry 2026-07-05 / Session: ms19-b3-plan

- Date: 2026-07-05
- Scope:
  - MS19-B3 Textless Pipeline Integration Foundation 実装プラン作成
  - MS19-B3参照の関連文書同期
- Changes:
  - `docs/Implementation_Plan/MS19-B3_Implementation_Plan.md` を新規作成した。
  - B3の対象を、Whisper raw resultからの本文抽出helper、既存 `WhisperTimingResult` を再利用できる `build_vowel_timing_plan()` 契約、core単体テストに限定した。
  - `generate_vmd_from_text_wav()` の `text_path` 契約変更、GUI導線、VMD保存導線、VMD writer変更はB3のOut of Scopeとして明記した。
  - `docs/Implementation_Plan/MS19_Block_Breakdown.md` にMS19-B3計画作成済みのステータス、成果物、受け入れ条件を追記した。
  - `docs/MS17_and_Beyond_Index.md` にMS19-B3計画書をアクティブドキュメントとして追加した。
  - `docs/MS18_and_Beyond_Roadmap.md` の次作業表記をMS19-B3実装前チェック / 実装へ更新した。
  - `docs/repo_milestone.md` にMS19-B3計画作成記録を追加した。
- Result:
  - このエントリは2026-07-05のMS19-B3計画作成時点の記録である。
- Follow-up:
  - 2026-07-06 にMS19-B3は実施済み。
  - 2026-07-07 にMS19-B4 GUI Entry Point and State Handlingは実施済み。
  - 2026-07-08 にMS19-B5 Review / Edit Transcription Result Flowは実施済み。
  - 2026-07-10 にMS19-B7はユーザー確認通過・完了済み。現在の次作業は `MS19-B8: MS19 Closeout` の実装プラン策定。
- Notes:
  - Code changes: none.
  - GUI changes: none.
  - Test changes: none.

## Entry 2026-07-05 / Session: ms19-b2-transcription-precheck

- Date: 2026-07-05
- Scope:
  - MS19-B2 Transcription Pipeline Pre-check
  - transcription本文抽出候補、Whisper raw result契約、B3引き継ぎ整理
- Changes:
  - `docs/Implementation_Plan/MS19-B2_Implementation_Plan.md` を `Completed` へ更新し、B2実施結果、transcription_text抽出候補、エラー分類、テスト不足、B3への引き継ぎを追記した。
  - `docs/Implementation_Plan/MS19_Block_Breakdown.md` をMS19-B2完了、次作業MS19-B3へ更新した。
  - `docs/MS17_and_Beyond_Index.md` をMS19-B2完了、次作業MS19-B3へ更新した。
  - `docs/MS18_and_Beyond_Roadmap.md` の次作業表記をMS19-B3へ更新した。
  - `docs/Implementation_Plan/MS18_Block_Breakdown.md` と `docs/Implementation_Plan/MS18-B7_Implementation_Plan.md` の次作業表記をMS19-B3へ更新した。
  - `docs/repo_milestone.md` にMS19-B2 closeout記録を追加した。
  - `docs/repo_milestone.md` のMS19-B2計画作成エントリに、後続でB2実施済みであることを補記した。
- Result:
  - MS19-B2 closeoutはOK。
- Follow-up:
  - 2026-07-06 にMS19-B3は実施済み。
  - 2026-07-07 にMS19-B4 GUI Entry Point and State Handlingは実施済み。
  - 2026-07-08 にMS19-B5 Review / Edit Transcription Result Flowは実施済み。
  - 2026-07-10 にMS19-B7はユーザー確認通過・完了済み。現在の次作業は `MS19-B8: MS19 Closeout` の実装プラン策定。
- Validation:
  - `.\.venv\Scripts\python.exe -m pytest tests\test_whisper_timing.py` -> 2 passed
  - `.\.venv\Scripts\python.exe -m pytest tests\test_text_processing.py` -> 10 passed
  - `.\.venv\Scripts\python.exe -m pytest tests\test_pipeline_and_vmd.py` -> 9 passed
- Notes:
  - Code changes: none.
  - GUI changes: none.
  - Test changes: none.

## Entry 2026-07-04 / Session: ms19-b2-plan

- Date: 2026-07-04
- Scope:
  - MS19-B2 Transcription Pipeline Pre-check 実装プラン作成
  - MS19-B2参照の関連文書同期
- Changes:
  - `docs/Implementation_Plan/MS19-B2_Implementation_Plan.md` を新規作成した。
  - B2の対象を、Whisper raw result保持、書き起こし本文抽出候補、timing anchor契約、エラー分類、既存テスト不足確認に限定した。
  - `docs/Implementation_Plan/MS19_Block_Breakdown.md` にMS19-B2計画作成済みのステータス、成果物、受け入れ条件を追記した。
  - `docs/MS17_and_Beyond_Index.md` にMS19-B2計画書をアクティブドキュメントとして追加した。
  - `docs/repo_milestone.md` にMS19-B2計画作成記録を追加した。
- Result:
  - MS19-B2は計画作成済み。まだ実施完了ではない。
  - 次作業は MS19-B2 Transcription Pipeline Pre-check の実施前チェック / 実施。
- Notes:
  - Code changes: none.
  - GUI changes: none.
  - Test changes: none.

## Entry 2026-07-04 / Session: ms19-b1-state-contract

- Date: 2026-07-04
- Scope:
  - MS19-B1 Voice-only Input Requirements / State Contract
  - MS19-B1実施結果の関連文書同期
  - 古い次作業表記の更新
- Changes:
  - `docs/Implementation_Plan/MS19-B1_Implementation_Plan.md` を `Completed` へ更新し、B1実施結果、状態契約、Risk Inventory、B2への引き継ぎを追記した。
  - `docs/Implementation_Plan/MS19_Block_Breakdown.md` をMS19-B1完了、次作業MS19-B2へ更新した。
  - `docs/MS17_and_Beyond_Index.md` をMS19-B1完了、次作業MS19-B2へ更新した。
  - `docs/MS18_and_Beyond_Roadmap.md`、`docs/Implementation_Plan/MS18_Block_Breakdown.md`、`docs/Implementation_Plan/MS18-B7_Implementation_Plan.md` の次作業表記をMS19-B2へ更新した。
  - `docs/repo_milestone.md` にMS19-B1 closeout記録を追加した。
- Result:
  - MS19-B1 closeoutはOK。
  - 次作業は `MS19-B2: Transcription Pipeline Pre-check`。
- Notes:
  - Code changes: none.
  - GUI changes: none.
  - Test changes: none.

## Entry 2026-07-03 / Session: ms18-closeout

- Date: 2026-07-03
- Scope:
  - MS18 CloseOut
  - B6由来package化前P2のユーザー判断によるクリア反映
  - MS18 closeout A判定への文書同期
- Changes:
  - `docs/Implementation_Plan/MS18-B6_Implementation_Plan.md` のpackage化可否判定をCloseOut時点でAへ更新した。
  - `docs/Implementation_Plan/MS18-B7_Implementation_Plan.md` にMS18 CloseOut結果を追記し、MS18全体判定をAへ更新した。
  - `docs/MS17_and_Beyond_Index.md` をMS18 CloseOut済み、MS18-B6/B7完了、A判定へ更新した。
  - `docs/MS18_and_Beyond_Roadmap.md` をMS18 CloseOut済みの現在地へ更新し、次作業をMS19実装プラン策定またはpackage / release作業へ変更した。
  - `docs/Implementation_Plan/MS18_Block_Breakdown.md` をMS18 CloseOut A判定へ更新した。
  - `docs/repo_milestone.md` にMS18 CloseOut記録を追加した。
- Decision:
  - FFmpeg license texts / notice、`FFmpeg\bin\` Git追跡扱い、PyInstaller xref上の `PySide6` 参照は、ユーザー判断によりクリア扱いとした。
  - `sample/` は、出典・ライセンス・用途説明が確定できない限り実行用ZIPから除外する方針を維持する。
- Result:
  - MS18 closeout判定はA。
  - MS18はCloseOut済み。
- Notes:
  - Code changes: none.
  - package作成、GitHub Release公開、installer作成は未実施。

## Entry 2026-07-03 / Session: ms18-b7-mmd-manual-closeout

- Date: 2026-07-03
- Scope:
  - MS18-B7 Actual MMD Manual Verification Closeout
  - 実MMDユーザー確認結果の記録
  - MS18 closeout判定の文書同期
- Changes:
  - `docs/Implementation_Plan/MS18-B7_Implementation_Plan.md` を `Completed` へ更新し、B7実施結果、Codex側一時生成物、ユーザー確認通過、README / readme反映不要判断、MS18 C判定を追記した。
  - `docs/MS17_and_Beyond_Index.md` をB7完了・MS18 C判定へ更新した。
  - `docs/MS18_and_Beyond_Roadmap.md` をB7完了後の現在地と次作業へ更新した。
  - `docs/Implementation_Plan/MS18_Block_Breakdown.md` にB7実施結果、MS18 C判定、package化前残課題を追記した。
  - `docs/repo_milestone.md` にMS18-B7 closeout記録を追加した。
- Validation:
  - `git status --short --branch`
  - `git branch --show-current`
  - `git log --oneline -n 10`
  - `Get-Content -LiteralPath docs\MS17_and_Beyond_Index.md`
  - B7確認用VMD / MMD用WAVの一時生成確認
  - `.\.venv\Scripts\python.exe -m pytest tests\test_ms17_b7_mmd_wav_export.py tests\test_ms17_b7_mmd_wav_failure_cleanup.py tests\test_ms17_b7_mmd_wav_overwrite_confirm.py` -> `10 passed`
- Result:
  - MS18-B7 closeoutはOK。
  - 実MMDユーザー確認は通過、問題なし。
  - この時点ではB6由来のpackage化前P2を未クリアとして扱った。後続の `ms18-closeout` エントリでユーザー判断によりA判定へ更新済み。
- Notes:
  - Code changes: none.
  - README / `readme_mmdautolip.txt` changes: none; B7確認で手順不足や追加注意の必要は報告されなかった。
  - package作成、GitHub Release公開、installer作成は未実施。

## Entry 2026-07-02 / Session: ms18-b7-implementation-plan

- Date: 2026-07-02
- Scope:
  - MS18-B7 Actual MMD Manual Verification Closeout planning
  - 実MMDでのVMD / MMD用WAV読み込み・再生・リップ同期目視確認、ユーザー手動確認結果の記録、MS18 closeout判定の計画化
- Changes:
  - `docs/Implementation_Plan/MS18-B7_Implementation_Plan.md` を新規作成した。
  - B7のIn Scope / Out of Scope、前提条件、対象ファイル、詳細ステップ、テスト方針、受け入れ条件、リスクと対策を定義した。
  - 実MMD確認はユーザー環境依存のため、ユーザー手動確認結果を正として記録できる手順を定義した。
  - MS18-B6で残ったFFmpeg license texts / `FFmpeg\bin\` Git追跡 / PySide6 xref確認は、B7の実MMD確認と分離してpackage化前P2として扱う方針を明記した。
  - `docs/MS17_and_Beyond_Index.md` にMS18-B7の計画作成済み行と文書レジストリを追加した。
  - `docs/Implementation_Plan/MS18_Block_Breakdown.md` の次作業参照へB7計画書を追加した。
  - `docs/MS18_and_Beyond_Roadmap.md` にB7計画作成済みステータスを追記した。
- Validation:
  - `git status --short --branch`
  - `git branch --show-current`
  - `git log --oneline -n 5`
  - `Get-Content -LiteralPath docs\MS17_and_Beyond_Index.md`
  - `rg --files docs\Implementation_Plan`
  - `rg`によるMS18-B7 / Actual MMD Manual Verification Closeout関連箇所確認
- Notes:
  - Code changes: none.
  - User questions: none required; B7 scope was available from existing MS18 docs and B6 closeout state.
  - Tests were not run because this session only created the MS18-B7 implementation plan and related document references.

## Entry 2026-07-02 / Session: ms18-b6-release-package-license-preflight

- Date: 2026-07-02
- Scope:
  - MS18-B6 Release / Packaging / License Preflight
  - 実行用ZIP / GitHub generated Source code archive / FFmpeg license notice / PyInstaller依存関係 / sample同梱方針の確認
- Changes:
  - `docs/Implementation_Plan/MS18-B6_Implementation_Plan.md` を `Completed` へ更新し、B6実施結果を追記した。
  - `docs/Release_Package_Manifest.md` に、`FFmpeg\bin\` がGit追跡対象であることによる source archive 側の配布確認要件を追加した。
  - `NOTICE` / `THIRD_PARTY_LICENSES.md` に、実行用ZIPだけでなくGitHub generated Source code ZIP / tar.gz側でもFFmpeg同梱扱いの確認が必要なことを追記した。
  - `THIRD_PARTY_LICENSES.md` に、PyInstaller解析上の `PySide6` 参照を配布依存関係確認項目として記録した。
  - `README.md` / `readme_mmdautolip.txt` に、配布前ライセンス確認対象を実行用ZIPとsource archiveの両方へ広げて記録した。
  - `docs/MS17_and_Beyond_Index.md` / `docs/MS18_and_Beyond_Roadmap.md` / `docs/Implementation_Plan/MS18_Block_Breakdown.md` / `docs/repo_milestone.md` をB6実施結果へ同期した。
- Validation:
  - `git status --short --branch`
  - `git branch --show-current`
  - `git log --oneline -n 5`
  - `.\.venv\Scripts\python.exe -m PyInstaller --version` -> `6.19.0`
  - `.\FFmpeg\bin\ffmpeg.exe -version` -> `N-123549-g70537ec8e6-20260318`
  - `.\FFmpeg\bin\ffprobe.exe -version` -> `N-123549-g70537ec8e6-20260318`
  - `git ls-files FFmpeg/bin`
  - `rg --files -g "*LICENSE*" -g "*COPYING*" -g "*ffmpeg*" -g "*FFmpeg*"`
  - `Get-ChildItem build\MMD_AutoLipTool`
  - `rg`による `build\MMD_AutoLipTool\xref-MMD_AutoLipTool.html` / `warn-MMD_AutoLipTool.txt` の `PySide6` 参照確認
- Result:
  - MS18-B6 preflight実施は完了。
  - package化へ進む前に、FFmpeg license text / notice、GitHub source archiveへのFFmpeg混入、PySide6混入有無とlicense影響を追加確認する必要がある。
- Notes:
  - Code changes: none.
  - Build script changes: none.
  - Tests were not run because B6 was a release/package/license preflight and documentation synchronization block.

## Entry 2026-07-01 / Session: ms18-b6-implementation-plan

- Date: 2026-07-01
- Scope:
  - MS18-B6 Release / Packaging / License Preflight planning
  - 実行用ZIP同梱物・除外物、FFmpeg license notice、PyInstaller依存関係確認、package化可否判定の計画化
- Changes:
  - `docs/Implementation_Plan/MS18-B6_Implementation_Plan.md` を新規作成した。
  - B6のIn Scope / Out of Scope、対象ファイル、詳細ステップ、テスト方針、受け入れ条件、リスクと対策を定義した。
  - `sample/` は、出典・ライセンス・用途説明が確定できない限り実行用ZIPから除外する推奨方針として整理した。
  - MS18-B5で観測した PyInstallerログ上の `PySide6` hook 選択を、B6の配布内容・依存関係確認項目として明記した。
  - `docs/MS17_and_Beyond_Index.md` にMS18-B6の計画作成済み行と文書レジストリを追加した。
  - `docs/Implementation_Plan/MS18_Block_Breakdown.md` の次作業参照へB6計画書を追加した。
- Validation:
  - `git status --short --branch`
  - `git log --oneline -n 10`
  - `rg`によるMS18-B6 / Release / Packaging / License関連箇所確認
  - `.\FFmpeg\bin\ffmpeg.exe -version`
  - `.\FFmpeg\bin\ffprobe.exe -version`
- Notes:
  - User questions: none required; B6 scope was available from existing MS18 docs, Release_Package_Manifest, license documents, and current build/spec state.

## Entry 2026-07-01 / Session: ms18-b5-smokelaunch-process-residual-fix

- Date: 2026-07-01
- Scope:
  - MS18-B5 SmokeLaunch / Process Residual Investigation
  - `build.ps1 -SmokeLaunch` の停止待機・残留確認
  - `build.ps1 -Clean` の旧onefile成果物削除
- Changes:
  - `build.ps1` の `-Clean` で旧 `dist\MMD_AutoLipTool.exe` を明示削除するようにした。
  - SmokeLaunch起動前に同一exeパスの既存PIDを記録し、B5で起動した対象だけを停止・確認するようにした。
  - `Stop-Process` 後、最大30秒まで対象PIDの終了をポーリングするようにした。
  - 同一 `dist\MMD_AutoLipTool.exe` パスに限定して残留PIDを検出・停止し、既存PIDを停止対象から除外するようにした。
  - `MS18-B5_Implementation_Plan.md`, `MS18_Block_Breakdown.md`, `MS17_and_Beyond_Index.md`, `repo_milestone.md` にB5完了結果を反映した。
- Validation:
  - `git diff --check`: passed.
  - `powershell -ExecutionPolicy Bypass -File .\build.ps1 -Clean -SmokeLaunch`: passed.
  - `powershell -ExecutionPolicy Bypass -File .\build.ps1`: passed.
  - `Get-Process -Name MMD_AutoLipTool -ErrorAction SilentlyContinue`: no process observed after SmokeLaunch.
  - `Get-Process -Name pyinstaller -ErrorAction SilentlyContinue`: no process observed after SmokeLaunch.
  - `Get-Process -Name python -ErrorAction SilentlyContinue`: no process observed after SmokeLaunch.
  - User test: passed, reported by user.
- Notes:
  - 修正途中の検証で、`Stop-Process` 後10秒では `MMD_AutoLipTool.exe` が終了しきらないケースを確認した。確認後には消えていたため、恒久残留ではなく onefile起動後の外部停止完了待ち不足と分類した。
  - PyInstallerログ上、Matplotlib backend収集で `PySide6` hook が選択されている。B5範囲外のため、MS18-B6 Release / Packaging / License Preflightで配布内容・依存関係確認として扱う。

## Entry 2026-06-30 / Session: ms18-b5-implementation-plan

- Date: 2026-06-30
- Session: ms18-b5-implementation-plan
- Summary:
  - `MS18-B5: SmokeLaunch / Process Residual Investigation` の実装プランを作成した。
  - `build.ps1 -SmokeLaunch` のプロセス残留・タイムアウト原因調査手順を、事前確認、build入力確認、プロセス状態確認、SmokeLaunch再現、原因分類、最小修正判断へ分解した。
  - GUI起動を伴う確認では、承認や環境制約を明記し、停止対象をB5で起動したPIDまたは同じexeパスに限定する方針を定義した。
  - `MS17_and_Beyond_Index.md` と `MS18_Block_Breakdown.md` にB5計画書への参照を追加した。
- Modified Files:
  - `docs/Implementation_Plan/MS18-B5_Implementation_Plan.md`
  - `docs/Implementation_Plan/MS18_Block_Breakdown.md`
  - `docs/MS17_and_Beyond_Index.md`
  - `docs/Version_Control.md`
- Verification:
  - `git status --short --branch`
  - `git branch`
  - `git log --oneline -n 10`
  - `Get-Content -LiteralPath docs\MS17_and_Beyond_Index.md`
  - `rg -n -C 80 "## 13\. MS18-B5" docs\Implementation_Plan\MS18_Block_Breakdown.md`
  - `Get-Content -LiteralPath build.ps1`
  - `Get-Content -LiteralPath MMD_AutoLipTool.spec`
  - `Get-Content -LiteralPath src\main.py`
  - `Get-Content -LiteralPath src\gui_wx\app.py`
  - `rg -n "MS18-B5_Implementation_Plan|ms18-b5-implementation-plan|SmokeLaunch / Process Residual|ユーザーへの追加質問|質問" ...`
  - `git diff --check`
- Notes:
  - Code changes: none for this planning step.
  - User questions: none required; B5 scope was available from existing MS18 docs and current `build.ps1`.

## Entry 2026-06-30 / Session: ms18-b4-safe-refactor-implementation

- Date: 2026-06-30
- Session: ms18-b4-safe-refactor-implementation
- Summary:
  - `MS18-B4: Safe Refactor Implementation` を実施した。
  - `src/core/ffmpeg_locator.py` にFFmpeg / ffprobe探索結果のユーザー向け整形補助を追加した。
  - `src/gui_wx/app_controller.py` のFFmpeg / ffprobe未検出メッセージへ、探索元説明を反映した。
  - ユーザーチェックで発生した解析用WAV再生エラーを、Windows MCIが長い解析用WAVファイル名を拒否する問題として特定した。
  - `src/gui_wx/playback_controller.py` で、MCI再生時のみ短い一時ファイル名 `p.wav` のコピーを使い、停止時に削除するよう修正した。
  - 探索順、PATH fallback可否、自動ダウンロード禁止方針、GUI状態遷移、worker起動順は変更していない。
  - `src/main.py` の `error.log` / 起動例外処理は変更していない。
- Modified Files:
  - `src/core/ffmpeg_locator.py`
  - `src/gui_wx/app_controller.py`
  - `src/gui_wx/playback_controller.py`
  - `tests/test_ms17_b3_ffmpeg_locator.py`
  - `tests/test_wx_ms15_b3_playback.py`
  - `docs/Error_Handling_Specification.md`
  - `docs/Implementation_Plan/MS18-B4_Implementation_Plan.md`
  - `docs/Implementation_Plan/MS18_Block_Breakdown.md`
  - `docs/MS17_and_Beyond_Index.md`
  - `docs/repo_milestone.md`
  - `docs/Version_Control.md`
- Verification:
  - `.\.venv\Scripts\python.exe -m pytest tests\test_ms17_b3_ffmpeg_locator.py` -> `8 passed`
  - `.\.venv\Scripts\python.exe -m pytest tests\test_wx_ms14_b3_input.py` -> `2 passed`
  - `.\.venv\Scripts\python.exe -m pytest tests\test_wx_ms15_b3_playback.py` -> `10 passed`
  - MCI direct open check for generated analysis WAV via temporary `p.wav` -> `open_code=0`
  - User check: analysis WAV playback error resolved; user test passed.
- Notes:
  - Next block: `MS18-B5: SmokeLaunch / Process Residual Investigation`.

## Entry 2026-06-29 / Session: ms18-b4-implementation-plan

- Date: 2026-06-29
- Session: ms18-b4-implementation-plan
- Summary:
  - `MS18-B4: Safe Refactor Implementation` の実装プランを作成した。
  - MS18-B3で許可されたB4範囲を、FFmpeg / ffprobe探索元説明性改善と診断情報扱いの小規模整理に限定して、実装手順・テスト方針・受け入れ条件へ分解した。
  - B5/B6/B7へ送るSmokeLaunch、release packaging / license、実MMD確認、cache命名変更などをB4 Out of Scopeとして明記した。
  - `MS17_and_Beyond_Index.md` と `MS18_Block_Breakdown.md` にB4計画書への参照を追加した。
- Modified Files:
  - `docs/Implementation_Plan/MS18-B4_Implementation_Plan.md`
  - `docs/Implementation_Plan/MS18_Block_Breakdown.md`
  - `docs/MS17_and_Beyond_Index.md`
  - `docs/Version_Control.md`
- Verification:
  - `git status --short --branch`
  - `rg --files docs\Implementation_Plan`
  - `rg -n "MS18-B4_Implementation_Plan|B4-001|ms18-b4-implementation-plan|Safe Refactor Implementation" ...`
  - `git diff --check`
  - `git diff --stat`
- Notes:
  - Code changes: none.
  - Tests were not run because this session only created the MS18-B4 implementation plan and related document references.

## Entry 2026-06-29 / Session: ms18-doc-sync-audit

- Date: 2026-06-29
- Session: ms18-doc-sync-audit
- Summary:
  - MS18-B1〜B3の実施結果が関連ドキュメントに反映されているか確認した。
  - `MS18-B1_Implementation_Plan.md` の文書ステータスが `Draft` のまま残っていたため `Completed` へ補正した。
  - `MS17_and_Beyond_Index.md` の現在地表現を、MS18開始準備からMS18進行中へ補正した。
  - B1〜B3完了、B4次作業、B5/B6/B7への引き継ぎは主要ドキュメント間で整合していることを確認した。
- Modified Files:
  - `docs/Implementation_Plan/MS18-B1_Implementation_Plan.md`
  - `docs/MS17_and_Beyond_Index.md`
  - `docs/Version_Control.md`
- Verification:
  - `git status --short --branch`
  - `rg -n "次作業は MS18-B1|次作業は MS18-B2|次作業は MS18-B3|MS18-B4_Implementation_Plan|Security Preflight未実施|文書ステータス: Draft|文書ステータス: Completed" ...`
  - `git diff --check`
- Notes:
  - Code changes: none.
  - Remaining `文書ステータス: Draft` entries are MS18 overall roadmap / block breakdown status, not B1〜B3 block completion status.

## Entry 2026-06-29 / Session: ms18-b3-refactor-scope-definition

- Date: 2026-06-29
- Session: ms18-b3-refactor-scope-definition
- Summary:
  - `MS18-B3: Refactor Scope Definition` を実施した。
  - MS18-B2 Completion Report のP1/P2/P3を確認し、MS18-B4で扱う項目・扱わない項目を分類した。
  - B2でP1は検出されておらず、B4へ必須投入すべきP2もないことを確認した。
  - B4で扱ってよい候補を、PATH fallback時の探索元説明性改善と、`error.log` / 開発コンソールの診断情報扱いの小規模整理に限定した。
  - SmokeLaunch / Clean手順、FFmpeg license / package、実MMD確認はB5/B6/B7へ分離した。
- Modified Files:
  - `docs/Implementation_Plan/MS18-B3_Implementation_Plan.md`
  - `docs/MS17_and_Beyond_Index.md`
  - `docs/MS18_and_Beyond_Roadmap.md`
  - `docs/Implementation_Plan/MS18_Block_Breakdown.md`
  - `docs/repo_milestone.md`
  - `docs/Version_Control.md`
- Verification:
  - `git status --short --branch`
  - `git branch`
  - `git log --oneline -n 10`
  - `git fetch origin`
  - `git rev-parse main`
  - `git rev-parse origin/main`
  - `rg --files docs\Implementation_Plan`
- Notes:
  - Code changes: none.
  - Tests were not run because MS18-B3 is a scope-definition block with no implementation change.
  - Next block: `MS18-B4: Safe Refactor Implementation`.

## Entry 2026-06-28 / Session: ms18-b2-security-preflight-review

- Date: 2026-06-28
- Session: ms18-b2-security-preflight-review
- Summary:
  - `MS18-B2: Security Preflight Review` を実施した。
  - 外部ファイル入力、ffprobe / ffmpeg 実行経路、subprocess引数、shell injection相当リスク、FFmpeg / ffprobe探索順、自動ダウンロード禁止、temp / cache / 出力ファイル処理、GUI worker / Busy状態、PyInstaller onefile、エラーメッセージ / 情報露出、FFmpeg license / release readinessを確認した。
  - Security PreflightとしてP1は検出せず、P2/P3をMS18-B3以降へ引き継いだ。
  - コード変更は行っていない。
- Modified Files:
  - `docs/Implementation_Plan/MS18-B2_Implementation_Plan.md`
  - `docs/MS18_and_Beyond_Roadmap.md`
  - `docs/Implementation_Plan/MS18_Block_Breakdown.md`
  - `docs/MS17_and_Beyond_Index.md`
  - `docs/repo_milestone.md`
  - `docs/Version_Control.md`
- Verification:
  - `git fetch origin`
  - `git rev-parse main`
  - `git rev-parse origin/main`
  - `git ls-files cache`
  - `.\FFmpeg\bin\ffmpeg.exe -version`
  - `.\FFmpeg\bin\ffprobe.exe -version`
  - `.\.venv\Scripts\python.exe -m pytest tests\test_ms17_b3_ffmpeg_locator.py tests\test_ms17_b4_ffprobe_runner.py tests\test_ms17_b5_ffmpeg_runner.py tests\test_ms17_b5_audio_cache.py tests\test_ms17_b5_audio_convert.py tests\test_ms17_b7_mmd_wav_export.py tests\test_ms17_b7_mmd_wav_failure_cleanup.py tests\test_ms17_b7_mmd_wav_overwrite_confirm.py tests\test_ms17_b8_cancel_ffmpeg_ffprobe.py tests\test_ms17_b8_late_worker_result_discard.py tests\test_ms17_b8_busy_action_states.py` -> `42 passed`
- Notes:
  - P2: FFmpeg / ffprobe同梱配布時のlicense texts / notice最終確定はMS18-B6へ引き継ぎ。
  - P2: `build.ps1 -SmokeLaunch` のPyInstallerプロセス残留原因未確定はMS18-B5へ引き継ぎ。
  - P2: 実MMD確認未完了はMS18-B7へ引き継ぎ。
  - P3: PATH fallback説明、`error.log` / 開発コンソールのローカル診断情報、cache stem、`build.ps1 -Clean` の旧onefile成果物明示削除なしを記録。
  - Next block: `MS18-B3: Refactor Scope Definition`.

## Entry 2026-06-28 / Session: ms18-b1-release-readiness-inventory

- Date: 2026-06-28
- Session: ms18-b1-release-readiness-inventory
- Summary:
  - `MS18-B1: Repo / Release Readiness / Risk Inventory` を実施した。
  - `main` と `origin/main` が `1099a79` で一致していること、MS17-B9 closeout と cache追跡対象外化が正本に反映済みであることを確認した。
  - `cache/` が Git 追跡対象外であること、README / NOTICE / THIRD_PARTY_LICENSES.md / Release_Package_Manifest が MS17 closeout状態とリリース前残課題を記録していることを確認した。
  - P1は検出せず、P2/P3をMS18-B2以降へ引き継いだ。
- Modified Files:
  - `docs/Implementation_Plan/MS18-B1_Implementation_Plan.md`
  - `docs/MS18_and_Beyond_Roadmap.md`
  - `docs/Implementation_Plan/MS18_Block_Breakdown.md`
  - `docs/MS17_and_Beyond_Index.md`
  - `docs/repo_milestone.md`
  - `docs/Version_Control.md`
- Verification:
  - `git fetch origin`
  - `git rev-parse main`
  - `git rev-parse origin/main`
  - `git diff --stat`
  - `git diff --name-only`
  - `git diff --cached --stat`
  - `git diff --cached --name-only`
  - `git ls-files cache`
  - `.\FFmpeg\bin\ffmpeg.exe -version`
  - `.\FFmpeg\bin\ffprobe.exe -version`
- Notes:
  - Code changes: none.
  - Tests were not run because MS18-B1 is a repo-state and documentation closeout block with no implementation change.
  - Existing pre-B1 working tree diff remains in `.gitignore`: `.codex/config.toml` ignore entry.
  - Next block: `MS18-B2: Security Preflight Review`.

## Entry 2026-06-03 / Session: ms17-cache-untrack

- Date: 2026-06-03
- Session: ms17-cache-untrack
- Summary:
  - `cache/` をローカル生成物としてGit追跡対象外にした。
  - 既に追跡されていた `cache/analysis_wav/` 配下の解析用WAVをGitインデックスから除外した。
  - 配布ZIPの除外対象に `cache/` を明記した。
- Modified Files:
  - `.gitignore`
  - `docs/Release_Package_Manifest.md`
  - `docs/repo_milestone.md`
  - `docs/Version_Control.md`
- Removed From Git Tracking:
  - `cache/analysis_wav/MMD_AutoLipTool__1_1bd7dfb9_analysis.wav`
  - `cache/analysis_wav/MMD_AutoLipTool__2_03fce0ae_analysis.wav`
- Verification:
  - `git ls-files cache` の出力が空で、追跡対象が残っていないことを確認した。
- Notes:
  - ローカルの `cache/analysis_wav/` ファイル自体は削除していない。
  - 実装コード、FFmpeg処理、解析用WAV生成仕様への変更はない。

## Entry 2026-06-03 / Session: ms17-b9-closeout-doc-sync

- Date: 2026-06-03
- Session: ms17-b9-closeout-doc-sync
- Summary:
  - `MS17-B9: 統合テスト・docs補正・MS17 closeout` を実施した。
  - MS17-B3〜B8の限定テスト群を確認し、MS17音声入力・変換・MMD用WAV出力・worker状態管理の回帰を確認した。
  - README、配布用 `readme_mmdautolip.txt`、`pyproject.toml` descriptionを wav / mp3 / m4a 入力、解析用WAV、専用の MMD用WAV出力導線へ同期した。
  - `NOTICE`、`THIRD_PARTY_LICENSES.md`、`docs/Release_Package_Manifest.md` を現在配置済み FFmpeg / ffprobe 実体に合わせて更新した。
  - `build.ps1` の stale な `FFmpeg v8.1` 固定メッセージを、現在選択した FFmpeg build 前提へ補正した。
  - MS17全体のcloseout判定を記録し、MS18以降の配布検証・実MMD確認へ残課題を引き継いだ。
- Modified Files:
  - `README.md`
  - `readme_mmdautolip.txt`
  - `pyproject.toml`
  - `NOTICE`
  - `THIRD_PARTY_LICENSES.md`
  - `docs/Release_Package_Manifest.md`
  - `build.ps1`
  - `docs/MS17_and_Beyond_Index.md`
  - `docs/Implementation_Plan/MS17_Block_Breakdown.md`
  - `docs/Implementation_Plan/MS17-B9_Implementation_Plan.md`
  - `docs/repo_milestone.md`
  - `docs/Version_Control.md`
- Verification:
  - `.\.venv\Scripts\python.exe -m pytest` with all B3〜B8限定テスト -> 表示上 `69 passed`、終了コード 1（wx teardown由来と見られる既知挙動）
  - 非GUI寄り限定テスト分割実行 -> `55 passed`
  - `tests/test_wx_ms14_b3_input.py` -> `2 passed`
  - B7ダイアログ/ボタン/上書き確認小グループ -> `6 passed`
  - B8状態系小グループ -> `6 passed`
  - 既存GUI回帰テスト (`tests/test_wx_ms15_b1_waveform.py`, `tests/test_wx_ms16_b6_event_selection_foundation.py`) -> `6 passed`
  - `.\FFmpeg\bin\ffmpeg.exe -version` -> `N-123549-g70537ec8e6-20260318`
  - `.\FFmpeg\bin\ffprobe.exe -version` -> `N-123549-g70537ec8e6-20260318`
  - `sample\sample_voice.wav` ffprobe duration -> `4.138957`
  - `sample\sample_voice.wav` から `C:\tmp\ms17_b9_mmd.wav` を生成し、`pcm_s16le / 44100 Hz / stereo` を確認
  - `build.ps1 -SmokeLaunch` -> PyInstallerプロセス残留によりタイムアウト
  - 生成済み `dist\MMD_AutoLipTool.exe` の5秒起動スモーク -> 通過
  - ユーザー手動テスト -> 通過、問題なし（ユーザー報告）
- Notes:
  - 全体pytestは、既知のハング/終了コード不安定性があるためMS17-B9の完了条件に含めず、実行していない。
  - 実MMDでのMMD用WAV読み込み・再生確認はCodex側では未実施。ユーザー手動テスト通過とは別枠で、リリース前確認へ引き継ぐ。
  - 現在配置済み FFmpeg / ffprobe は `--enable-gpl --enable-version3` を含むため、配布前に該当する第三者ライセンス通知を確定する必要がある。
  - `cache/` のGit追跡対象外化は、追補セッション `ms17-cache-untrack` で実施した。

## Entry 2026-06-02 / Session: ms17-b8-audio-worker-busy-cancel

- Date: 2026-06-02
- Session: ms17-b8-audio-worker-busy-cancel
- Summary:
  - `MS17-B8: GUI状態・Busy・長時間処理確認・worker結果破棄統合` を実装した。
  - ffprobe検査、解析用WAV生成、MMD用WAV出力を音声worker経由にし、GUIスレッドで長時間処理を直接実行しない導線へ移行した。
  - `current_audio_job_id` による世代管理、Busy中の主要操作無効化、音声処理用キャンセルボタン、300秒超過時の確認ダイアログを追加した。
  - 既存 `subprocess.run` ベースの runner は互換維持し、B8用に Popen ベースの cancellable runner を追加した。
  - P2修正として、MMD用WAV出力ごとの `audio_job_id` 発行と、終了処理中のworker callback破棄を反映した。
- Modified Files:
  - `src/core/ffmpeg_runner.py`
  - `src/core/ffprobe_runner.py`
  - `src/gui_wx/app_controller.py`
  - `src/gui_wx/main_frame.py`
  - `src/gui_wx/ui_state.py`
  - `tests/test_wx_ms14_b3_input.py`
  - `docs/MS17_and_Beyond_Index.md`
  - `docs/Implementation_Plan/MS17-B8_Implementation_Plan.md`
  - `docs/Implementation_Plan/MS17_Block_Breakdown.md`
  - `docs/repo_milestone.md`
  - `docs/Version_Control.md`
- Added Files:
  - `src/gui_wx/audio_worker.py`
  - `src/gui_wx/worker_state.py`
  - `tests/test_ms17_b8_audio_worker_state.py`
  - `tests/test_ms17_b8_cancel_ffmpeg_ffprobe.py`
  - `tests/test_ms17_b8_long_audio_confirmation.py`
  - `tests/test_ms17_b8_busy_action_states.py`
  - `tests/test_ms17_b8_late_worker_result_discard.py`
- Verification:
  - `.\.venv\Scripts\python.exe -m pytest tests/test_ms17_b8_audio_worker_state.py tests/test_ms17_b8_cancel_ffmpeg_ffprobe.py tests/test_ms17_b8_long_audio_confirmation.py tests/test_ms17_b8_busy_action_states.py tests/test_ms17_b8_late_worker_result_discard.py` -> 11 passed
  - `.\.venv\Scripts\python.exe -m pytest tests/test_wx_ms14_b3_input.py` -> 2 passed
  - `.\.venv\Scripts\python.exe -m pytest tests/test_ms17_b7_mmd_wav_export.py tests/test_ms17_b7_mmd_wav_save_dialog.py tests/test_ms17_b7_mmd_wav_button_state.py tests/test_ms17_b7_mmd_wav_failure_cleanup.py tests/test_ms17_b7_mmd_wav_overwrite_confirm.py` -> 14 passed
  - `.\.venv\Scripts\python.exe -m pytest tests/test_ms17_b4_ffprobe_runner.py tests/test_ms17_b5_ffmpeg_runner.py tests/test_ms17_b5_audio_convert.py` -> 13 passed
  - ユーザー手動テスト: 通過（ユーザー報告）
- Notes:
  - README / 配布文書 closeout、実MMD最終確認は MS17-B9 へ送る。
  - 一部 wx 回帰テストのまとめ実行では、表示上全件 passed だが終了コード 1 となる既存tearDown由来と見られる挙動を確認した。

## Entry 2026-06-01 / Session: ms17-b7-mmd-wav-export

- Date: 2026-06-01
- Session: ms17-b7-mmd-wav-export
- Summary:
  - `MS17-B7: MMD用WAV出力基盤` を実装した。
  - MMD用WAV仕様を `pcm_s16le / 44100 Hz / stereo` 固定として、元音声ファイルから専用WAVを生成する core を追加した。
  - GUIに専用の「MMD用WAV出力」ボタンと保存ダイアログを追加し、解析用WAV生成済みの場合に有効化するようにした。
  - 保存先はユーザー指定、初期ファイル名は元音声stem + `_mmd.wav`、同名ファイルは上書き確認後のみ出力する。
  - MMD用WAV出力はVMD保存処理と連動させず、VMD出力対象もリップモーフキーフレームのみのまま維持した。
  - B7ではffprobe再検査を行わず、B6で保持済みの `AudioProbeResult` を使用する。
  - 3ch以上の入力では ch1/ch2 のみをMMD用WAVへ残し、mono入力では ch1 を stereo へ複製する。
  - 実FFmpeg出力時に `LIST` chunk が混入して検証に失敗するケースを確認し、MMD用WAV出力に `-bitexact` を付けて `fmt -> data` の単純構造へ寄せた。
- Modified Files:
  - `src/core/audio_errors.py`: MMD用WAV出力固有のエラーコードを追加。
  - `src/core/ffmpeg_runner.py`: MMD用WAV用の `run_ffmpeg_mmd_wav` を追加し、ch1/ch2選択と `-bitexact` 出力を実装。
  - `src/core/settings_store.py`: MMD用WAV保存先ディレクトリ設定を追加。
  - `src/gui_wx/ui_state.py`: MMD用WAV出力可能状態と最終出力パスを追加。
  - `src/gui_wx/app_controller.py`: MMD用WAV出力処理を追加。
  - `src/gui_wx/main_frame.py`: 専用ボタン、保存ダイアログ、上書き確認を追加。
  - `tests/test_wx_ms14_b2_state.py`: wx.App teardownを補正し、wx系pytest結合実行の終了コードを安定化。
  - `docs/Implementation_Plan/MS17-B7_Implementation_Plan.md`: 実装前チェックのP2注意点とB7実装後確認を追記。
  - `docs/Implementation_Plan/MS17_Block_Breakdown.md`: MS17-B7完了内容と検証結果を反映。
  - `docs/MS17_and_Beyond_Index.md`: MS17-B7成果、追加source/test目録を反映。
  - `docs/MMD_Audio_WAV_Compatibility_Specification.md`: 実装済みの `-bitexact` 方針を記録。
  - `docs/repo_milestone.md`: MS17-B7実装メモと手動テスト結果を追加。
- Added Files:
  - `src/core/mmd_wav_export.py`
  - `tests/test_ms17_b7_mmd_wav_export.py`
  - `tests/test_ms17_b7_mmd_wav_save_dialog.py`
  - `tests/test_ms17_b7_mmd_wav_button_state.py`
  - `tests/test_ms17_b7_mmd_wav_failure_cleanup.py`
  - `tests/test_ms17_b7_mmd_wav_overwrite_confirm.py`
- Notes:
  - MMD用WAVは解析用WAVとは別のユーザー向け出力物として扱う。
  - MMD用WAV出力失敗時に、既存の timing plan / Preview / VMD保存可能状態は無効化しない。
  - 実FFmpegで生成したMMD用WAVは `RIFF/WAVE -> fmt -> data` の順で検証通過した。
  - ユーザーによるGUI手動テストで、MMD用WAV出力フローに問題がないことを確認した。
  - B8ではMMD用WAV出力中のBusy統合、worker化、cancel、300秒確認を扱う。
  - READMEのMMD用WAV説明更新はB9 closeoutで扱う。
- Verification:
  - `.\.venv\Scripts\python.exe -m pytest tests/test_ms17_b7_mmd_wav_export.py` -> 6 passed
  - `.\.venv\Scripts\python.exe -m pytest tests/test_ms17_b7_mmd_wav_export.py tests/test_ms17_b7_mmd_wav_failure_cleanup.py tests/test_ms17_b7_mmd_wav_button_state.py tests/test_ms17_b7_mmd_wav_save_dialog.py tests/test_ms17_b7_mmd_wav_overwrite_confirm.py` -> 14 passed
  - `.\.venv\Scripts\python.exe -m pytest tests/test_ms17_b5_ffmpeg_runner.py tests/test_ms17_b5_audio_convert.py tests/test_settings_store.py tests/test_wx_ms14_b2_state.py tests/test_wx_ms14_b5_export.py` -> 25 passed
  - 実FFmpeg出力の再現確認: `-bitexact` 追加後に `_validate_mmd_wav_file()` が通過
  - ユーザー手動テスト: MMD用WAV出力フロー問題なし
  - `git diff --check` -> 空白エラーなし（CRLF警告のみ）

## Entry 2026-05-31 / Session: ms17-b6-doc-state-sync

- Date: 2026-05-31
- Session: ms17-b6-doc-state-sync
- Summary:
  - `MS17-B6: wav/mp3/m4a 入力導線統合` が完了済みである現状に合わせ、変更履歴上の欠落を補正した。
  - GUIの音声読み込み導線が wav / mp3 / m4a を扱い、ffprobe検査、解析用WAV生成、波形表示、解析処理へ接続されている状態を記録した。
  - MS17-B7 の方針は、VMD保存処理との連動出力ではなく、専用の「MMD用WAV出力」導線で進める前提として整理した。
  - MMD用WAVのB7仕様は `pcm_s16le / 44100 Hz / stereo` 固定として扱う。
- Modified Files:
  - `README.md`: 音声入力を wav / mp3 / m4a 対応へ更新。
  - `docs/MS17_and_Beyond_Index.md`: MS17-B7 の導線表現を専用出力へ補正。
  - `docs/Implementation_Plan/MS17_Block_Breakdown.md`: MS17-B7 の範囲と受け入れ条件を専用出力 / stereo固定へ補正。
  - `docs/MMD_Audio_WAV_Compatibility_Specification.md`: MMD用WAVのチャンネル仕様を stereo 固定へ補正。
  - `docs/MS16_and_Beyond_Milestone_Map_for_Antigravity.md`: MS17の表現を wav/mp3/m4a 入力対応済みの現状へ補正。
  - `docs/Ver0_4_Expansion_Roadmap_for_Antigravity.md`: Phase 5 の入力形式表現を補正。
  - `docs/VMD_Output_Specification.md`: MMD用WAV出力とVMD出力契約の関係を補正。
  - `docs/Error_Handling_Specification.md`: 現行 `AudioErrorCode` と解析用WAV用語に合わせてエラー分類表現を補正。
  - `docs/Security_Safety_Specification.md`: 音声入力拡張とMMD用WAV出力の安全仕様表現を補正。
  - `docs/repo_milestone.md`: MS17以降の音声拡張表現を補正。
  - `docs/Implementation_Plan/MS17-B6_Implementation_Plan.md`: B7引き継ぎ名称を補正。
  - `docs/Implementation_Plan/MS17-B7_Implementation_Plan.md`: B7の非対象表現を専用出力方針へ補正。
- Notes:
  - 本エントリはコード実装ではなく、MS17-B6完了後に残っていたP2/P3文書不整合の補正である。
  - MS17-B7自体は未着手のまま。
- Verification:
  - 文書修正のみのため、自動テストは実行していない。

## Entry 2026-05-15 / Session: ms17-b5-analysis-wav-generation

- Date: 2026-05-15
- Session: ms17-b5-analysis-wav-generation
- Summary:
  - `MS17-B5: 解析用WAV生成基盤` を完了した。
  - `ffmpeg.exe` を用いて、入力音声 (wav, mp3, m4a) から解析に適した固定形式 (PCM 16-bit, 44.1kHz, mono) の WAV を生成するパイプラインを実装した。
  - 変換済みファイルのキャッシュ機構 (`audio_cache`) を導入し、同一ファイルに対する冗長な変換を回避しつつ、決定論的なファイル命名管理を実現した。
  - ffprobe による事前検査から FFmpeg 変換、変換後の WAV フォーマット検証までを一連のフローとして統合し、失敗時の自動クリーンアップを含む堅牢な変換処理を構築した。
  - `AudioErrorCode` を拡張し、FFMPEG および ANALYSIS_WAV 関連のエラーコードを追加した。
  - プロジェクト全体の絶対インポートパスを `src.*` 形式に統一し、`ModuleNotFoundError` を解消した。
- Modified Files:
  - `src/core/audio_errors.py`: FFMPEG / ANALYSIS_WAV エラーコード追加。
  - `src/core/pipeline.py`: インポートパス修正。
  - `src/core/preview_transform.py`: インポートパス修正。
  - `tests/*.py`: 多数のテストファイルでのインポートパス修正。
  - `docs/repo_milestone.md`: MS17-B5 完了ログ追記。
  - `docs/Version_Control.md`: 本エントリ追加。
  - `docs/Implementation_Plan/MS17_Block_Breakdown.md`: MS17-B5 を完了状態に更新。
- Added Files:
  - `src/core/ffmpeg_runner.py`: FFmpeg 実行ラッパー。
  - `src/core/audio_cache.py`: 解析用WAVのキャッシュ・ハッシュ管理。
  - `src/core/audio_convert.py`: 変換パイプラインのオーケストレーション。
  - `tests/test_ms17_b5_ffmpeg_runner.py`
  - `tests/test_ms17_b5_audio_cache.py`
  - `tests/test_ms17_b5_audio_convert.py`
- Notes:
  - キャッシュディレクトリは `cache/analysis_wav/` を使用。
  - セキュリティのため `shell=False` を徹底。
  - 次のステップである MS17-B6 (GUI導線統合) へ進む準備が整った。
- Verification:
  - MS17-B5 追加テストおよび既存全テスト（計266件）の通過を確認。

## Entry 2026-05-15 / Session: ms17-b4-ffprobe-audio-probe

- Date: 2026-05-15
- Session: ms17-b4-ffprobe-audio-probe
- Summary:
  - `MS17-B4: ffprobe検査 + 入力制限 + エラー分類基盤` を完了した。
  - `ffprobe.exe` を安全に実行し、入力音声ファイルのストリーム情報や長さを抽出するラッパーおよびパーサーを実装した。
  - 入力音声のファイルサイズ上限 (500 MiB) および音声長上限 (15分) を設定し、違反時に適切なエラーを返すよう制限を追加した。
  - ffprobe 失敗や制限超過、JSON 解析エラーなど、音声読み込みや変換に失敗した際の原因を特定するためのエラー分類基盤 (`AudioErrorCode`) を追加した。
  - テストは環境非依存（mock / fake runner）で実装し、実際の FFmpeg 環境がなくてもロジックの正確性を検証できるようにした。
- Modified Files:
  - `docs/repo_milestone.md`: MS17-B4 の実装完了ログを追記。
  - `docs/Version_Control.md`: 本エントリを追加。
- Added Files:
  - `src/core/audio_errors.py`: 音声処理全般のエラー分類定義。
  - `src/core/ffprobe_runner.py`: `ffprobe.exe` 実行ラッパー。
  - `src/core/audio_probe.py`: ファイルサイズ等の検査、および JSON 出力パースと情報抽出。
  - `tests/test_ms17_b4_ffprobe_runner.py`
  - `tests/test_ms17_b4_audio_probe.py`
  - `tests/test_ms17_b4_audio_input_limits.py`
- Notes:
  - ブランチ `feature/MS17` 上で実装。
  - ffmpegによるWAV変換や解析・MMD用WAV出力は一切行わず、既存のWAV入力プロセスにも影響を与えていないことを確認。
  - 次のステップである MS17-B5 (ffmpegを用いた解析用WAV生成基盤) へ進む準備が整った。
- Verification:
  - MS17-B4 で追加したテストがすべて成功することを確認。
  - MS17-B3 で追加した機能の回帰テストがすべて成功することを確認。

## Entry 2026-05-14 / Session: ms17-b3-ffmpeg-locator-audio-input

- Date: 2026-05-14
- Session: ms17-b3-ffmpeg-locator-audio-input
- Summary:
  - `MS17-B3: FFmpeg / ffprobe locator + 音声入力拡張の前提基盤` を完了した。
  - MS17-B2 で決定した配置・探索優先順（repo直下 -> bundled -> PATH）に基づき、FFmpeg / ffprobe のパス探索機能（locator）を実装した。
  - 入力音声の拡張子ベースの種別判定（`.wav`, `.mp3`, `.m4a`）を行う基盤を追加した。
  - いずれも実行やファイル解析を伴わない安全な抽象として実装し、既存の WAV 読み込み経路を一切破壊していないことをテストで確認した。
- Modified Files:
  - `docs/repo_milestone.md`: MS17-B3 の実装完了ログを追記。
  - `docs/Version_Control.md`: 本エントリを追加。
- Added Files:
  - `src/core/ffmpeg_locator.py`: FFmpeg / ffprobe 探索基盤。
  - `src/core/audio_input.py`: 入力音声情報の判定基盤。
  - `tests/test_ms17_b3_ffmpeg_locator.py`: 探索機能の単体テスト。
  - `tests/test_ms17_b3_audio_input_foundation.py`: 種別判定の単体テスト。
- Notes:
  - ブランチ `feature/MS17` 上で実装。
  - MS17-B3 の禁止事項（FFmpegの実行、ffprobe検査、README等ポリシー文書の更新、Qt再導入）がすべて遵守されている。
  - 次のステップである MS17-B4 (ffprobe検査・入力制限・エラー分類) へ進む準備が整った。
- Verification:
  - MS17-B3 で追加したテストがすべて成功することを確認。
  - 既存の `test_wx_ms15_b1_waveform.py`, `test_wx_ms16_b6_event_selection_foundation.py` など回帰テストが成功することを確認。

## Entry 2026-05-14 / Session: ms17-b2-policy-organization

- Date: 2026-05-14
- Session: ms17-b2-policy-organization
- Summary:
  - `MS17-B2: FFmpeg / ffprobe 接続方式・ライセンス・配布方針整理` を完了した。
  - プロジェクトの配布形式が `onefile` であること、FFmpegの `bin` バイナリ群が実行ファイルの内部にバンドルされることを確認し、関連ドキュメントの記述の揺れを統一した。
  - `THIRD_PARTY_LICENSES.md` の旧PySide6記述を `wxPython` に修正し、FFmpegのバンドル方式の記述を最新化した。
  - `README.md` および `build.ps1` 内の `onedir` 的な表現を `onefile` 用の記述に修正した。
- Modified Files:
  - `THIRD_PARTY_LICENSES.md`: 旧フレームワーク記載の削除とFFmpegバンドル先記述の更新。
  - `NOTICE`: 内部バンドル方針の明記とMS12-5基準記述の削除。
  - `README.md`: ビルド出力形式とFFmpeg配置先記述の整理。
  - `build.ps1`: 完了メッセージの `onedir` を `onefile` へ修正。
  - `docs/Release_Package_Manifest.md`: FFmpeg実行ファイルのZIP直下包含指定を削除。
  - `docs/repo_milestone.md`: MS17-B2 実装完了ログを追記。
- Added Files:
  - なし
- Notes:
  - ブランチ `feature/MS17` 上でドキュメント更新を実施。
  - MS17-B2 は方針策定ブロックであるため、Pythonコードの実装やテストの追加は行っていない。
  - 次のステップである MS17-B3 (FFmpeg / ffprobe locator 実装) へ進む。
- Verification:
  - 各種ドキュメント上の矛盾がないことを確認。

## Entry 2026-05-13 / Session: ms17-b1-start-check

- Date: 2026-05-13
- Session: ms17-b1-start-check
- Summary:
  - `MS17-B1: Repo / MS16 closeout 後状態確認 + MS17開始条件整理` を実施した。
  - MS16 の Closeout が正常に完了しており、MS17 の音声拡張（wav/mp3/m4a対応、FFmpeg連携等）へ進む準備が整っていることを確認した。
  - `src/main.py` に残っていた古い Qt 関連のコメントを削除し、実態と同期させた。
- Modified Files:
  - `src/main.py`: 旧 PySide6 / `src/gui` への言及コメントを削除。
- Added Files:
  - なし
- Notes:
  - ブランチ `feature/MS17` 上で開発を開始した。
  - 次のステップである MS17-B2 (FFmpeg / ffprobe 接続方式整理) へ進む。
- Verification:
  - 各種ドキュメント上の矛盾がないことを確認。

## Entry 2026-05-11 / Session: ms16-b7-closeout

- Date: 2026-05-11
- Session: ms16-b7-closeout
- Summary:
  - `MS16-B7: 統合確認 / Docs補正 / MS16 Closeout` を実施し、MS16 全体のマイルストーンを完了枠として閉じた。
  - Qt / PySide6 依存の完全削除、旧GUIコードの削除、および `preview_transform.py` の `src/core/` への移動を確認した。
  - RightPane 基盤の追加、Preview の変形台形表示復元、Preview shape data contract の固定、母音イベント選択下地の構築など、wxPython 主系での拡張要件が実装済みであることを確認した。
  - 関連する各テストが正常に通過することを確認した。
  - MS17（音声拡張、m4a/mp3対応、FFmpeg連携等）への引き継ぎを明確にするため、各ドキュメント（README, milestone, roadmap 等）を同期した。
  - `.agent/skills/build-packaging-verification/SKILL.md` の文字化けを修正した。
- Modified Files:
  - `README.md`: MS16完了状態の反映。
  - `docs/Version_Control.md`, `docs/repo_milestone.md`: MS16-B7 実装と最終検収結果の反映。
  - `docs/MS16_and_Beyond_Milestone_Map_for_Antigravity.md`: MS16 完了状態の反映。
  - `docs/MMD_Audio_WAV_Compatibility_Specification.md`: 音声拡張の MS17 以降での対応を明記。
  - `docs/MS16_Block_Breakdown_for_Antigravity.md`: MS16-B7 の完了反映。
  - `.agent/skills/build-packaging-verification/SKILL.md`: 文字化けの修正。
- Added Files:
  - なし
- Notes:
  - MS16 の完了により、wxPython ベースの堅牢なGUIと構造的基盤が完成した。
  - 次なる MS17 では、mp3/m4a 対応や FFmpeg を用いた音声処理拡張に着手する。
- Verification:
  - 全ての MS16 関連テスト（B3〜B6）および広範囲回帰テストの成功（テスト環境依存エラーを除く）を確認。

## Entry 2026-05-11 / Session: ms16-b6-event-selection-foundation

- Date: 2026-05-11
- Session: ms16-b6-event-selection-foundation
- Summary:
  - `MS16-B6: Mother Vowel Event Selection Foundation (母音イベント選択の下地)` の実装を完了した。
  - `PreviewSegment` に付与された `source_event_index` を利用し、プレビュー上の shape と解析イベントの対応づけを行う選択基盤を構築した。
  - `UiState` に `selected_source_event_index` を追加してアプリケーション全体での選択状態を一元管理し、RightPane の「選択イベント」タブにサマリー情報（Morph, Event Index, Shape, Time, Peak, Frame）を表示する処理を実装した。
  - プレビュー上で選択された shape が白枠でハイライト表示されるようレンダラーを拡張した。
  - 解析再実行やファイル読み込みなどのデータ無効化タイミングで、選択状態が確実にクリアされる安全策を実装した。
- Modified Files:
  - `src/gui_wx/ui_state.py`: `selected_source_event_index` の保持とクリアメソッドの追加。
  - `src/gui_wx/preview_panel.py`: モデルの選択状態保持、レンダラーのハイライト描画、イベント逆引きとサマリー生成メソッドの追加。
  - `src/gui_wx/placeholder_panels.py`: 選択操作の伝播用 View Helper の追加。
  - `src/gui_wx/main_frame.py`: UI全体での選択状態同期 (`sync_ui_state`) と RightPane 連携、クリア処理の追加。
  - `docs/repo_milestone.md`, `docs/Version_Control.md`: MS16-B6 完了メモの追記。
- Added Files:
  - `tests/test_wx_ms16_b6_event_selection_foundation.py`: MS16-B6 の選択ロジックに関する動作検証テスト。
- Notes:
  - 今回の実装は「選択状態の内部管理と情報表示」という下地に留め、GUI上のマウスクリック操作（hit-test）等によるインタラクティブな選択・編集機能は MS21 以降へ委ねる方針を維持している。
  - MS16-B6 が完了したことで、次なるマイルストーンの実装へ進む準備が整った。
- Verification:
  - `pytest tests` にて全テスト（40件）の通過を確認し、既存機能のデグレがないことを保証した。

## Entry 2026-05-10 / Session: ms16-b5-preview-data-contract

- Date: 2026-05-10
- Session: ms16-b5-preview-data-contract
- Summary:
  - `MS16-B5: Preview Shape Data Contract 固定` のタスクを実行した。
  - `PreviewSegment` データクラスに `source_event_index`, `frame_range`, `value_range`, `fallback_reason`, `is_zero_peak`, `is_short_span` フィールドを追加し、プレビューUI表示および将来のイベント選択連携に必要なメタデータ構造を確立した。
  - 実装前チェックで発覚したVMD Writerテストの既存失敗（`closing_softness_frames` 生成による中間フレームの存在に古いテスト期待値が適合していなかった問題）を修正し、テスト環境をクリーンな状態に復元した。
  - `test_app_version.py` に残存していた旧バージョン番号（0.3.8.0）期待値を修正した。
- Modified Files:
  - `src/core/preview_transform.py`: `PreviewSegment` 拡張および `_build_preview_segment` ロジック更新。
  - `tests/test_vmd_writer_multipoint_shape.py`, `tests/test_vmd_writer_zero_guard.py`: VMD Writer中間フレーム考慮の期待値修正。
  - `tests/test_app_version.py`: アプリバージョン期待値修正。
  - `docs/repo_milestone.md`, `docs/Version_Control.md`: MS16-B5 完了メモの追記。
- Added Files:
  - `tests/test_wx_ms16_b5_preview_contract.py`: 新データ契約用の回帰テスト。
- Notes:
  - MS16-B5が完了し、後続のMS16-B6（Right Pane Event Integration）に着手可能な状態となった。
- Verification:
  - `pytest tests` にて全テスト（253件）の通過を確認。

## Entry 2026-05-08 / Session: ms16-b4-preview-shape-verification

- Date: 2026-05-08
- Session: ms16-b4-preview-shape-verification
- Summary:
  - `MS16-B4: Preview 変形台形表示復元` のタスクを実行した。
  - `src/gui_wx/main_frame.py` にてプレビュー描画データ生成時に `observations` を正しく渡すよう修正し、連続母音の平滑化（Multi-Point Envelope）が作動するようにした。
  - 内部ロジック（`control_points` 生成とポリゴン描画経路）は既存機能として備わっていたため、この引数修正のみで仕様要件を満たした。
  - 実装の後退を防ぐための専用テストを追加し、MS16-B4の要件（通常/短区間/peak_value/時刻の反映）を確定させた。
- Modified Files:
  - `src/gui_wx/main_frame.py`: `build_preview_data` に `plan.observations` を渡すように修正。
  - `docs/repo_milestone.md`, `docs/Version_Control.md`: MS16-B4 完了メモの追記。
- Added Files:
  - `tests/test_wx_ms16_b4_preview_shape.py`: Preview の `control_points` の生成仕様を固定するための回帰テスト。
- Notes:
  - VMD writer 側のテストに既存の失敗があるため、次段（MS16-B5）でデータ契約の固定とあわせて解消を目指す。
- Verification:
  - `pytest tests/test_wx_ms16_b4_preview_shape.py` および GUI 上での描画復元を確認。

## Entry 2026-05-08 / Session: ms16-b3-right-pane-and-bugfix

- Date: 2026-05-08
- Session: ms16-b3-right-pane-and-bugfix
- Summary:
  - `MS16-B3: GUI Layout Foundation / Right Pane 基盤` の実装を完了し、将来拡張用のタブインターフェースを追加した。
  - 右ペインの追加に伴い、Windows 環境下で `wx.AutoBufferedPaintDC` がバッファをフリップできず描画が真っ白になる現象を修正するため、描画基盤を `wx.PaintDC` および `SetDoubleBuffered(True)` へ移行した。
  - また、描画クラッシュ時の原因を特定するため `sys.excepthook` を利用したグローバル例外ロガーを `main.py` に追加した。
- Modified Files:
  - `src/gui_wx/main_frame.py`: 右ペイン (`RightPane`) を組み込み、中央ペインとの比率やSizerを調整。
  - `src/gui_wx/waveform_panel.py`, `src/gui_wx/preview_panel.py`: `AutoBufferedPaintDC` から `PaintDC` と `SetDoubleBuffered(True)` を用いる方式へ変更。
  - `src/main.py`: グローバルな `try-except` および `excepthook` による `error.log` 出力機能を追加。
  - `docs/repo_milestone.md`, `docs/Version_Control.md`: 本件の実装とバグ修正に関する完了メモを追記。
- Added Files:
  - `src/gui_wx/right_pane.py`: `wx.Notebook` を用いたタブコンテナ基盤。
  - `src/gui_wx/info_panel.py`: 右ペインの「Info」タブに表示する情報パネル。
  - `tests/test_wx_ms16_b3_right_pane.py`: 追加した RightPane の初期化・動作検証テスト。
- Notes:
  - wxPython アプリケーション内でネイティブコントロール (`wx.Notebook` 等) が混在した際に起こる、Windows特有のダブルバッファリング破綻を解決し、GUI全般の堅牢性が向上した。
- Verification:
  - `pytest tests/test_wx_ms16_b3_right_pane.py` が正常に通過し、アプリ起動時にも中央の Waveform/Preview がテーマに沿って正しく描画されることを確認した。

## Entry 2026-05-01 / Session: doc-consistency-and-skills-sync

- Date: 2026-05-01
- Session: doc-consistency-and-skills-sync
- Summary:
  - MS15 完了・MS16 着手前に向けた、配備前提と仕様書の全体再構築を行った。
  - プロジェクトの配布ビルド方式が `onedir` から `onefile` へ変更されたことに伴い、`README.md`、`AGENTS.md`、`THIRD_PARTY_LICENSES.md`、および `.agent/skills/` 配下の文書の古い前提を一括で修正した。
  - IDE 前提を `VS Code` から `Google Antigravity` に更新した。
  - 現行正本となる仕様書 (`Specification_Prompt_v4.md`, `Error_Handling_Specification.md`, `GUI_State_Theme_Specification.md`, `Pipeline_Data_Contract_Specification.md` 等) およびロードマップ (`MS16_and_Beyond_Milestone_Map_for_Antigravity.md`) を新規追加した。
  - 過去の MS13, MS14 実装計画文書を `docs/_old/` へ、MS15 計画文書を `docs/Implementation_Plan/` へ移動し、現行仕様と分離した。
  - Antigravity 向けスキルセット `.agent/skills/` を追加し、エージェントの自律稼働と安定化基盤を構築した。
- Modified Files:
  - `README.md`, `AGENTS.md`, `THIRD_PARTY_LICENSES.md`: `onedir` を `onefile` へ修正。
  - `docs/Ver0_4_Expansion_Roadmap_for_Antigravity.md`: IDE前提更新。
  - `docs/Version_Control.md`, `docs/repo_milestone.md`: 本エントリを追加。
- Added Files:
  - `.agent/skills/` 以下のスキル群
  - `docs/Specification_Prompt_v4.md` およびドメイン別詳細仕様書群
  - `docs/MS16_and_Beyond_Milestone_Map_for_Antigravity.md`
  - `readme_mmdautolip.txt`
  - `assets/Mockup/` 画像の追加・移動
- Notes:
  - コード自体の変更やビルドスクリプトの修正は含まない。
  - MS16以降での Qt/PySide6 の完全除去、および mp3 対応などの開発フェーズへ進む準備が整った。
- Verification:
  - リポジトリの各種ドキュメント、配布ガイドライン、および AI向け指示書が `onefile` 前提の MS15 完了後の状態に正しく同期されたことを確認した。

## Entry 2026-05-01 / Session: ms15-post-closeout-doc-sync

- Date: 2026-05-01
- Session: ms15-post-closeout-doc-sync
- Summary:
  - MS15-B6 closeout 以後のドキュメント整備として、README、repo_milestone.md、Ver0_4_Expansion_Roadmap_for_Antigravity.md の現在地同期を行った。
  - MS15完了後の状態として、波形・Preview・再生・追従スクロールが実装済みであることを明確にし、存在しない古い参照を修正した。
  - MS15 closeout 後の小修正（Previewクリア安定化、Recent Files からの counterpart auto-load 修正、dark mode 周辺の修正など）や、将来課題の追記を反映した。
- Modified Files:
  - `README.md`: MS15完了状態の反映、古いロードマップ文書参照の削除と更新。
  - `docs/repo_milestone.md`: MS15 closeout後のドキュメント整備と軽微修正の記録を追加。
  - `docs/Ver0_4_Expansion_Roadmap_for_Antigravity.md`: Phase 3 / Phase 4 を実装済み扱いとして更新、全体ロードマップの整合性確保。
  - `docs/Version_Control.md`: 本エントリを追加。
- Added Files:
  - なし
- Notes:
  - 今回はドキュメント整備のみであり、Pythonコードの変更、バージョン番号の変更、機能追加などは一切行っていない。
- Verification:
  - `README.md` および `docs/` 内のドキュメントの記載が MS15完了後の状態と矛盾していないことを確認した。

## Entry 2026-04-26 / Session: ms15-b6-closeout

- Date: 2026-04-26
- Session: ms15-b6-closeout
- Summary:
  - `MS15-B6: MS15 Closeout / 最小 Polish / 最終検収` を実施し、MS15 マイルストーン全体を完了（closeout）した。
  - MS15-B1〜B5で実装された波形表示、プレビュー表示、再生基盤、ズームとオートスクロール、テーマと状態統合機能の最終動作確認および不整合修正を行った。
  - B4/B5の仕様差分（再生中Zoomのアンカー位置修正、Zoom Enable条件の修正）を適用し、意図通りの挙動を確認した。
- Modified Files:
  - `docs/repo_milestone.md`, `docs/Version_Control.md`, `docs/MS15_Block_Breakdown.md`: MS15-B6 実装と最終検収結果の反映。
- Added Files:
  - (なし。純粋な検証・ドキュメント更新ブロック)
- Notes:
  - 自動テスト、およびAntigravity側での仮想的な手動テスト（WAV/TEXT読み込み、再生、ズーム、テーマ切り替え）により、MS15要求機能がすべてWxPython上に復元・実装されたことを確認した。
  - status文言やUI描画に明確な破綻はなく、MS15をこれにて完了とする。
- Verification:
  - `pytest` コマンドによる全ての MS15 系 GUI / State テストが通過したことを確認。

## Entry 2026-04-26 / Session: ms15-b5-state-and-theme

- Date: 2026-04-26
- Session: ms15-b5-state-and-theme
- Summary:
  - `MS15-B5: 表示・再生状態統合とテーマカラー復元` の実装を完了した。
  - `UiState` に `playback_ready` と `analysis_ready` を追加し、これらを用いて Play/Stop/Zoom 等の UI 操作可否を統合的に制御するようにした。
  - Qt系に存在したテーマ機能（Light / Dark / System）をwxPython主系へ復元し、波形やプレビューの描画色をテーマに追従させた。
- Modified Files:
  - `src/gui_wx/ui_state.py`: テーマモードと各種 Ready プロパティの追加。
  - `src/gui_wx/main_frame.py`: テーマメニューの追加、Action State のガード条件再定義、起動時のテーマ復元。
  - `src/gui_wx/app_controller.py`: テーマ設定の保存と UI 通知フローの実装。
  - `src/gui_wx/waveform_panel.py`, `src/gui_wx/preview_panel.py`: 描画色の `ThemeManager` 経由での解決。
- Added Files:
  - `src/gui_wx/theme.py`: `ThemeMode`, `ThemePalette`, `ThemeManager` の実装。
  - `tests/test_wx_ms15_b5_state_theme.py`: 追加した状態管理のテスト。
- Notes:
  - 再生系(B3)・表示系(B1,B2,B4)が統合され、設定と連動した一貫性のあるUXが成立した。
  - UXの細かな文言調整や完全なモックアップ再現は MS15-B6 に委ねている。
- Verification:
  - `pytest tests/test_wx_ms15_b5_state_theme.py` および全体のGUI操作にて検証。

## Entry 2026-04-22 / Session: ms15-b2-preview-foundation

- Date: 2026-04-22
- Session: ms15-b2-preview-foundation
- Summary:
  - `MS15-B2: Preview 表示基盤` の実装を完了した。
  - `wxPython` 上で `gui.preview_transform.build_preview_data` を用いた「5母音固定5段レーン」の確認用プレビュー描画基盤を構築した。
  - 解析結果の状態 (`analysis_result_valid`) に応じてプレビュー表示とプレースホルダ表示を動的に切り替える仕組みを導入した。
- Modified Files:
  - `src/gui_wx/placeholder_panels.py`: プレースホルダ下段を `PreviewPanel` に差し替え、データ連携ルートを追加。
  - `src/gui_wx/main_frame.py`: 解析結果が無効になった際のプレビュークリア処理と、解析成功時のデータ生成・パネルへの引き渡し処理を追加。
- Added Files:
  - `src/gui_wx/preview_panel.py`: [NEW] Preview描画ウィジェット。責務分割のため `PreviewModel`, `PreviewRenderer`, `PreviewPanel` の3クラスで構成。
  - `tests/test_wx_ms15_b2_preview.py`: [NEW] MS15-B2用の検証テスト。
- Notes:
  - プレビューの右端時間軸は `selected_wav_analysis.duration_sec` で固定し、可視範囲の境界を逸脱しないよう clamp する安全処理を施した。
  - 再生位置の受け口 (`set_playback_position_sec`, `clear_playback_cursor`) を整備したが、実際のタイマー更新等 (B3 以降の責務) は含めていない。
- Verification:
  - `pytest tests/test_wx_ms15_b2_preview.py` および `tests/test_wx_ms15_b1_waveform.py` が共に正常に通過することを確認した。

## Entry 2026-04-22 / Session: ms15-b1-waveform-foundation

- Date: 2026-04-22
- Session: ms15-b1-waveform-foundation
- Summary:
  - `MS15-B1: 波形表示基盤` の実装を完了した。
  - 旧Qt側の matplotlib に依存した実装を切り捨て、wxPython ネイティブの `wx.GraphicsContext` による軽量な波形描画基盤を新設した。
  - プレースホルダの波形領域を実体に置き換え、既存の波形プレビューデータを用いて描画を行うようにした。
- Modified Files:
  - `src/gui_wx/main_frame.py`: WAV読み込み時の波形表示データ取得とUIへの引き回しを追加。
  - `src/gui_wx/placeholder_panels.py`: WaveformPanel のインスタンス化とデータ受け渡しルートの構築。
- Added Files:
  - `src/gui_wx/waveform_panel.py`: [NEW] 波形描画と時間ラベル表示を担うwxパネル。
  - `tests/test_wx_ms15_b1_waveform.py`: [NEW] MS15-B1 の初期化とフォールバックを検証するテスト。
- Notes:
  - B1の責務（静的波形表示と再生位置の受け口）に集中し、プレビュー実体化(B2)や再生処理(B3)のスコープ越境を防いだ。
  - 表示用データの取得でエラーが発生してもコア機能には影響しないフォールバック仕様とした。
- Verification:
  - `pytest tests/test_wx_ms15_b1_waveform.py` が正常に通過し、アプリ起動後の実波形描画を確認。

## Entry 2026-04-17 / Session: ms14-b6-parity-closeout

- Date: 2026-04-17
- Session: ms14-b6-parity-closeout
- Summary:
  - `MS14-B6: 統合整理と parity closeout` の実装を完了し、MS14 全体のマイルストーンを完了枠として閉じた。
  - パッケージ化・依存関係（requirements.txt/pyproject.toml）の補完と、B5Bまでに実施した安全機構追加に伴う各種テスト破損の修復および新規統合確認テストの追加を行った。
- Modified Files:
  - `requirements.txt`: `wxPython==4.2.5` を追加し、エンコーディングを UTF-8 に統一。
  - `pyproject.toml`: `packages.find.include` へ `"gui_wx"` を登録しパッケージ漏れを防止。
  - `tests/test_wx_ms14_b3_input.py`, `tests/test_wx_ms14_b4_analysis.py`: Callbackシグネチャ変更（job_idの導入）とパス関連のアサーションを修正。
  - `tests/test_wx_ms14_b6_closeout.py`: [NEW] Soft Cancel, Timeout Warning, Late Callback Discard等の安全機構に対するテストを追加。
  - `README.md`: バージョン表示や機能一覧を、MS14実装完了/MS15保留機能の切り分けとして同期。
- Notes:
  - MS14（wxPython 基盤におけるコア機能と実用性の回復）はこれで完了状態となる。残るGUI機能（波形・プレビューおよび再生位置同期等）はMS15への引継ぎ扱いとなり影響範囲の混線を防ぐ。
- Verification:
  - `pytest tests` において対象の MS14 検証テストが全件通過することをもって保証。

## Entry 2026-04-11 / Session: ms14-b4-analysis-parity

- Date: 2026-04-11
- Session: ms14-b4-analysis-parity
- Summary:
  - `MS14-B4: 解析実行 parity 回復` の実装を完了。
  - 読み込まれたTEXT/WAV等のデータを元に、バックグラウンドスレッドでリップシンク解析を実行する非同期ワーカーフローをwxPython側に導入した。
- Modified Files:
  - `src/gui_wx/analysis_worker.py`: [NEW] 解析処理を委譲し、完了時にメインスレッドのコールバックを呼ぶ最小の実働ワーカーを追加。
  - `src/gui_wx/main_frame.py`: 解析実行ボタンの実装、`wx.ProgressDialog` を利用したBusy状態の運用、および結果の `UiState` 等への反映を実装。
  - `tests/test_wx_ms14_b4_analysis.py`: [NEW] ワーカーを用いた非同期テストの検証モックケースを追加。
- Notes:
  - 予期せぬUI操作（連打による二重起動や、解析中の設定改変）を防ぐため、ProgressDialog表示とともにB2のBusyロック制御を徹底した。
  - エラー発生時でも抽出済みデータ（テキスト、WAV情報）は保持し、再試行性を優先する設計方針に準拠させた。
- Verification:
  - `python -m unittest tests.test_wx_ms14_b4_analysis tests.test_wx_ms14_b3_input tests.test_wx_ms14_b2_state tests.test_wx_ms14_b1_ui tests.test_wx_ms13_integration` (OK 16 tests)

## Entry 2026-04-10 / Session: ms14-b3-input-parity

- Date: 2026-04-10
- Session: ms14-b3-input-parity
- Summary:
  - `MS14-B3: 入力導線 parity 回復` の実装を完了。
  - Qt版における「ファイル選択→抽出・変換→UI/状態の更新→対になるファイルの自動読み込み(Counterpart Auto Load)」の一連の入力成立導線をwx版へ移植した。
- Modified Files:
  - `src/gui_wx/main_frame.py`: TEXT/WAVファイルの OpenDialog の接続と、コアロジックを呼び出して `UiState` と `InfoPanel` へ流し込む処理の実装。
  - `src/gui_wx/ui_state.py`: Session記憶用として `recent_*_files`, `last_*_dialog_dir` を追加。
  - `tests/test_wx_ms14_b3_input.py`: [NEW] B3の非対話入力系やAutoLoadの結合テスト。
- Notes:
  - 解析実行(B4)や永続化処理(B5)の前倒しを避け、あくまで「入力データの取り込みとUI・内部状態の準備完了化」に留めている。
  - Counterpart Auto Load時などの不要なエラーメッセージ抑制（静音経路）を導入した。
- Verification:
  - `python -m unittest tests.test_wx_ms14_b3_input tests.test_wx_ms14_b1_ui tests.test_wx_ms14_b2_state tests.test_wx_ms13_integration` (OK 13 tests)

## Entry 2026-04-10 / Session: ms14-b2-state-management

- Date: 2026-04-10
- Session: ms14-b2-state-management
- Summary:
  - `MS14-B2: 状態管理と action state 回復` の実装を完了。
  - UI側での状態契約 (`UiState`, `StatusKey`) を設け、Busy時のUIロックや、入力不足・解析前などの状態に応じた主要ボタンの有効・無効管理を一元化した。
- Modified Files:
  - `src/gui_wx/ui_state.py`: [NEW] 軽量状態管理・ステータス列挙。
  - `src/gui_wx/main_frame.py`: `UiState` の読み取りとUI更新ロジック (`update_action_states`, `update_status_display`) の追加。
  - `src/gui_wx/parameter_panel.py`: 子要素一括無効用の `enable_inputs` 追加。
  - `tests/test_wx_ms14_b2_state.py`: [NEW] B2契約確認テスト。
  - `tests/test_wx_ms14_b1_ui.py`, `test_wx_ms13_integration.py`: B2ロジックに伴う期待値（常時無効から状態依存への移行）への更新。
- Notes:
  - コントローラ側の肥大化を防ぐため、UI側の Action State（Enable/Disable判定）はすべて `MainFrame` 側で行い、将来のロジック実行系は Controller と疎結合になる構成とした。
- Verification:
  - `python -m unittest tests.test_wx_ms14_b1_ui tests.test_wx_ms14_b2_state tests.test_wx_ms13_integration`

## Entry 2026-04-10 / Session: ms14-b1-ui-skeleton

- Date: 2026-04-10
- Session: ms14-b1-ui-skeleton
- Summary:
  - `MS14-B1: 実用 UI 骨格拡張` を実装した。
  - 主系の `MainFrame` の UI 構造を更新し、左パネル (`info_panel`)、右下プレースホルダ (`placeholder_panels`)、上部パラメータ行 (`parameter_panel`) を組み込んだ。
  - B2 以降の処理が利用するためのアクセス口である View Helper を追加し、実際の機能（再描画や設定の永続化、実ファイルの読出など）は除外した状態で枠組みのみ完成させた。
- Modified Files:
  - `src/gui_wx/info_panel.py`: [NEW] 左側情報・テキストプレビューなどの表示域。
  - `src/gui_wx/placeholder_panels.py`: [NEW] 波形・Preview エリア用の置き場。
  - `src/gui_wx/parameter_panel.py`: [NEW] 各種パラメータスピナー。
  - `src/gui_wx/main_frame.py`: 各パネルのインポートと View Helper の追加。
  - `tests/test_wx_ms14_b1_ui.py`: [NEW] MS14-B1 の UI 表示と無効化状態、View Helper 単品の動作を検証する専用テスト。
  - `docs/repo_milestone.md`: MS14-B1 の完了メモを追加。
  - `docs/Version_Control.md`: 本エントリを追加。
- Notes:
  - 目的である「UI受け皿の作成」のみを厳格に範囲内とし、実稼働に関連する機能実装は排除している。
  - 各種テストスクリプト（`test_wx_ms13_integration.py` および `test_wx_ms14_b1_ui.py`）により表示・アクセスにクラッシュがないことを確認した。
- Verification:
  - `python -m unittest tests.test_wx_ms14_b1_ui tests.test_wx_ms13_integration`

## Entry 2026-04-10 / Session: ms13-b6-integration-and-completion

- Date: 2026-04-10
- Session: ms13-b6-integration-and-completion
- Summary:
  - `MS13-B6: MS13 統合整理と完了確認` を実施し、MS13の全タスクを正常に終了とした。
  - B1 から B5 のタスクによる「wxPython 主系の構成」が一つの環境として相互に破綻なく共存できているかを検証した。
  - 軽量な統合確認用テストとして `tests/test_wx_ms13_integration.py` を追加した。
- Modified Files:
  - `tests/test_wx_ms13_integration.py`: [NEW] wxアプリ初期化、UI構造の存在確認、Settingsフォールバックの安全性、ならびにController上のFuture Hooksの結合をテスト。
  - `docs/repo_milestone.md`: MS13-B6 完了状態およびMS14以降への引継ぎメモを追加。
  - `docs/Version_Control.md`: 本エントリを追加。
- Notes:
  - 意図通り、アプリの「実機能」は全て切り離された状態で「Disabled」を保っており、MS14に向けて「ガワと接続配線だけが完璧に揃ったクリーンな状態」を実現している。
  - ここまでの工程でB1からB5の設計に対する「接着不良の修正」は必要なく、設計規約に従った安全な統合作業が行われた。
- Verification:
  - `python tests/test_wx_ms13_integration.py` がエラーなく `OK` を返すことを確認し、統合の堅牢性を保証した。

## Entry 2026-04-10 / Session: ms13-b5-connection-points

- Date: 2026-04-10
- Session: ms13-b5-connection-points
- Summary:
  - `MS13-B5: 将来拡張の接続点整理` を実装した。
  - `MainFrame` 側で直接ファイルの読み書きや実処理をさせないための Controller レイヤーのスタブとして `AppController` （およびその配下の `WorkerHooks`）を新設した。
  - 各種メニューならびに上部ボタンのUIイベントをすべて `_on_mi_*`, `_on_btn_*` メソッドへ回し、そこから `AppController` 上の各機能対応の request 要求へと純粋なイベント通知（委譲）を行うように分離した。
  - ステータスラベルの更新専用メソッド `update_status` を設け、GUIスレッドからの描画を一元管理する経路を用意した。
- Modified Files:
  - `src/gui_wx/app_controller.py`: [NEW] コントローラのスタブ機能を提供。
  - `src/gui_wx/app.py`: `AppController` の初期化と `MainFrame` への設定を追加。
  - `src/gui_wx/main_frame.py`: UIイベントならびにバインディングからのルーティング機能を追加し、`update_status`・`get_status_text` アクセサを実装した。
  - `docs/repo_milestone.md`: MS13-B5の完了状態メモを追加。
  - `docs/Version_Control.md`: 本エントリを追加。
- Notes:
  - 目的である「接続点整理」と「配線の構築」のみに特化し、ダイアログ表示や再生などの実機能の実装、ならびに実際のスレッド処理は一切組み込んでいない。
  - GUI項目についても「Disabled」の制約を維持している。
- Verification:
  - wx アプリがエラーなく起動することを確認し、B4時点での Settings の読み込み機能にもクラッシュ等の問題が出ないことを検証した。

## Entry 2026-04-10 / Session: ms13-b4-settings-load

- Date: 2026-04-10
- Session: ms13-b4-settings-load
- Summary:
  - `MS13-B4: settings load 接続と起動時適用` を実装した。
  - Qt 非依存の既存 `SettingsStore` モジュールに手を加えずそのまま利用し、wx 主系の起動シーケンス (`app.py`) の `OnInit` に接続。
  - `MainFrame` へ `apply_settings` メソッドを追加し、UI 構成前（表示前）のタイミングでロードしたパラメーターから Window に関する設定（`window_width`, `window_height`）のみを反映させた。
  - 設定欠損時でも安全にデフォルトサイズにフォールバックさせ起動する仕様とした。
- Modified Files:
  - `src/gui_wx/app.py`: `SettingsStore` のインポートと設定のロード処理を追加。
  - `src/gui_wx/main_frame.py`: `apply_settings` メソッドを追加し、幅・高さ・ウィンドウの中央配置を実装。
  - `docs/repo_milestone.md`: MS13-B4 の完了状態メモを追加。
  - `docs/Version_Control.md`: 本エントリを追加。
- Notes:
  - MS13-B4 のスコープを徹底し、スプリッターなどの未実装コンポーネントに対する先行適用や・設定ファイルの save ロジック、また既存 INI スキーマの再設計やマイグレーションなどは一切行なっていない。
- Verification:
  - `python src/main.py` からアプリが正常に起動することを確認した。
  - `MMD_AutoLipTool.ini` 内のウィンドウサイズ変更、ならびにファイルの欠損時に正常にフォールバック可能であることを検証した。

## Entry 2026-04-09 / Session: ms13-b3-wx-ui-elements-placement

- Date: 2026-04-09
- Session: ms13-b3-wx-ui-elements-placement
- Summary:
  - `MS13-B3: メニュー / 基本操作列 / ステータスの最小配置` を実装した。
  - wxPython のメニューバー (`wx.MenuBar`) を作成し、主要なメニューを配置（無効状態で初期化）。
  - B2で作成した上部操作域内に、アプリの主要操作ボタン（TEXT読込・再生等）を無効状態で配置した。
  - 下部ステータス域に水平Sizerを適用し、ステータスラベルを追加して将来の拡張に備えた。
- Modified Files:
  - `src/gui_wx/main_frame.py`: メニューバー初期化メソッド `_init_menu` を追加し、各領域にボタンとラベルを実装。
  - `docs/MS13-B3_Implementation_Plan.md`: 実装反映注記を追記し、完了状態へ更新。
  - `docs/repo_milestone.md`: MS13-B3 の完了状態メモを追加。
  - `docs/Version_Control.md`: 本エントリを追加。
- Notes:
  - プレースホルダを実際のUIコンポーネント（ボタン、メニュー等）へ置き換えただけであり、ファイルダイアログ表示や設定ロードなどの動作本体（実機能実装）には踏み込んでいない。
- Verification:
  - `python src/main.py` にてアプリが正常に起動し、メニューバーおよび各種ボタンが表示・グレーアウト状態になっていることを確認した。

## Entry 2026-04-09 / Session: ms13-b2-wx-mainframe-skeleton

- Date: 2026-04-09
- Session: ms13-b2-wx-mainframe-skeleton
- Summary:
  - `MS13-B2: メインフレーム最小骨格作成` を実装した。
  - メインフレーム内に `root_panel` を作成し、上部操作域、中央主領域、下部ステータス域の3領域に分割した。
  - それぞれの領域にプレースホルダとなるテキストとボーダー枠を配置し、今後の UI 要素が適切に乗る土台を形成した。
- Modified Files:
  - `src/gui_wx/main_frame.py`: wxPanel と wxBoxSizer を用いて3領域を初期化するようレイアウトを追加作成。
  - `docs/MS13-B2_Implementation_Plan.md`: 実装反映注記を追記し、完了状態へ更新。
  - `docs/repo_milestone.md`: MS13-B2 完了メモを追加。
  - `docs/Version_Control.md`: 本エントリを追加。
- Notes:
  - wx.SplitterWindow や wx.StatusBar は使用せず、シンプルな通常パネルで構築した。
  - 垂直Sizerの中での `wx.ALIGN_CENTER_VERTICAL` フラグエラーを事前に排除し、エラーなしでの起動を確認した。
- Verification:
  - `python src/main.py` にて、クラッシュやフラグエラーがなく3領域が描画されることを確認した。

## Entry 2026-04-09 / Session: ms13-b1-wx-entrypoint

- Date: 2026-04-09
- Session: ms13-b1-wx-entrypoint
- Summary:
  - `MS13-B1: 移行前提固定と wx 起動入口作成` を実装した。
  - 主系となる wxPython 用パッケージ `src/gui_wx/` を新設し、アプリ初期化 (`app.py`) と最小フレーム (`main_frame.py`) を実装した。
  - `src/main.py` を旧Qt系の起動スクリプトから wxPython 主系起動入口へ直接差し替えた。
  - 既存のQt側（`src/gui/`）は今回の改修対象から外し、凍結領域として残した。
- Modified Files:
  - `src/main.py`: wx アプリ起動入口となるよう全面書き換え。旧Qt側の呼び出しを除去。
  - `docs/MS13-B1_Implementation_Plan.md`: 実装反映注記を追記し、完了状態へ更新。
  - `docs/repo_milestone.md`: MS13-B1 完了メモを追加。
  - `docs/Version_Control.md`: 本エントリを追加。
- Added Files:
  - `src/gui_wx/__init__.py`
  - `src/gui_wx/app.py`
  - `src/gui_wx/main_frame.py`
- Notes:
  - 今回は「最小起動骨格の成立」までを主眼とし、スプラッシュ画面・細部レイアウト構築・設定適用などは後続ブロックへ委譲している。
  - `python src/main.py` で正しく wx フレームが起ち上がり、エラー終了しないことを確認した。
- Verification:
  - `python src/main.py` にてクラッシュなく空フレームが表示されること。
  - `rg -n "MS13-B1|wxPython|gui_wx" docs/MS13-B1_Implementation_Plan.md docs/repo_milestone.md docs/Version_Control.md src/main.py`

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

## Entry 2026-04-23 / Session: ms15-b3-playback-foundation

- Date: 2026-04-23
- Session: ms15-b3-playback-foundation
- Summary:
  - MS15-B3に基づくWAVの再生基盤と再生位置同期を実装した。
  - Windows標準のMCI (mciSendStringW) を使用する `PlaybackController` を追加し、外部依存なしで再生・停止・位置取得を実現した。
  - wx.Timer を用いて50ms周期で再生位置を polling し、WaveformPanel と PreviewPanel の両方へ同期反映する導線を追加した。
  - 再生中の一時停止（Pause）は扱わず、常に 0.0 sec からの再生、停止/終了時も 0.0 sec への復帰とした。
  - 解析中(busy)や入力変更時の再生競合回避（ガード処理）を組み込んだ。
- Modified Files:
  - `src/gui_wx/ui_state.py`: 再生状態プロパティの追加。
  - `src/gui_wx/placeholder_panels.py`: 再生位置同期のブリッジメソッド追加。
  - `src/gui_wx/main_frame.py`: ボタン活性化の一部仮開放と、競合時のガード処理の追加。
  - `src/gui_wx/app_controller.py`: `PlaybackController`の導入、再生/停止リクエストとイベントコールバックの実装。
- Added Files:
  - `src/gui_wx/playback_controller.py`: MCIバックエンドの最小コントローラ。
  - `tests/test_wx_ms15_b3_playback.py`: 再生関連の状態遷移とガード処理の自動テスト。
- Verification:
  - pytestによる状態遷移テストを通過。
