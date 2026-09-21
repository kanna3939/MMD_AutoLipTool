# MMD_AutoLipTool GUI整備・機能拡張 マイルストーン一覧

## 2026-09-19 / MS28-B2 Long-Vowel Boundary Repair 実装・自動検証

- 対象:
  - MS28-B1の実装状態を維持したまま、隣接long sourceの境界契約、同一frame handoff、R06/R07/R13/R14回帰条件を実装
- 実施内容:
  - `src/core/pipeline.py`へ、`S=T`保持、`S<T`補修、`S=P=T+1`のpeak補修、その他の`S>T`無補修というB2の4分岐を実装した。
  - raw resolverとpipeline経由のcanonical zero / fail-closed / 非衝突`S=P`を、`tests/test_ms22_b2_long_vowel_resolver.py`および`tests/test_ms21_b3_pipeline_preview_integration.py`へ回帰として追加した。
  - B2のproduction code / test code以外の版数、依存関係、spec / build設定、runtime JSON / INI、配布成果物は変更していない。
- 検証:
  - B2 resolver **39 passed**、pipeline / Preview **4 passed**、adapter・spec **9 passed・21 subtests**。
  - 全suite **1100 passed、4 skipped、88 subtests、process exit code 0**。`git diff --check`もprocess exit code `0`。
  - 実Whisperによるユーザー提供ファイルの再解析、native GUI、実MMD、EXE、buildは今回実施していない。
- 判定:
  - MS28-B2のcore実装と自動回帰検証は完了・検証済み。実Whisper / GUI / MMD / EXE / buildは未検証として継続する。
  - MS27の完了状態、MS28の独立修正実装トラック、Ver.1.0の版数・配布境界は変更しない。
- 変更範囲:
  - production code: `src/core/pipeline.py`
  - test code: `tests/test_ms22_b2_long_vowel_resolver.py`、`tests/test_ms21_b3_pipeline_preview_integration.py`
  - 本エントリで、MS28-B1 / B2計画、MS20以降Index / Roadmap、Version Controlの状態記録も実装結果へ同期した。

## 2026-09-19 / MS27完了・MS28独立修正実装トラック定義

- 対象:
  - MS27の完了状態と、MS27から切り離したMS28修正実装トラックの定義を状態文書へ反映
- 実施内容:
  - ユーザー判断により、MS27はVer.1.0の実装到達状態をもって完了済みとした。既存のbuild・配布・license・package/readiness証跡は履歴として保持する。
  - 追加のリリースパッケージ整備、再build、GitHub Release、tag、push、merge、公開用source archive生成はMS27の完了条件から分離した。
  - MS28をMS20〜MS27の全体マイルストーン系列とは切り離した、Ver.1実装後の不具合修正実装用マイルストーンとして定義した。
  - MS28-B1は、TEXT＋音声の母音タイムライン非表示と、音声のみ解析後の生成設定反映失敗を対象とする修正実装計画である。
- 判定:
  - MS27は完了済み。MS28は独立修正実装トラックとして開始し、MS28-B1は計画済み・実装未着手である。
- 変更範囲:
  - 状態文書、routing文書、MS28-B1計画の位置づけのみを同期した。production code、test code、runtime JSON / INI、build成果物は変更していない。
  - 今回はテスト、build、GUI、実MMD、push、merge、tag、releaseを実施していない。状態文書のlocal commitは今回の明示依頼で行う。

## 2026-09-18 / MS27 CloseOut確定

- 対象:
  - B6のG-READY Pass、候補#08の既存証跡、未検証事項・公開境界を前提とするMS27 CloseOutのユーザー確定と状態文書同期
- 実施内容:
  - ユーザーがMS27 CloseOutを確定した。B1〜B6のPass記録、候補#08のEXE / ZIP identity、MS26 CloseOut Aを継承し、MS26の実MMD確認はユーザー報告としての記録を維持する。
  - Python 3.11 / 3.12のsource / build互換性は未検証の別support policyとして残す。FFmpegのexact provider archive identityは既存B3方針上の非阻害provenance limitationであり、GitHub上の既存公開の規約適合はユーザー判断である。Codexは法的適合を独自に保証しない。
- 判定:
  - MS27 CloseOutを確定した。新たなP1 / P2 / P3は記録していない。
  - GitHub Release、tag、push、merge、公開用source archive生成は未実施の別工程である。
- 変更範囲:
  - 状態文書のみを同期した。候補#08のEXE / ZIP、配布用readme、LICENSE、NOTICE、候補採用版の`THIRD_PARTY_LICENSES.md`、production code、test code、build設定、runtime JSON / INIは変更していない。
  - 今回はbuild、テスト、compileall、ZIP再生成、GUI / 実MMD、ネットワーク、stage、commit、push、merge、tag、releaseを実施していない。

## 2026-09-18 / MS27-B6 release readiness監査

- 対象:
  - 候補#08のB1〜B5証跡、current HEADとの差分、配布文書影響、MS27 release readinessの最終照合
- 実施内容:
  - B6開始時のbranchは`feature/MS27-implementation`、HEADは`840fa8b Document MS27-B6 implementation plan`、working treeはcleanであった。
  - B5の保存証跡と候補#08をread-onlyで照合し、EXE 425824202 bytes / SHA-256 `AF3B8FD65E3A518F5960EB4D697BE81AA773A1DAE312703552902D97D4CE4223`、ZIP 423274681 bytes / SHA-256 `D963D5F619D48C59B2287992BF6AB350B23AA8DE240686477EA59093F9DB9086`、ZIP 157 filesを確認した。
  - `MMD_AutoLipTool.spec`は候補sourceと同一bytesである。候補embedded版の`THIRD_PARTY_LICENSES.md`と現HEADとの差分は、B5後の状態記録だけであり、候補へ後追いで含めない。配布bytesへ現HEAD版を採用する場合はB4/B5の再実施が必要である。
  - B5のCodex実行記録と、スプラッシュ`Ver. 1.0.0`のユーザー目視確認を継承した。今回GUI / 実MMDは操作していない。
- 判定:
  - B1〜B5のPassを維持し、B6監査報告を完了した。
  - Python 3.11 / 3.12のsource / build互換性は未検証だが、ユーザー決定によりWindows onefile公開判定から外した。`origin/main`は`2151d7b`を指し、FFmpeg 10 entriesと通知文書を追跡し、候補branchの`FFmpeg/bin`に差分がないことを確認した。ユーザーはGitHub上の既存公開を規約上問題なしと判断しており、Codexは法的適合を独自に保証しない。これらを反映してMS27のG-READYをPassとする。
  - B6監査時点ではMS27 CloseOut、GitHub Release、tag、push、merge、公開用source archive生成は未実施だった。後続のユーザー明示決定によりMS27 CloseOutは確定し、公開操作は未実施のままである。
- 変更範囲:
  - 候補#08の採用入力外である状態文書とroot READMEをB6結果へ同期した。候補#08のEXE / ZIPおよび配布用readme、LICENSE、NOTICE、候補採用版の`THIRD_PARTY_LICENSES.md`は変更していない。
  - テスト、compileall、build、ZIP再生成、GUI / 実MMD、ネットワーク、stage、commit、push、merge、tag、releaseは実施していない。

## 2026-09-16 / MS27-B5 ZIP・配布環境確認

- 対象:
  - MS27-B5の候補#08再build、ZIP組立・展開、配布環境での起動・音声処理・Whisper解析・通常終了確認
- 実施内容:
  - 候補#07で確認した過剰なmodule除外を限定補修し、候補#08を再build・SmokeLaunch・内部監査した。EXEは425824202 bytes、SHA-256 `AF3B8FD65E3A518F5960EB4D697BE81AA773A1DAE312703552902D97D4CE4223`、FileVersion / ProductVersionは`1.0.0`。
  - `MMD_AutoLipTool_v1.0.0_Windows_onefile.zip`を組立・展開し、157 files、必須5ファイル、license tree、全hash、安全なentry、runtime data / weights / sampleの非同梱を確認した。ZIP SHA-256は`D963D5F619D48C59B2287992BF6AB350B23AA8DE240686477EA59093F9DB9086`。
  - Codexが配布EXEをrepo外cwd、Windows標準PATHのみ、Python環境変数なしで操作し、WAV / MP3 / M4A、model未配置時の安全な停止、既存smallモデルによるvoice_onlyとTEXT＋音声、Preview、VMD保存、通常終了・再起動・残留なしを確認した。スプラッシュ`Ver. 1.0.0`はユーザー目視確認であり、Codex画面取得とは扱わない。
- 検証:
  - runtime除外の対象回帰は`8 passed, 21 subtests passed`、process exit code `0`。
  - B5の最終照合はZIP・展開・実行先の全157 files、出力WAV / VMD形式、process evidence、文書hashについてprocess exit code `0`で完了した。
- 判定:
  - B5-G-INPUT / DOCS / PATH / ENVおよびG-PACKAGEはPass。B5を実装・検証完了とした。
  - Python 3.11 / 3.12、FFmpeg exact archive provenance・公開時の対応ソース提供方式、MS27 release readinessとGitHub公開はB6以降の未確認・未実施事項である。B5 PassをMS27全体closeoutや公開許可と扱わない。
- 変更範囲:
  - spec、THIRD_PARTY_LICENSES、対象テスト、B5計画をworking treeへ反映した。ユーザー提供の未追跡WAVは保護し、ZIPへ含めていない。
  - stage、commit、push、merge、tag、releaseは未実施である。

## 2026-09-14 / MS27-B4 artifact audit・ユーザー確認反映

- 対象:
  - MS27-B4の残存finding解消、fix-03 onefile再ビルド、SmokeLaunch、内部archive監査、ユーザー手動確認・実MMD確認の記録
- 実施内容:
  - `MMD_AutoLipTool.spec`へmatplotlib、旧Qt、Torch test/TensorBoard、Numba TBB任意backendの除外を追加し、`build_hooks/hook-torch.py`でTorch標準hookの過剰な全サブモジュール収集を置換した。
  - `tests/test_whisper_model_catalog.py`へcustom hook契約を反映した。
  - fix-03候補のonefile EXEを生成し、内部archiveからmatplotlib package/data、sample_data、旧Qt、Torch test/TensorBoard、Numba TBB任意backendが含まれないことを確認した。Whisper / Torch / Numba主要moduleは保持されている。
  - ユーザーからMS27-B4手動確認通過・実MMDでも問題なしとの報告を受領した。Codex自身のGUI / 実MMD操作とは扱わない。
- 検証:
  - B4対象test: `7 passed`、process exit code `0`。
  - fix-03隔離onefile build / SmokeLaunch: process exit code `0`、成功。
  - EXE: 425758214 bytes、SHA-256 `B211FA3312568C0E9067297157C63CEDA742BBFF67C5A84E62D2E1219F05965C`、FileVersion / ProductVersion `1.0.0`。
- 判定:
  - MS27-B4のG-ARTIFACTはPass。B5 ZIP / 配布環境確認、B6 release readiness、GitHub公開は未実施。
- 変更範囲:
  - spec、build hook、対象回帰testをworking treeへ反映した。今回の文書同期自体ではproduction code、runtime JSON / INI、FFmpeg binaryは変更していない。
  - stage、commit、push、merge、tag、releaseは未実施である。

## 2026-09-12 / MS26 Closeout A

- 対象:
  - MS26-B1〜B4の最終証拠照合、ユーザー実MMD受入、Closeout判定、MS27移管の同期
- 実施内容:
  - B1 baseline / contract gate、B2 automated cross-boundary regression、B4 Whisper周辺targeted revalidationの既存実行記録を確認した。
  - ユーザーから、MMD Ver 9.32、指定model、入力音声、出力MMD用WAV、日本語・ラテン、4主要ケース、実MMD上の音声・モーフ同期、GUI / recovery / Whisper追加gateの確認済み報告を受領した。Codex自身のGUI / 実MMD操作とは扱わない。
  - 生成artifact一組のVMD / MMD用WAV / reportをread-only確認済みとして対応付けた。PMX hashは現在のCodex環境から独立取得できず、補助identityの制限として記録した。
  - B2-R05のdaemon例外見出しは観測事実として保持し、再現なし・機能影響未観測の非確定観測へ分類した。原因未確定を無害性の証明とは扱わない。
  - `MS26-B4-003`としてB4-AC01〜08、MS27の責務境界、関連文書の現行状態を最終照合した。
- 検証:
  - B2補修後unit `25 passed`、実FFmpeg `24/24`、full pytest `1067 passed, 4 skipped`、各process exit code `0`の既存記録を再利用した。skipはsymlink作成権限不足（`WinError 1314`）。
  - B4 targeted revalidation: 25 passed・2 skipped、controller 3 passed、Whisper UI 4 passed、各process exit code `0`の既存記録を再利用した。
  - 文書差分の`git diff --check`は今回の最終更新後にprocess exit code `0`を確認した。
- 判定:
  - B4-AC01〜08を充足し、未解消のP1 / P2 / P3はない。MS26 Closeout Aと判定した。
  - PyInstaller onefile、SmokeLaunch、配布物、license / package / release readinessはMS27へ移管する。
- 変更範囲:
  - MS26関連文書8件を更新した。production code、test code、GUI、runtime JSON / INI、依存関係、build設定、外部素材は変更していない。
  - stage、commit、push、merge、tag、releaseは未実施である。

## 2026-09-04 / MS25-B7 回帰・文書同期・Closeout A

- 対象:
  - MS25-B7 full regression、cross-boundary回帰、利用者向け文書・正文仕様照合、Closeout判定
- 実施内容:
  - 検証HEAD `0b25c5c Document MS25-B7 implementation plan`でB6 required fault / recovery gate、MS25-B1〜B6 aggregate、4群のcross-boundary回帰、全pytest、compileallを実行した。
  - README、`readme_mmdautolip.txt`、Pipeline / GUI State / Error Handling / VMD Output正文仕様を現行挙動と照合し、必要事項が反映済みのため追加変更不要と判定した。
  - Index、Roadmap、Block Breakdown、B6 plan、B7 plan、milestone、Version ControlをB7実績、skip理由、manual evidence、MS26 / MS27境界へ同期した。
- 検証:
  - B6 required gate: `26 passed`、process exit code `0`。Windows実filesystemのjunction / reparse collisionとsharing violationはskipなしで通過した。
  - MS25-B1〜B6 aggregate: `160 passed, 2 skipped`、process exit code `0`。
  - cross-boundary: diagnostics / report / fingerprint `60 passed`、VMD / effective output / preset / profile `200 passed`、MMD WAV / individual save `21 passed`、worker / lifecycle / textless / Whisper `41 passed`。合計`322 passed`、各process exit code `0`。
  - 全pytest: `1041 passed, 4 skipped`、process exit code `0`。skipはWindows symlink作成権限不足（WinError 1314）に限定され、B6 required gateにはない。
  - `compileall -q src tests`、`git diff --check`: process exit code `0`。
  - B5 / B6の手動GUI確認はユーザー報告として範囲限定で再利用した。B7でfresh GUIは実施していない。
- 判定:
  - 新たなP1 / P2 / P3はなく、MS25 Closeout Aと判定した。
  - 実MMD確認はMS26、Python 3.11 / 3.12は未検証、package / release readinessはMS27へ引き継ぐ。
  - B7文書同期の変更はworking tree上で未stage・未commitである。production code、test code、GUI、依存関係、build設定、runtime user dataは変更していない。push、merge、tag、releaseは未実施である。

## 2026-09-03 / MS25-B5 実装・自動検証・ユーザー手動GUI確認完了

- 対象:
  - MS25-B5 GUI・worker・状態統合、一括出力導線、P3修正
- 実施内容:
  - `ファイル > MMD一括出力...`、parent / folder名dialog、delivery専用worker、Busy / cancel / close lifecycle、pre-commit UI bridgeを接続した。
  - generic worker stateとworker referenceの不整合によりfalse `delivery_busy`となる経路をP3修正し、既存の個別VMD / MMD用WAV / report導線を維持した。
- 検証:
  - B5および関連worker / GUI回帰: `29 passed`、process exit code `0`。
  - 全pytest: `1015 passed, 4 skipped`、process exit code `0`。
  - `compileall -q src tests`、`git diff --check`: process exit code `0`。
  - ユーザーから提示したB5手動GUIテスト通過の報告を受領した。これはユーザー確認として記録し、Codex自身のGUI実行結果とは扱わない。
- 判定:
  - MS25-B5は実装・自動検証・ユーザー手動GUI確認まで完了した。変更はworking tree上で未stage・未commitである。
  - B6 fault matrix、B7 full cross-boundary regression / closeout、実MMD確認は未完了。Python 3.11 / 3.12は未検証、package / release readinessはMS27へ引き継ぐ。

## 2026-08-28 / MS24 Closeout A

- 対象:
  - MS24-B7 Closeout判定、B7-F-002のP3文書表記補正、関連routing文書同期
- 実施内容:
  - `B7-F-002`を`P3（解消）`へ補正し、B7のfinding ledgerを解消済み状態へ統一した。
  - B7 plan、B6 plan、Block Breakdown、Index、Roadmap、Version ControlをMS24 Closeout Aの到達状態へ同期した。
- 判定:
  - P1 / P2はなく、B7-F-001 / B7-F-002は解消済みとして記録した。
  - MS24 Closeout Aを合格と判定した。Python 3.11 / 3.12は未検証扱い、実MMD確認はMS26、package / release readinessはMS27へ引き継ぐ。
- 変更範囲:
  - production code、test code、GUI、依存関係、runtime user dataは変更していない。push、merge、tag、releaseは未実施である。

## 2026-08-28 / MS24-B7 統合回帰・配布影響静的監査

- 対象:
  - MS24-B7 integration regression、manifest / package静的監査、利用者向け文書同期
- 実施内容:
  - MS24直接回帰、MS23 direct、MS19 voice-only、MS20 diagnostics、MS21 rollback / pipeline、pipeline / VMD、MS17 MMD用WAV回帰を現行HEADで再実行した。
  - README、配布用readme、Release Package Manifest、THIRD_PARTY_LICENSESへ、Whisperモデルの安全な切り替え手順、明示Download & Verify、exact size / SHA256、model weights非同梱、解析時自動download禁止、音声外部送信なしを同期した。
  - `collect_data_files("whisper")`、spec固有datas、package-data、tracked fileを監査し、manifestとWhisper package assets以外のmodel weightsが配布入力へ入らないことを確認した。
- 検証:
  - MS24直接回帰: `76 passed, 2 skipped`、process exit code `0`。
  - MS23 direct・MS19 voice-only・MS20 diagnostics・MS21 rollback / pipeline・pipeline / VMD・MS17 MMD用WAV回帰: `163 passed`、process exit code `0`。
  - 全pytest: `881 passed, 2 skipped`、process exit code `0`。
  - `compileall -q src tests`、`git diff --check`: process exit code `0`。
  - `collect_data_files("whisper")`: `mel_filters.npz`、`multilingual.tiktoken`、`english.json`、`gpt2.tiktoken`の4件。model weightsなし。
  - Python 3.14.3をMS24の開発・受入環境として確認した。Python 3.13.xは必須compatibility gateとしない。
- 判定:
  - integration regression、static package audit、Python 3.14.3 development / acceptance gateは完了した。MS24 Closeout判定は未実施とする。
  - B3〜B6で受領済みのユーザー手動GUI確認報告をcurrent evidenceとして再利用した。B7で追加のGUI実行は行っていない。
  - 旧P2（Python 3.13.x gate未実施）は、ユーザー判断による3.14.3開発・受入環境の採用で解消した。Python 3.11 / 3.12は今回の受入対象外として未検証扱いを維持する。実MMD確認はMS26、onefile / ZIP / PySide6最終artifact・package / release readinessはMS27へ引き継ぐ。
  - production code、test code、GUI挙動、依存関係、runtime user dataは変更していない。push、merge、tag、releaseは未実施である。

## 2026-08-28 / MS24-B7 Implementation Plan P2/P3レビュー補正

- 対象:
  - MS24-B7 Implementation Planと、MS24のrouting文書に残っていたB6状態・責務境界・回帰対象の同期
- 実施内容:
  - MS23-B2〜B6直接回帰、保持すべきtiming経路、pipeline / VMD / MMD用WAV回帰をB7 planへ具体的なtest fileとして追記した。
  - B2 `VerifiedWhisperCheckpoint` DTO、loader自身の同一open handle再検証、検証済みbytes束縛の責務境界を文書間で統一した。
  - `pyproject.toml`の`requires-python >=3.11` metadata floorと、MS24のPython 3.13.x compatibility gateを分離して記録した。
  - B6のcommit済み状態（`1f1aff2`）とB7 plan作成済み・B7実施未着手をIndex、Roadmap、Block Breakdown、B6 plan、Version Controlへ同期した。
- 判定:
  - 今回は文書のみを補正した。production code、test code、GUI、依存関係、runtime user dataは変更していない。
  - Python 3.13.x互換性、`collect_data_files("whisper")` static audit、B7 cross-boundary回帰、Closeout判定は未実施である。

## 2026-08-26 / MS24-B6 実装・自動検証・ユーザー手動GUI確認完了

- 対象:
  - MS24-B6 `WhisperDiagnosticsSummary`、diagnostics projection、safe failure、model-aware rollback連携
- 実施内容:
  - selected / active / loaded / analysis identityの分離、package version / gate status、projection generation、Info / report / RightPaneの同一snapshot投影を実装した。
  - MS23固定morph・Latin profile・preset・diagnostics・fingerprint契約、暗黙download禁止、依存値、runtime user data境界を維持した。
- 検証:
  - 全pytest `881 passed, 2 skipped`、process exit code `0`
  - `compileall -q src tests`、`git diff --check`、process exit code `0`
  - ユーザーからB6手動GUI確認通過・問題なしの報告を受領した。これはユーザー確認の範囲に限定し、Codex自身のGUI実行結果とは扱わない。
- 判定:
  - MS24-B6は`1f1aff2 Implement MS24-B6 diagnostics and recovery`としてcommit済みである。push、merge、tag、releaseは未実施である。
  - Python 3.13.x互換性確認は未実施、実MMD確認はMS26、MS27 package / release readinessはMS27へ引き継ぐ。次工程はMS24-B7である。

## 2026-08-25 / MS24-B5 実装・自動検証・ユーザー手動GUI確認完了

- 対象:
  - MS24-B5 verified-local model runtime・AnalysisWorker / pipeline伝播
  - Apply / candidate commit-reject、single-active ownership、rollback、Delete、storage root change、shutdown lifecycle
- 実施内容:
  - verified model requestをTEXT + 音声・voice-onlyの全Whisper timing経路へ伝播し、解析時の暗黙downloadを禁止した。
  - single-active runtime、lease、明示unload / device cleanup、candidate Apply、B5 production ownership permitを接続した。
  - model identity-aware rollback、model変更時のretained timing invalidation、production Delete、storage root change、終了時shutdownを接続した。
  - MS23の固定morph、Latin profile、preset、diagnostics、fingerprint契約とword / segment fallbackを維持した。
- 検証:
  - 全pytest `872 passed, 2 skipped`、process exit code `0`
  - `compileall -q src`、`git diff --check`、process exit code `0`
  - ユーザーから手動GUI確認完了・問題なしの報告を受領した。これはユーザー確認の範囲に限定し、Codex自身のGUI実行結果とは扱わない。
- 判定:
  - MS24-B5はworking tree上で実装・自動検証・ユーザー手動GUI確認まで完了した。
  - Python 3.13.x互換性確認、実MMD確認、MS27 package / release readinessは未確認または別工程である。
  - stage、commit、push、merge、tag、releaseは未実施。次作業はPython 3.13.x compatibility gate確認後のMS24-B6 Implementation Planである。

## 2026-08-24 / MS24-B4 実装・自動検証・ユーザー手動GUI確認完了

- 対象:
  - MS24-B4 明示確認付きforeground download・cancel・削除
  - 保存先変更、再利用可能availability rescan、B2/B5 Delete境界
- 実施内容:
  - 公式manifest URL限定downloader、exact size / Content-Length / redirect / stream failure / cancel / cleanup検証、専用model management workerを追加した。
  - Whisper管理UIへDownload & Verify、Cancel、Delete、保存先変更、progress/statusを接続した。
  - SettingsStore managed merge、`system` / `light` / `dark` theme保持、`start_whisper_availability_rescan()`を実装した。
  - B5 permit未接続時はDeleteをblockedとし、active / loaded / analysis identityをB4から変更しない。
- 検証:
  - 全pytest `860 passed, 2 skipped, 77 subtests passed`、process exit code `0`
  - `compileall src tests`、`git diff --check`、process exit code `0`
  - ユーザーから手動GUI確認完了・問題なしの報告を受領した。これはユーザー確認の範囲に限定し、Codex自身のGUI実行結果とは扱わない。
- 判定:
  - MS24-B4はworking tree上で実装・自動検証・ユーザー手動GUI確認まで完了した。
  - Python 3.13.x互換性確認、B5 ownership provider接続後の実production Delete、実MMD確認、MS27 package / release readinessは未完了である。
  - stage、commit、push、merge、tag、releaseは未実施。次作業はPython 3.13互換性gateとB5 Implementation Planである。

## 2026-08-23 / MS24-B4 Implementation Plan再チェックP2/P3解消

- 補正内容:
  - 通常アプリの保存先変更は`SettingsStore` managed persistenceだけを使用し、runtime INIの直接編集・コピー・stageは禁止する境界へ修正した。
  - `system` / `light` / `dark` theme round-trip、全設定merge、`whisper_models_dir`だけの置換をB4対象と回帰へ追加した。
  - promote成功後の全体availability projectionはcontrollerの再利用可能な`start_whisper_availability_rescan()`だけを入口とし、Python 3.13.xの実行ファイルpath・version・process exit code記録をcompatibility gateへ追加した。
- 判定:
  - P2 / P3は計画・関連文書上で補正済み。次作業は補正後MS24-B4 planのfresh read-only pre-implementation check。
  - production code、test code、GUI、依存関係、runtime user data、stage、commit、push、merge、tag、releaseは変更していない。

## 2026-08-23 / MS24-B4 Implementation Plan作成・P2/P3補正

- 対象:
  - MS24-B4 明示確認付きforeground download・cancel・削除
  - 保存先変更、再利用可能availability rescan、B2/B5 Delete境界
- 補正内容:
  - 保存先変更は現在の全設定を保持する安全なmerge保存とし、`whisper_models_dir`だけのpartial saveでtheme、window、recent path等を上書きしない契約を追加した。
  - B2内部の対象model verification scanとcontrollerの`start_whisper_availability_rescan()`による全体availability projectionを分離した。
  - B3の実装コミットを`a27a26f`、B4 plan作成済みとして現在地を同期した。
- 判定:
  - P2 / P3は計画・関連文書上で解消済み。次作業はMS24-B4 planのfresh read-only pre-implementation check。
  - production code、test code、GUI、依存関係、runtime user dataは変更していない。

## 2026-08-23 / MS24-B3 実装・自動検証・ユーザー手動GUI確認完了

- 対象:
  - MS24-B3 設定・UiState・モデル選択UI
  - selected / active identity、local-only availability scan、RightPane Whisperモデルtab、Busy / stale / shutdown境界
- 実施内容:
  - `SettingsStore`、`UiState`、`AppController`、`MainFrame`、`RightPane`、`app.py`へB3の設定・状態・UI投影を実装した。
  - B3専用availability workerを追加し、起動時scanをUIスレッドから分離した。候補選択だけではactive / loaded / analysis identity、既存解析、Preview、network、Whisper loadを変更しない。
  - B2の`failure_code` / `message`をB3のfailure code / diagnostic detailへ分離し、通常UIにはsafe noticeだけを表示する契約を固定した。
- 検証:
  - B3追加・関連の限定検証、full suite `846 passed, 2 skipped`、`compileall src tests`、`git diff --check`はprocess exit code `0`。
  - ユーザーから、計画指定範囲の手動GUI確認完了・問題なしの報告を受領した。これはユーザー確認の範囲に限定し、Codex自身のGUI実行結果とは扱わない。
- 判定:
  - MS24-B3はworking tree上で実装・自動検証・ユーザー手動GUI確認まで完了。実network、実model、実Whisper解析、実MMD確認は未実施で、B4、B5、MS26へ引き継ぐ。
  - stage、commit、push、merge、tag、releaseは未実施。次作業はMS24-B4 Implementation Plan策定。

## 2026-08-20 / MS23-B7 Closeout 完了（A）

- 対象:
  - MS23-B7 Closeout監査
  - B1〜B6 / B4Bの要求、実装、test、ユーザーGUI確認、文書、runtime user data、配布境界
- 実施内容:
  - B7 Implementation Planへcurrent revalidation、P分類、A判定、MS24 / MS26 handoffを記録した。
  - MS23 Block Breakdown、MS20 and Beyond Index、RoadmapをMS23 Closeout Aへ同期した。
  - production code、test code、GUI、runtime user data、dependency、package / build / license設定は変更していない。
- 検証:
  - MS23 direct -> 82 passed、31 subtests passed / exit code 0
  - MS21 / MS22関連 -> 90 passed / exit code 0
  - diagnostics / report / Preview / writer / VMD -> 174 passed / exit code 0
  - MS17 / MS19 / MS20 lifecycle -> 54 passed、7 subtests passed / exit code 0
  - wx aggregate -> 136 passed、661 deselectedを2回 / 各exit code 0
  - full suite -> 797 passed、57 subtests passedを2回 / 各exit code 0
  - `compileall src tests`、`git diff --check` -> exit code 0
  - runtime user data 3 pathはroot限定ignore・Git非追跡。package / dependency / license / network / Qt境界に差分なし。
  - B2 / B5 / B6のGUI確認はユーザー報告の範囲を再利用。Codex自身のGUI実行ではない。
- 判定:
  - P1 / P2 / P3なし。MS23 CloseoutはA。
  - 実MMDでのVMD / WAV読み込み・再生・リップ同期はMS26へ引き継ぐ。
  - 次作業はMS24 Implementation Plan策定。MS24実装、merge、push、tag、release、branch削除は未実施。

## 2026-08-12 / MS22-B7 Closeout 完了（A）

- 対象:
  - MS22-B7 Closeout監査
  - B1からB6の受け入れ条件・実装・test・ユーザー確認・文書・runtime user data・配布境界
- 実施内容:
  - B7実装計画§15.2へ、B1〜B6の証拠台帳、回帰結果、P分類、runtime user data境界、dependency / package境界を記録した。
  - P1 / P2 / P3なしを確認し、MS22 CloseoutをAと判定した。
  - production code、test code、GUI、dependency、package設定は変更していない。
- 検証:
  - MS22 direct regression -> 93 passed / exit code 0
  - text / pipeline / Preview / writer / settings回帰 -> 185 passed / exit code 0
  - MS21 effective output / history / lifecycle回帰 -> 138 passed / exit code 0
  - MS17 / MS19 / MS20 input / diagnostics / save回帰 -> 158 passed / exit code 0
  - B4 / B5 / splash組合せ -> 18 passed / exit code 0
  - `pytest tests` -> 713 passed / exit code 0
  - `compileall src tests`、`git diff --check` -> exit code 0
  - B4 / B5 / B6の手動GUI確認はユーザー報告の範囲を再利用し、Codex自身のGUI実行とは扱っていない。
- 判定:
  - `presets.json` / `MMD_AutoLipTool.ini`はGit追跡対象外・root限定ignoreで、local `presets.json`保持を確認した。
  - 実MMDでのVMD / WAV読み込み・リップ同期はMS26の未検証事項として維持する。
  - 次作業はMS23 Implementation Plan策定。MS23実装、merge、push、tag、release、branch削除は未実施。

## 2026-07-31 / MS21-B8 Closeout 完了

- 対象:
  - MS21-B8 Closeout監査
  - B1からB7の受け入れ条件・実装・test・ユーザー確認・文書・配布境界
- 実施内容:
  - B8計画§15へB1〜B7の実装commit、受け入れ条件、自動test、ユーザー確認範囲、文書同期を記録した。
  - B7-PRE-004のclosed状態、dependency / package / build / license差分なし、fixed morph / VMD / network契約を確認した。
  - B8はproduction code、test code、GUI挙動、依存関係、build / package設定を変更していない。
- 検証:
  - B7専用 -> 15 passed / exit code 0
  - B2〜B6 MS21回帰 -> 123 passed / exit code 0（B5専用再確認28 passed / exit code 0を含む）
  - MS17 / MS19 / MS20・既存回帰 -> 154 passed、7 subtests passed / exit code 0
  - `pytest tests` -> 618 passed、7 subtests passed / exit code 0
  - `compileall src tests`、`git diff --check` -> exit code 0
  - B1からB7のユーザー手動GUI確認は、各Blockで報告された範囲を再利用した。
- 判定:
  - P1 / P2 / P3なし。MS21 CloseoutはAとし、MS22開始条件を引き継ぐ。
  - 実MMDでのVMD / WAV読み込み・リップ同期はMS26の未検証事項として引き継ぐ。
  - merge、push、tag、release、branch削除は未実施。

## 2026-07-27 / MS21-B7 完了

- 対象:
  - MS21-B7 State Integration / Regression / Docs / Adjustment Sync Efficiency
  - Selected Event Tab Auto-Switch追加補正
- 実施内容:
  - analysis failure / cancel rollback、dirty入力保護、parameter一致、analysis / audio terminal guardを実装した。
  - 1同期限定contextとadjustment-only同期により、Undo / Redo時の重複resolverと不要再描画を削減した。
  - Preview eventのcanonical user click成功後にRightPane「選択イベント」tabへ自動切替する追加補正を実装した。
  - 自動testのanalysis failure経路が実MessageBoxを開く問題を、production契約を変えずtest内mockへ限定補修した。
  - README、配布用readme、Pipeline / GUI / Error仕様、MS21進捗文書をimplemented状態へ同期した。
- 検証:
  - B7本体実装時のfull suite -> 617 passed、7 subtests passed / exit code 0
  - 追加補正・MessageBox test補修後のfull suite -> 618 passed、7 subtests passed / exit code 0
  - `compileall src tests`、`git diff --check` -> exit code 0
  - ユーザー手動GUI確認 -> 追加補正を含むB7範囲が通過、問題なし
- 判定:
  - MS21-B7は実装、自動検証、ユーザー手動GUI確認まで完了した。
  - dependency、package、build、license、固定モーフ、VMD形式、network契約に変更はない。
- 次作業:
  - MS21-B8 Closeout計画を策定する。
  - merge、push、tag、release、branch削除は未実施。

## 2026-07-20 / MS20-B8 MS20 Closeout 完了

- 対象:
  - MS20-B8
  - B1からB7のCloseout監査
- 実施内容:
  - diagnostics core、RightPane Info / Warning、live playback context、VMD保存policy、diagnostic report、state lifecycleをcode / test / user / docsの4系統で照合した。
  - B3からB7の通過済みユーザーGUI確認記録を再確認した。
  - pre-implementation checkで検出したBlock BreakdownのP3表記を解消し、MS20進捗文書をCloseOut済みへ同期した。
  - dependency、package、build、license関連ファイルにMS20由来の差分がないことを確認した。
- 検証:
  - MS20固有テスト -> 108 passed / exit code 0
  - state / GUI / worker / voice_only回帰 -> 65 passed、7 subtests passed表示 / exit code 1
  - pipeline / VMD回帰 -> 12 passed / exit code 0
  - `pytest tests` -> 476 passed表示 / exit code 1
  - 後者2件はfailure / error / fatal stack traceなしでsummaryまで完走し、B7 baselineと一致した。
  - `compileall src tests`、`git diff --check` -> exit code 0
- 判定:
  - P1 / P2なし。P3 1件は文書同期で解消し、残存findingなし。
  - MS20 CloseoutはA。
  - B8でproduction code、test code、GUI、dependency、build/package設定は変更していない。
  - B3からB7のユーザー確認証拠を再利用した。Closeout監査後、ユーザーからB8チェック通過・問題なしと報告された。
  - 自動検証とユーザー確認が揃い、MS20のCloseout状態を確定した。
- 次作業:
  - MS21 Implementation Planを策定する。
  - main merge、remote push、tag、release、branch削除は未実施。

## 2026-07-13 / MS19-B9 MS19 Closeout 完了

- 対象:
  - MS19-B9
  - B1からB8のCloseout監査
- 実施内容:
  - MS19固有テスト、計画指定のcore / GUI回帰、全体pytestを実行した。
  - B3からB9のユーザー確認記録、README / 配布用readme / 仕様 / milestone文書、MS19差分を確認した。
  - dependency、packaging、license関連ファイルにMS19由来の差分がないことを確認した。
- 検証:
  - MS19固有テスト -> 33 passed / exit code 0
  - `test_wx_ms14_b6_closeout.py` -> 終了処理補修後 3 passed / exit code 0
  - 計画指定回帰 -> 62 passed表示 / exit code 1
  - `pytest tests` -> 368 passed表示 / exit code 1
  - Python 3.14.3、wxPython 4.2.5、pytest 9.0.3で実行
- 判定:
  - P1なし。
  - P2は解消。`tests/test_wx_ms14_b6_closeout.py` でフレーム破棄前に `_cleanup_analysis_job()` を実行するよう補修した。
  - MS19 CloseoutはA。
  - Production code、build/package設定は変更していない。
  - ユーザーチェック通過・問題なし。
- 次作業:
  - package / release作業またはMS20計画策定へ進む。

## 2026-07-12 / MS19-B9 MS19 Closeout Plan

- 対象:
  - MS19-B9
  - MS19 Closeout実装プラン作成
- 実施内容:
  - `docs/Implementation_Plan/MS19-B9_Implementation_Plan.md` を作成した。
  - B1からB8のコード、テスト、ユーザー確認、文書を再照合するCloseout手順を定義した。
  - MS19固有テスト、関連回帰、通常全体テストの実行方針と、wx終了コードの分離記録を定義した。
  - package / release、version bump、merge / push、MS20実装をB9対象外とした。
  - P1 / P2 / P3分類とA / B / CのCloseout判定を定義した。
- 変更有無:
  - B9計画作成によるProduction code changes: なし
  - B9計画作成によるTest changes: なし
  - Docs changes: あり
- 後続状態:
  - MS19-B9実装プラン作成済み。
  - 次作業はMS19-B9実装前チェック。

## 2026-07-11 / MS19-B8 Workspace Reset / New Session Flow Implementation

- 対象:
  - MS19-B8
  - Workspace Reset / New Session Flow 実装
- 実施内容:
  - ファイルメニューへ `新規作業... Ctrl+N` を追加した。
  - `UiState` の作業データ限定reset、確認キャンセル時の完全不変、Busy中無効を実装した。
  - audio / analysis job IDを単調に進め、reset前のlate callbackを反映しないようにした。
  - InfoPanel、Waveform、Preview、RightPane、playback cursor、viewportを初期表示へ戻すようにした。
  - recent files、theme、解析パラメータ、保存先履歴を保持し、source / output / cacheファイルを削除しない契約をテストした。
- 検証:
  - `tests/test_ms19_b8_workspace_reset.py` -> 8 passed / exit code 0
  - B8対象・関連回帰 -> 60 passed表示 / process exit code 1
  - `pytest tests` -> 368 passed表示 / process exit code 1
  - 後者2件のexit code 1は既存wx終了処理由来として継続記録する。
  - ユーザースモークテスト通過・問題なし。
- 後続状態:
  - MS19-B8 closeoutはOK。
  - 次作業はMS19-B9 Closeout実装プランの策定。

## 2026-07-11 / MS19-B8 Workspace Reset / New Session Flow Plan

- 対象:
  - MS19-B8
  - Workspace Reset / New Session Flow 実装プラン作成
- 実施内容:
  - `docs/Implementation_Plan/MS19-B8_Implementation_Plan.md` を新規作成した。
  - ファイルメニューの `新規作業... Ctrl+N` を正本導線とし、TEXT・音声・書き起こし・解析結果・表示・再生状態を安全に初期化する方針を定義した。
  - `UiState` 全交換を禁止し、recent files、theme、parameter、last directoryを保持する作業データ限定reset契約を定義した。
  - 確認キャンセル、Busy中無効、audio / analysis job ID無効化、source / output / cacheファイル非削除を受け入れ条件にした。
  - MS19 CloseoutをB8からB9へ移動した。
  - Block Breakdown、Index、RoadmapをB8計画作成済みへ同期した。
- 変更有無:
  - Code changes: なし
  - GUI changes: なし
  - Test changes: なし
  - Docs changes: あり
- 後続状態:
  - MS19-B8実装プラン作成済み。
  - 次作業はMS19-B8実装前チェック。
  - MS19 CloseoutはB9で実施する。

## 2026-07-10 / MS19-B7 Error Handling / Tests / Docs Implementation

- 対象:
  - MS19-B7
  - Error Handling / Tests / Docs 実装
- 実施内容:
  - voice_only解析エラーをWhisper失敗、書き起こし空、timing anchor不足、読み変換失敗、母音列なし、編集済みテキスト空、再解析情報不足へ分類した。
  - 解析失敗時はtiming planとVMD保存可状態を無効化し、編集済み書き起こしは保持する状態復帰を実装・テストした。
  - voice_only VMD保存失敗時は解析結果と保存可否を保持し、別の保存先で再試行できる表示へ更新した。
  - `tests/conftest.py` を追加して通常pytestのimport pathを安定化し、旧MS14 closeout fixtureを現行TEXT入力契約へ追従させた。
  - README / 配布用readme / Error Handling / Pipeline Data Contract / GUI State仕様を音声のみ入力へ同期した。
- 検証:
  - B7新規テスト6件 -> pass / exit code 0
  - B7対象・関連回帰テスト -> 59 passed / exit code 0
  - `pytest tests` -> 360 passed表示。既存wx終了処理由来でprocess exit code 1
- 後続状態:
  - B7実装と自動確認は完了。
  - 2026-07-10 にユーザー確認通過・問題なし。
  - MS19-B7 closeoutはOK。
  - 次作業はMS19-B8 MS19 Closeout実装プラン策定。

## 2026-07-09 / MS19-B7 Error Handling / Tests / Docs Plan

- 対象:
  - MS19-B7
  - Error Handling / Tests / Docs 実装プラン作成
- 実施内容:
  - `docs/Implementation_Plan/MS19-B7_Implementation_Plan.md` を新規作成した。
  - B7の対象を、音声のみ入力に固有の失敗条件分類、状態復帰、テスト実行状態整理、README / 配布用readme / 関連docs同期に限定した。
  - Whisper失敗、書き起こし空、読み変換失敗、母音列なし、編集済みテキスト空、VMD保存失敗を、B7で扱う代表エラー条件として整理した。
  - 通常 `pytest tests` のimport path収集問題と `tests/test_wx_ms14_b6_closeout.py` の既存closeout系2件失敗は、B7実装前チェックで分類する方針とした。
  - `docs/MS17_and_Beyond_Index.md`、`docs/Implementation_Plan/MS19_Block_Breakdown.md`、`docs/MS18_and_Beyond_Roadmap.md` をB7計画作成済み状態へ同期した。
- 変更有無:
  - Code changes: なし
  - GUI changes: なし
  - Test changes: なし
  - Docs changes: あり
- 後続状態:
  - MS19-B7 Error Handling / Tests / Docs の実装プランは作成済みである。
  - 2026-07-10 にMS19-B7はユーザー確認通過・完了済み。現在の次作業はMS19-B8実装プラン策定。

## 2026-07-09 / MS19-B6 VMD / Preview / Save Integration

- 対象:
  - MS19-B6
  - VMD / Preview / Save Integration
- 実施内容:
  - `src/core/pipeline.py` に、TEXT pathを要求せず `current_timing_plan` からVMDを書き出す `generate_vmd_from_timing_plan()` と戻り値 `VmdGenerationResult` を追加した。
  - 既存 `generate_vmd_from_text_wav()` と `PipelineResult.text_path` の契約は維持した。
  - `src/gui_wx/ui_state.py` で、voice_only解析成功後はVMD保存可、編集適用直後の未再解析状態はVMD保存不可になるよう `vmd_save_ready` を拡張した。
  - `src/gui_wx/app_controller.py` で、TEXTあり保存は既存 `generate_vmd_from_text_wav()`、voice_only保存は新規 `generate_vmd_from_timing_plan()` を呼ぶ分岐を追加した。
  - `src/gui_wx/main_frame.py` からB4/B5時点の「TEXTなしVMD保存は未対応」ステータス文言を除去した。
  - B4/B5由来のvoice_only保存不可期待値テストを、B6後の仕様へ更新した。
  - `docs/Implementation_Plan/MS19-B6_Implementation_Plan.md`、`docs/Implementation_Plan/MS19_Block_Breakdown.md`、`docs/MS17_and_Beyond_Index.md`、`docs/MS18_and_Beyond_Roadmap.md` をB6実装済み状態へ同期した。
- 変更有無:
  - Code changes: あり
  - GUI changes: あり
  - Test changes: あり
  - Docs changes: あり
- テスト:
  - `.\.venv\Scripts\python.exe -m pytest tests\test_pipeline_and_vmd.py tests\test_ms19_b4_voice_only_gui_state.py tests\test_ms19_b5_transcription_edit_state.py tests\test_wx_ms14_b2_state.py tests\test_wx_ms14_b5_export.py` -> 36 passed / exit code 0
  - `git diff --check` -> 空白エラーなし。LF→CRLF警告のみ。
  - `.\.venv\Scripts\python.exe -m pytest tests` -> 収集時に既存import path不足で停止。
  - `src` / `tests` を `sys.path` に追加した全体確認 -> `tests/test_wx_ms14_b6_closeout.py` の既存closeout系2件のみ失敗。B6保存導線の対象テストでは問題なし。
- ユーザー確認:
  - 2026-07-09 にB6のユーザー側確認通過・問題なし。
- 後続状態:
  - MS19-B6 closeoutはOK。
  - 音声のみ入力のVMD保存有効化は実装済み。
  - 編集適用直後の未再解析状態ではVMD保存不可、編集済み再解析成功後はVMD保存可。
  - 2026-07-10 にMS19-B7はユーザー確認通過・完了済み。現在の次作業はMS19-B8実装プラン策定。

## 2026-07-08 / MS19-B6 VMD / Preview / Save Integration Plan

- 対象:
  - MS19-B6
  - VMD / Preview / Save Integration 実装プラン作成
- 実施内容:
  - `docs/Implementation_Plan/MS19-B6_Implementation_Plan.md` を新規作成した。
  - 現在のB5実装状態を前提に、B6の対象を音声のみ入力のVMD保存有効化、TEXT pathなし保存入口、Preview追従確認、既存TEXTあり保存導線維持に限定した。
  - 既存 `generate_vmd_from_text_wav()` の破壊的な契約変更は行わず、音声のみ入力向けに `current_timing_plan` からVMDを書き出す別入口を追加する方針とした。
  - 編集適用直後の未再解析状態ではVMD保存不可、編集済み再解析成功後はVMD保存可とする状態契約を明記した。
  - `docs/MS17_and_Beyond_Index.md`、`docs/Implementation_Plan/MS19_Block_Breakdown.md`、`docs/MS18_and_Beyond_Roadmap.md` をB6計画作成済み状態へ同期した。
- 変更有無:
  - Code changes: なし
  - GUI changes: なし
  - Test changes: なし
  - Docs changes: あり
- 後続状態:
  - このエントリ作成時点では、MS19-B6 VMD / Preview / Save Integration の実装プラン作成まで完了していた。
  - 2026-07-10 にMS19-B7はユーザー確認通過・完了済み。現在の次作業はMS19-B8実装プラン策定。

## 2026-07-08 / MS19-B5 Review / Edit Transcription Result Flow

- 対象:
  - MS19-B5
  - Review / Edit Transcription Result Flow
- 実施内容:
  - `src/gui_wx/info_panel.py` に、音声のみ解析結果の書き起こし欄を必要時だけ編集可能にする制御、適用ボタン、元に戻すボタン、編集本文取得APIを追加した。
  - `src/gui_wx/ui_state.py` に、元の書き起こし本文、現在の書き起こし本文、編集済み状態、未再解析状態、保持済み `WhisperTimingResult` を追加した。
  - `src/gui_wx/analysis_worker.py` に `whisper_timing_result` 返却を追加し、編集済みテキスト再解析時は保持済み timing result を使ってWhisperを再実行しない契約を追加した。
  - `src/gui_wx/main_frame.py` に、書き起こし編集の適用 / 元に戻す処理、未適用編集ガード、編集済みテキスト再解析 worker 起動を追加した。
  - B5用GUI state / workerテストを追加し、B4/MS14/Whisper関連の対象回帰テストを確認した。
- 変更有無:
  - Code changes: あり
  - GUI changes: あり
  - Test changes: あり
  - Docs changes: あり
- テスト:
  - `.\.venv\Scripts\python.exe -m pytest tests\test_ms19_b5_transcription_edit_state.py` -> 6 passed / exit code 0
  - `.\.venv\Scripts\python.exe -m pytest tests\test_ms19_b4_analysis_worker_voice_only.py` -> 1 passed / exit code 0
  - `.\.venv\Scripts\python.exe -m pytest tests\test_ms19_b4_voice_only_gui_state.py` -> 5 passed / exit code 0
  - `.\.venv\Scripts\python.exe -m pytest tests\test_wx_ms14_b2_state.py` -> 5 passed / exit code 0
  - `.\.venv\Scripts\python.exe -m pytest tests\test_wx_ms14_b4_analysis.py` -> 3 passed / exit code 0
  - `.\.venv\Scripts\python.exe -m pytest tests\test_whisper_timing.py` -> 3 passed / exit code 0
- ユーザー確認:
  - 2026-07-08 にB5のユーザー側確認通過・問題なし。
- 後続状態:
  - MS19-B5 closeoutはOK。
  - このエントリ作成時点では、音声のみ入力のVMD保存有効化は未対応で、MS19-B6で扱う予定だった。
  - 2026-07-10 にMS19-B7はユーザー確認通過・完了済み。現在の次作業はMS19-B8実装プラン策定。

## 2026-07-07 / MS19-B5 Review / Edit Transcription Result Flow Plan

- 対象:
  - MS19-B5
  - Review / Edit Transcription Result Flow 実装プラン作成
- 実施内容:
  - `docs/Implementation_Plan/MS19-B5_Implementation_Plan.md` を新規作成した。
  - 現在のB4実装状態を前提に、B5の対象を音声のみ解析結果の書き起こし編集、編集後のひらがな / 母音列preview更新、編集前timing planの誤用防止、保持済み `WhisperTimingResult` と明示的な worker 入力契約による編集済みテキスト再解析の最小導線に限定した。
  - 編集済みテキスト再解析で `current_timing_plan` を更新した場合、既存Previewが追従して再描画されることはB5の許容範囲とした。
  - B5では、音声のみ入力のVMD保存有効化、Preview操作、再生タイムライン操作、VMD保存まで含む最終連携、永続的な書き起こし履歴管理、外部字幕形式出力、Qt / PySide6 GUI復活を扱わない方針とした。
  - `docs/MS17_and_Beyond_Index.md`、`docs/Implementation_Plan/MS19_Block_Breakdown.md`、`docs/MS18_and_Beyond_Roadmap.md`、`docs/Version_Control.md` をB5計画作成済み状態へ同期した。
- 変更有無:
  - Code changes: なし
  - GUI changes: なし
  - Test changes: なし
  - Docs changes: あり
- 後続状態:
  - このエントリは2026-07-07のMS19-B5計画作成時点の記録である。
  - 2026-07-08 に MS19-B5 Review / Edit Transcription Result Flow は実施済み。
  - 2026-07-09 に MS19-B6 VMD / Preview / Save Integration は実施済み。
  - 2026-07-10 にMS19-B7はユーザー確認通過・完了済み。現在の次作業はMS19-B8実装プラン策定。

## 2026-07-07 / MS19-B4 GUI Entry Point and State Handling

- 対象:
  - MS19-B4
  - GUI Entry Point and State Handling
- 実施内容:
  - `src/gui_wx/ui_state.py` に `text_audio` / `voice_only` の入力モード、解析開始可否、TEXTありVMD保存可否、transcription保持フィールドを追加した。
  - `src/gui_wx/analysis_worker.py` に `AnalysisWorkerResult` とTEXTあり / voice_only分岐を追加した。
  - voice_only分岐では `recognize_audio_timing()` を1回だけ実行し、同じ `WhisperTimingResult` を `build_vowel_timing_plan(..., whisper_timing_result=...)` へ渡すことでWhisper二重実行を避けるようにした。
  - `src/gui_wx/main_frame.py` はTEXTなし音声入力で解析ボタンを有効化し、voice_only解析成功時に書き起こし本文・ひらがな・母音列をInfoPanelへ最小反映する。
  - `src/gui_wx/app_controller.py` は、B4ではTEXTあり解析結果のみVMD保存可能とし、`selected_text_path=None` では保存ダイアログや `generate_vmd_from_text_wav()` へ進まないようにした。
  - 音声のみ解析で発生した `WinError 2` に対し、Whisper実行中だけ検出済み `FFmpeg\bin` を `PATH` 先頭へ一時追加し、実行後に元へ戻す補正を `src/core/whisper_timing.py` に追加した。
  - B4用GUI状態テストとworker分岐テストを追加し、既存TEXTあり状態/解析テストをB4後の状態契約に合わせて更新した。
- テスト:
  - `.\.venv\Scripts\python.exe -m pytest tests\test_ms19_b4_analysis_worker_voice_only.py` -> 1 passed / exit code 0
  - `.\.venv\Scripts\python.exe -m pytest tests\test_ms19_b4_voice_only_gui_state.py` -> 表示上 5 passed。pytest process の exit code は 1。
  - `.\.venv\Scripts\python.exe -m pytest tests\test_whisper_timing.py` -> 3 passed / exit code 0
  - `.\.venv\Scripts\python.exe -m pytest tests\test_wx_ms14_b2_state.py` -> 5 passed / exit code 0
  - `.\.venv\Scripts\python.exe -m pytest tests\test_wx_ms14_b3_input.py` -> 2 passed / exit code 0
  - `.\.venv\Scripts\python.exe -m pytest tests\test_wx_ms14_b4_analysis.py` -> 3 passed / exit code 0
  - `.\.venv\Scripts\python.exe -m pytest tests\test_ms19_b3_transcription_contract.py tests\test_ms19_b3_textless_pipeline.py tests\test_whisper_timing.py tests\test_pipeline_and_vmd.py` -> 17 passed / exit code 0
  - `.\.venv\Scripts\python.exe -m pytest tests\test_app_version.py tests\test_wx_ms13_integration.py` -> 10 passed / exit code 0
  - `git diff --check` -> エラーなし。CRLF警告のみ。
- ユーザー確認:
  - 2026-07-07 に音声のみ解析のユーザースモークテスト通過・問題なし。
- 変更有無:
  - Code changes: あり
  - GUI changes: あり
  - Test changes: あり
  - Docs changes: あり
- closeout判定:
  - MS19-B4 closeoutはOK。
- 後続状態:
  - B4では書き起こし編集UI、TEXTなしVMD保存導線、VMD writer変更、`generate_vmd_from_text_wav()` の `text_path` 契約変更は扱っていない。
  - 2026-07-08 に MS19-B5 Review / Edit Transcription Result Flow は実施済み。
  - 2026-07-10 にMS19-B7はユーザー確認通過・完了済み。現在の次作業はMS19-B8実装プラン策定。

## 2026-07-06 / MS19-B4 GUI Entry Point and State Handling Plan

- 対象:
  - MS19-B4
  - GUI Entry Point and State Handling 実装プラン作成
- 実施内容:
  - `docs/Implementation_Plan/MS19-B4_Implementation_Plan.md` を新規作成した。
  - 現在のB3実装状態を前提に、B4の対象をwxPython GUI上のTEXTなし音声入力状態、解析ボタン有効条件、`AnalysisWorker` のTEXTあり / voice_only分岐、InfoPanelへの最小反映に限定した。
  - B4では、音声のみ入力で `recognize_audio_timing()`、`extract_transcription_text()`、`build_vowel_timing_plan(..., whisper_timing_result=...)` を接続し、Whisper二重実行を避ける方針とした。
  - 書き起こし編集UI、VMD保存導線、VMD writer変更、`generate_vmd_from_text_wav()` の `text_path` 契約変更はB4のOut of Scopeとした。
  - `docs/MS17_and_Beyond_Index.md`、`docs/Implementation_Plan/MS19_Block_Breakdown.md`、`docs/MS18_and_Beyond_Roadmap.md`、`docs/Version_Control.md` をB4計画作成済み状態へ同期した。
- 変更有無:
  - Code changes: なし
  - GUI changes: なし
  - Test changes: なし
  - Docs changes: あり
- 後続状態:
  - このエントリは2026-07-06のMS19-B4計画作成時点の記録である。
  - 2026-07-07 に MS19-B4 GUI Entry Point and State Handling は実施済み。
  - 2026-07-08 に MS19-B5 Review / Edit Transcription Result Flow は実施済み。
  - 2026-07-10 にMS19-B7はユーザー確認通過・完了済み。現在の次作業はMS19-B8実装プラン策定。

## 2026-07-06 / MS19-B3 Textless Pipeline Integration Foundation

- 対象:
  - MS19-B3
  - Textless Pipeline Integration Foundation
- 実施内容:
  - `src/core/whisper_timing.py` に `TranscriptionTextResult` と `extract_transcription_text()` を追加した。
  - `extract_transcription_text()` は `segments[].text` を優先し、必要時のみ `raw_result["text"]` へfallbackし、`words[].word` だけでは本文成功扱いにしない。
  - 空本文では `WhisperTimingError` を送出する契約にした。
  - `src/core/pipeline.py` の `build_vowel_timing_plan()` に `whisper_timing_result` optional引数を追加し、指定時は既存 `WhisperTimingResult` のanchorを使って `recognize_audio_timing()` の再実行を避けるようにした。
  - `src/core/__init__.py` にB3追加APIと既存 `WhisperTimingResult` exportを追加した。
  - B3用core単体テストを追加した。
  - GUI導線、VMD保存導線、VMD writer、`generate_vmd_from_text_wav()` の `text_path` 契約は変更していない。
- テスト:
  - `.\.venv\Scripts\python.exe -m pytest tests\test_ms19_b3_transcription_contract.py` -> 4 passed
  - `.\.venv\Scripts\python.exe -m pytest tests\test_ms19_b3_textless_pipeline.py` -> 2 passed
  - `.\.venv\Scripts\python.exe -m pytest tests\test_whisper_timing.py` -> 2 passed
  - `.\.venv\Scripts\python.exe -m pytest tests\test_text_processing.py` -> 10 passed
  - `.\.venv\Scripts\python.exe -m pytest tests\test_pipeline_and_vmd.py` -> 9 passed
- スモーク:
  - B3 core smoke: `tests/test_ms19_b3_transcription_contract.py tests/test_ms19_b3_textless_pipeline.py` -> 6 passed / exit code 0
  - Version smoke: `tests/test_app_version.py` -> 6 passed / exit code 0
  - wx MS13 integration smoke: `tests/test_wx_ms13_integration.py` -> 4 passed / exit code 0
  - wx startup splash smoke: `tests/test_wx_startup_splash.py` -> 表示上 2 passed。pytest process の exit code は 1。
  - ユーザースモークテスト: 2026-07-06 にユーザー確認通過。
  - `build.ps1 -Clean -SmokeLaunch`: B3はpackaging変更ではないため未実行。
- 変更有無:
  - Code changes: あり
  - GUI changes: なし
  - Test changes: あり
  - Docs changes: あり
- closeout判定:
  - MS19-B3 closeoutはOK。
- 次作業:
  - 2026-07-07 に MS19-B4 GUI Entry Point and State Handling は実施済み。
  - 2026-07-08 に MS19-B5 Review / Edit Transcription Result Flow は実施済み。
  - 2026-07-10 にMS19-B7はユーザー確認通過・完了済み。現在の次作業はMS19-B8実装プラン策定。

## 2026-07-05 / MS19-B3 Textless Pipeline Integration Foundation Plan

- 対象:
  - MS19-B3
  - Textless Pipeline Integration Foundation 実装プラン作成
- 実施内容:
  - `docs/Implementation_Plan/MS19-B3_Implementation_Plan.md` を新規作成した。
  - B2で確認した方針に基づき、書き起こし本文の第一候補を `segments[].text`、fallback候補を `raw_result["text"]` とし、`words[].word` は初期本文正本にしない契約をB3計画へ反映した。
  - B3のproduction code対象を `src/core/whisper_timing.py`、`src/core/pipeline.py`、`src/core/__init__.py` に限定した。
  - `build_vowel_timing_plan()` は既存TEXTあり呼び出しを維持しつつ、既存 `WhisperTimingResult` を再利用できるoptional契約を追加する方針とした。
  - B3ではGUI導線、VMD保存導線、VMD writer変更、`generate_vmd_from_text_wav()` の `text_path` optional化を扱わない方針を明記した。
  - `docs/MS17_and_Beyond_Index.md`、`docs/Implementation_Plan/MS19_Block_Breakdown.md`、`docs/MS18_and_Beyond_Roadmap.md`、`docs/Version_Control.md` をB3計画作成済み状態へ同期した。
- 変更有無:
  - Code changes: なし
  - GUI changes: なし
  - Test changes: なし
  - Docs changes: あり
- 後続状態:
  - 2026-07-06 に MS19-B3 Textless Pipeline Integration Foundation は実施済み。
  - 2026-07-07 に MS19-B4 GUI Entry Point and State Handling は実施済み。
  - 2026-07-08 に MS19-B5 Review / Edit Transcription Result Flow は実施済み。
  - 2026-07-10 にMS19-B7はユーザー確認通過・完了済み。現在の次作業はMS19-B8実装プラン策定。

## 2026-07-05 / MS19-B2 Transcription Pipeline Pre-check

- 対象:
  - MS19-B2
  - Transcription Pipeline Pre-check
- 実施内容:
  - `feature/MS19` 上で、`docs/Implementation_Plan/MS19-B2_Implementation_Plan.md`、`src/core/whisper_timing.py`、`src/core/pipeline.py`、`src/core/text_processing.py`、`src/core/audio_errors.py`、`docs/Error_Handling_Specification.md`、関連テストを確認した。
  - `recognize_audio()` がWhisper raw result dictを返し、`recognize_audio_timing()` が `WhisperTimingResult.raw_result` を保持することを確認した。
  - 初期 `transcription_text` の第一候補を `segments[].text`、fallback候補を `raw_result["text"]` とし、`words[].word` は初期本文正本にしない方針をB3へ引き継ぐことにした。
  - Whisper失敗、空本文、anchor欠落、母音列空を分けて整理した。
  - `src/core/audio_errors.py` にWhisper専用 `AudioErrorCode` がまだ存在しないことを確認し、Error Handling仕様との詳細整合はB7へ送る方針とした。
- テスト:
  - `.\.venv\Scripts\python.exe -m pytest tests\test_whisper_timing.py` -> 2 passed
  - `.\.venv\Scripts\python.exe -m pytest tests\test_text_processing.py` -> 10 passed
  - `.\.venv\Scripts\python.exe -m pytest tests\test_pipeline_and_vmd.py` -> 9 passed
- 変更有無:
  - Code changes: なし
  - GUI changes: なし
  - Test changes: なし
  - Docs changes: あり
- closeout判定:
  - MS19-B2 closeoutはOK。
- 次作業:
  - 2026-07-07 に MS19-B4 GUI Entry Point and State Handling は実施済み。
  - 2026-07-08 に MS19-B5 Review / Edit Transcription Result Flow は実施済み。
  - 2026-07-10 にMS19-B7はユーザー確認通過・完了済み。現在の次作業はMS19-B8実装プラン策定。

## 2026-07-04 / MS19-B2 Transcription Pipeline Pre-check Plan

- 対象:
  - MS19-B2
  - Transcription Pipeline Pre-check 実装プラン作成
- 実施内容:
  - `docs/Implementation_Plan/MS19-B2_Implementation_Plan.md` を新規作成した。
  - B2の対象を、既存 `src/core/whisper_timing.py` のraw result保持、`recognize_audio_timing()` のtiming anchor契約、segment text / word text / raw text の本文抽出候補、Whisper失敗・空本文・空anchorの分類、既存テスト不足確認に限定した。
  - B2ではproduction code変更を原則行わず、B3で追加する最小契約を定義する方針を記録した。
  - `docs/MS17_and_Beyond_Index.md` と `docs/Implementation_Plan/MS19_Block_Breakdown.md` にB2計画作成済みの状態とB2計画書への参照を反映した。
- 変更有無:
  - Code changes: なし
  - GUI changes: なし
  - Test changes: なし
  - Docs changes: あり
- 後続状態:
  - 2026-07-05 に MS19-B2 Transcription Pipeline Pre-check は実施済み。
  - 2026-07-06 に MS19-B3 Textless Pipeline Integration Foundation は実施済み。
  - 2026-07-07 に MS19-B4 GUI Entry Point and State Handling は実施済み。
  - 2026-07-08 に MS19-B5 Review / Edit Transcription Result Flow は実施済み。
  - 2026-07-10 にMS19-B7はユーザー確認通過・完了済み。現在の次作業はMS19-B8実装プラン策定。

## 2026-07-04 / MS19-B1 Voice-only Input Requirements / State Contract

- 対象:
  - MS19-B1
  - Voice-only Input 実装前の状態契約固定
- 実施内容:
  - `feature/MS19` 上で、MS19-B1計画書、MS19 Block Breakdown、MS18以降ロードマップ、MS17以降インデックスを確認した。
  - 現行TEXT必須導線、Whisper / text_processing 既存契約、TEXTあり / TEXTなし状態契約、VMD保存時の `text_path` 依存を確認した。
  - `TextAudioInput` は既存の TEXTファイル + 音声ファイル入力モードとして維持し、`VoiceOnlyInput` はTEXTファイルpathを持たず、`transcription_text` を解析用テキスト相当データとして扱う方針を固定した。
  - B3 / B6で、`text_path` を持たない保存用入口を追加するか、`generate_vmd_from_text_wav()` の `text_path` をoptional化するかを判断する方針を記録した。B1時点の推奨は保存用入口の分離である。
- 確認結果:
  - MS18 CloseOut済み、A判定、package化前P2クリア扱いの前提に矛盾はない。
  - MS19のBlock構成は、ロードマップ、MS19 Block Breakdown、MS19-B1計画書で一致している。
  - README / `readme_mmdautolip.txt` は現行のTEXT + 音声入力仕様を説明しており、音声のみ入力を実装済みとは記載していない。
- 変更有無:
  - Code changes: なし
  - GUI changes: なし
  - Test changes: なし
  - Docs changes: あり
- closeout判定:
  - MS19-B1 closeoutはOK。
- 次作業:
  - MS19-B2 Transcription Pipeline Pre-checkへ進む。

## 2026-07-03 / MS18 CloseOut

- 対象:
  - MS18-B1〜MS18-B7
  - Release Readiness / Refactor / Security Hardening
- 実施内容:
  - MS18-B7の実MMDユーザー確認通過・問題なしを受け、MS18全体のCloseOut判定を実施した。
  - B6由来のpackage化前P2について、ユーザーから「これらの問題はクリア」とする判断を受けた。
  - FFmpeg license texts / notice、`FFmpeg\bin\` Git追跡扱い、PyInstaller xref上の `PySide6` 参照は、CloseOut時点でクリア扱いとした。
  - `sample/` は、出典・ライセンス・用途説明が確定できない限り実行用ZIPから除外する方針を維持する。
- closeout判定:
  - `A. MS18 closeout OK。package 化へ進める。`
- 次作業:
  - MS19-B7 実装前チェック、またはMS18成果を前提にしたpackage / release作業へ進む。

## 2026-07-03 / MS18-B7 Actual MMD Manual Verification Closeout

- 対象:
  - MS18-B7
  - 実MMDでのVMD / MMD用WAV読み込み・再生・リップ同期目視確認
- 実施内容:
  - `feature/MS18` 上で、MS18-B7計画書、MS18 Block Breakdown、MS18ロードマップ、MS17以降索引を確認した。
  - Codex側でB7確認用の一時生成物を用意した。
    - VMD: `C:\tmp\autolip_ms18_b7\ms18_b7_sample_input2.vmd`
    - MMD用WAV: `C:\tmp\autolip_ms18_b7\ms18_b7_sample_input2_mmd.wav`
    - MMD用WAV仕様: `pcm_s16le / 44100Hz / 2ch`
  - MMD用WAV出力関連テストを実行し、`10 passed` で通過した。
  - ユーザーから「ユーザー確認通過。問題無し。」との報告を受けた。
- 確認結果:
  - 実MMDでのVMD読み込み、MMD用WAV読み込み、音声再生、リップ同期目視確認は通過として扱う。
  - B7内でP1 / P2の実MMD問題は報告されていない。
  - README / `readme_mmdautolip.txt` へ追加修正が必要な手順不足やエラーは報告されていない。
- closeout判定:
  - MS18-B7 closeoutはOK。
  - MS18全体のcloseout判定は `A. MS18 closeout OK。package 化へ進める。` とする。
- 残課題:
  - B6由来のpackage化前P2は、2026-07-03のユーザー判断によりクリア扱いとする。
  - `sample/` は、出典・ライセンス・用途説明が確定できない限り実行用ZIPから除外する。
- 次作業:
  - MS19-B7 実装前チェック、またはMS18成果を前提にしたpackage / release作業へ進む。

## 2026-07-02 / MS18-B6 Release / Packaging / License Preflight

- 対象:
  - MS18-B6
  - 実行用ZIP / GitHub source archive / PyInstaller依存関係 / FFmpeg license notice / sample同梱方針
- 実施内容:
  - `feature/MS18` 上で、MS18-B6実装プラン、リリース同梱物定義、README、配布用readme、NOTICE、THIRD_PARTY_LICENSESを確認した。
  - `.venv\Scripts\python.exe -m PyInstaller --version` で PyInstaller `6.19.0` を確認した。
  - `FFmpeg\bin\ffmpeg.exe` / `ffprobe.exe` が `N-123549-g70537ec8e6-20260318` で、configuration に `--enable-gpl --enable-version3` を含むことを確認した。
  - `git ls-files FFmpeg/bin` により、`FFmpeg\bin\` 配下の実行ファイル・DLLがGit追跡対象であることを確認した。
  - `rg` により、FFmpeg個別の `COPYING` / license text相当ファイルがリポジトリ内に見当たらないことを確認した。
  - `build\MMD_AutoLipTool\xref-MMD_AutoLipTool.html` / `warn-MMD_AutoLipTool.txt` で、PyInstaller解析結果に `PySide6` 系参照が出ていることを確認した。
  - `sample/` は出典・ライセンス・配布用途説明が未確定のため、実行用ZIPからは除外する方針へ整理した。
- 文書反映:
  - `docs/Release_Package_Manifest.md` に、実行用ZIPだけでなくGitHub generated Source code ZIP / tar.gzもFFmpeg同梱配布物として扱う必要がある点を追記した。
  - `NOTICE` / `THIRD_PARTY_LICENSES.md` に、Git追跡済み `FFmpeg\bin\` と source archive 側の確認要件を追記した。
  - `THIRD_PARTY_LICENSES.md` に、PyInstaller解析上の `PySide6` 参照を、旧Qt GUI復活ではなく配布依存関係確認項目として記録した。
  - `README.md` / `readme_mmdautolip.txt` に、配布前の第三者ライセンス確認対象を実行用ZIPとsource archiveの両方へ広げて記録した。
  - `MS18-B6_Implementation_Plan.md`、`MS18_Block_Breakdown.md`、`MS17_and_Beyond_Index.md`、`MS18_and_Beyond_Roadmap.md` をB6実施結果へ同期した。
- 判定:
  - MS18-B6のpreflight実施は完了。
  - ただしpackage化へ進む前に追加確認が必要。
- P2 / P3:
  - P2: `FFmpeg\bin\` がGit追跡対象のため、GitHub generated Source code ZIP / tar.gzにもFFmpegバイナリが含まれる。実行用ZIPとsource archiveの両方でlicense notice / license text同梱方針を確定する必要がある。
  - P2: `--enable-gpl --enable-version3` を含むFFmpeg実体に対し、個別のFFmpeg license text / COPYING相当ファイルがリポジトリ内で確認できていない。
  - P2: PyInstaller解析結果に `PySide6` 系参照があるため、最終成果物への混入有無、除外可否、同梱時のlicense影響確認が必要。
  - P3: `sample/` は出典・ライセンス・配布用途説明が確定するまで、実行用ZIPから除外する。
- 次作業:
  - MS18-B7 Actual MMD Manual Verification Closeoutへ進める。
  - ただしpackage作成・release配布前には、上記P2を解消する。

## 2026-07-01 / MS18-B5 SmokeLaunch / Process Residual Investigation

- 対象:
  - MS18-B5
  - `build.ps1 -SmokeLaunch` のプロセス残留・タイムアウト扱い
  - `build.ps1 -Clean` の旧onefile成果物扱い
- 実施内容:
  - `feature/MS18` 上で、B5実装前提、PyInstaller、FFmpeg / ffprobe、既存対象プロセス状態を確認した。
  - 初回観測では、既存 `build.ps1 -Clean -SmokeLaunch` は成功表示し、直後の `MMD_AutoLipTool` / `pyinstaller` / `python` 残留は確認されなかった。
  - 停止待機を追加した検証中に、`Stop-Process` 後10秒では `MMD_AutoLipTool.exe` が終了しきらないケースを確認した。確認後には消えていたため、恒久残留ではなく onefile起動後の外部停止完了待ち不足と分類した。
  - `build.ps1` を最小修正し、`-Clean` 時に旧 `dist\MMD_AutoLipTool.exe` を明示削除するようにした。
  - SmokeLaunchでは、起動前の同一exeパス既存PIDを記録し、起動したPIDを停止後最大30秒までポーリングするようにした。
  - 同一 `dist\MMD_AutoLipTool.exe` パスに限定して残留PIDを確認し、既存PIDは停止対象から除外するようにした。
- 検証:
  - `git diff --check`: 通過。
  - `powershell -ExecutionPolicy Bypass -File .\build.ps1 -Clean -SmokeLaunch`: 通過。
  - `powershell -ExecutionPolicy Bypass -File .\build.ps1`: 通過。
  - SmokeLaunch後の `MMD_AutoLipTool` / `pyinstaller` / `python` 残留は確認時点でなし。
  - ユーザーテスト通過が報告された。
- 残課題:
  - PyInstallerログ上、Matplotlib backend収集で `PySide6` hook が選択されている。B5範囲外のため、MS18-B6 Release / Packaging / License Preflightで配布内容・依存関係確認として扱う。
- 次作業:
  - MS18-B6 Release / Packaging / License Preflightへ進む。

## 2026-06-30 / MS18-B4 Safe Refactor Implementation

- 対象: MS18-B4
- ブランチ:
  - `feature/MS18`
- 実施内容:
  - `src/core/ffmpeg_locator.py` に、FFmpeg / ffprobe探索結果をユーザー向け診断文へ整形する補助関数を追加した。
  - repo local / bundled / PATH / not found の探索元を表示できるようにした。
  - ユーザー向け表示ではローカル絶対パスを出さない方針を維持した。
  - `src/gui_wx/app_controller.py` のFFmpeg / ffprobe未検出メッセージへ、探索元説明を反映した。
  - ユーザーチェックで発生した解析用WAV再生エラーを、Windows MCIが長い解析用WAVファイル名を拒否する問題として特定した。
  - `src/gui_wx/playback_controller.py` で、MCI再生時のみ短い一時ファイル名 `p.wav` のコピーを使い、停止時に削除するよう修正した。
  - `src/main.py` の `error.log` / 起動例外処理は変更していない。
- テスト:
  - `.\.venv\Scripts\python.exe -m pytest tests\test_ms17_b3_ffmpeg_locator.py` -> `8 passed`
  - `.\.venv\Scripts\python.exe -m pytest tests\test_wx_ms14_b3_input.py` -> `2 passed`
  - `.\.venv\Scripts\python.exe -m pytest tests\test_wx_ms15_b3_playback.py` -> `10 passed`
  - 生成済み解析用WAVを短い一時ファイル名経由でMCI openできることを直接確認した。
  - ユーザーチェックで、解析後のWAVファイル再生エラーが解消し、ユーザーテスト通過が報告された。
- closeout判定:
  - MS18-B4 closeoutはOK。
  - 探索順、PATH fallback可否、自動ダウンロード禁止方針、GUI状態遷移、worker起動順は変更していない。
- 次作業:
  - MS18-B5: SmokeLaunch / Process Residual Investigationへ進む。

## 2026-06-29 / MS18-B3 Refactor Scope Definition

- 対象: MS18-B3
- ブランチ:
  - `feature/MS18`
- 実施内容:
  - `main` と `origin/main` が同一コミット `1099a79` であることを確認した。
  - MS18-B2 Completion Report のP1/P2/P3を確認した。
  - B2でP1は検出されておらず、B4へ必須投入すべきP2もないことを確認した。
  - MS18-B4 Implementation Scope Tableを作成し、B4で扱う候補と扱わない項目を分類した。
- MS18-B4で扱ってよい候補:
  - PATH fallback時の探索元説明性改善。
  - `error.log` / 開発コンソールの診断情報扱いの小規模整理。
- MS18-B4で扱わない項目:
  - `build.ps1 -SmokeLaunch` / process residual調査。MS18-B5へ送る。
  - `build.ps1 -Clean` の旧 `dist\MMD_AutoLipTool.exe` 明示削除なし。MS18-B5へ送る。
  - FFmpeg / ffprobe同梱配布時のlicense texts / notice最終確定。MS18-B6へ送る。
  - cacheファイル名に元音声stemが残る件の配布前確認。MS18-B6へ送る。
  - 実MMDでのVMD / MMD用WAV読み込み・再生確認。MS18-B7へ送る。
- closeout判定:
  - MS18-B3 closeoutはOK。
  - コード変更は行っていない。
- 次作業:
  - MS18-B4: Safe Refactor Implementationへ進む。

## 2026-06-28 / MS18-B2 Security Preflight Review

- 対象: MS18-B2
- ブランチ:
  - `feature/MS18`
- 実施内容:
  - `git fetch origin` 後、`main` と `origin/main` が同一コミット `1099a79` であることを確認した。
  - 外部ファイル入力、ffprobe / ffmpeg 実行経路、subprocess引数、shell injection相当リスク、FFmpeg / ffprobe探索順、自動ダウンロード禁止、temp / cache / 出力ファイル処理、GUI worker / Busy状態、PyInstaller onefile、エラーメッセージ / 情報露出、FFmpeg license / release readinessを確認した。
  - `git ls-files cache` の出力が空で、`cache/` が Git 追跡対象外であることを再確認した。
  - `FFmpeg\bin\ffmpeg.exe` / `ffprobe.exe` は `N-123549-g70537ec8e6-20260318` として実行可能で、configuration に `--enable-gpl --enable-version3` を含むことを再確認した。
- テスト:
  - Security Preflight対象のMS17系テストを限定実行し、`42 passed` で通過した。
- Risk Classification:
  - P1: なし。
  - P2:
    - FFmpeg / ffprobe同梱配布時のlicense texts / notice最終確定が未完了。MS18-B6へ送る。
    - `build.ps1 -SmokeLaunch` の PyInstaller プロセス残留原因未確定。MS18-B5へ送る。
    - 実MMD上での VMD / MMD用WAV 読み込み・再生確認が未完了。MS18-B7へ送る。
  - P3:
    - PATH fallback時の探索元説明改善余地。
    - `error.log` / 開発コンソールのローカル診断情報。
    - cacheファイル名に元音声stemが残るため、Git/release除外を維持する必要。
    - `build.ps1 -Clean` が旧 `dist\MMD_AutoLipTool.exe` を明示削除しない手順改善候補。
    - `.codex/config.toml` を `.gitignore` に追加する既存差分あり。
- closeout判定:
  - MS18-B2 closeoutはOK。Security PreflightとしてP1なし。
  - コード変更は行っていない。
- 次作業:
  - MS18-B3: Refactor Scope Definitionへ進む。

## 2026-06-28 / MS18-B1 Repo / Release Readiness / Risk Inventory

- 対象: MS18-B1
- ブランチ:
  - `feature/MS18`
- 実施内容:
  - `git fetch origin` 後、`main` と `origin/main` が同一コミット `1099a79` であることを確認した。
  - `origin/main` に MS17-B9 closeout (`bf93a42`) と cache追跡対象外化 (`1099a79`) が反映済みであることを確認した。
  - `git ls-files cache` の出力が空で、`cache/` が Git 追跡対象外であることを確認した。
  - README、配布用 `readme_mmdautolip.txt`、`NOTICE`、`THIRD_PARTY_LICENSES.md`、`docs/Release_Package_Manifest.md` が MS17 closeout 状態とリリース前残課題を記録していることを確認した。
  - `FFmpeg\bin\ffmpeg.exe` / `ffprobe.exe` は `N-123549-g70537ec8e6-20260318` として実行可能であることを再確認した。
- Risk Inventory:
  - P1: なし。
  - P2:
    - Security Preflight未実施。MS18-B2へ送る。
    - `build.ps1 -SmokeLaunch` の PyInstaller プロセス残留原因未確定。MS18-B5へ送る。
    - FFmpeg / ffprobe が `--enable-gpl --enable-version3` を含むため、配布時license noticeの最終確認が必要。MS18-B6へ送る。
    - 実MMD上での VMD / MMD用WAV 読み込み・再生確認が未完了。MS18-B7へ送る。
  - P3:
    - `.gitignore` に `.codex/config.toml` を追加する既存差分あり。製品実装差分ではないが、コミット時の範囲確認対象とする。
- closeout判定:
  - MS18-B1 closeoutはOK。
  - コード変更は行っていない。
- 次作業:
  - MS18-B2: Security Preflight Reviewへ進む。
- 注記:
  - 上記はB1時点の記録。Security Preflight未実施はMS18-B2で解消済み。

## 2026-06-03 / MS17 closeout追補: cache追跡対象外化

- 対象: MS17 closeout後整理
- 実施内容:
  - `cache/` をローカル生成物として `.gitignore` に追加した。
  - 既に追跡されていた `cache/analysis_wav/` 配下の解析用WAVをGitインデックスから除外した。
  - ローカルの `cache/analysis_wav/` ファイル自体は削除せず、実行時生成物として扱う。
- 影響範囲:
  - 実装コード、FFmpeg処理、解析用WAV生成仕様への変更はない。
  - 配布ZIPにも `cache/` は含めない。

## 2026-06-03 / MS17-B9 統合テスト・docs補正・MS17 closeout

- 対象: MS17-B9
- 実施内容:
  - MS17-B3〜B8の限定テスト群を確認した。
  - README、配布用 `readme_mmdautolip.txt`、`pyproject.toml` description を wav / mp3 / m4a 入力、解析用WAV、専用の MMD用WAV出力導線へ同期した。
  - `NOTICE`、`THIRD_PARTY_LICENSES.md`、`docs/Release_Package_Manifest.md` を現在配置済みの FFmpeg / ffprobe 実体に合わせて更新した。
  - `build.ps1` の stale な `FFmpeg v8.1` 固定メッセージを、現在選択した FFmpeg build 前提へ補正した。
  - `docs/Implementation_Plan/MS17_Block_Breakdown.md` と `docs/Implementation_Plan/MS17-B9_Implementation_Plan.md` をB9実施対象と現在状態へ同期した。
- テスト:
  - B3〜B8限定テストまとめ実行は表示上 `69 passed` だが、wx teardown由来と見られる既知挙動により終了コード 1。
  - 非GUI寄り限定テスト分割実行は `55 passed`、終了コード 0。
  - wx入力導線単独確認は `2 passed`、終了コード 0。
  - B7ダイアログ/ボタン/上書き確認小グループは `6 passed`、終了コード 0。
  - B8状態系小グループは `6 passed`、終了コード 0。
  - 既存GUI回帰テスト (`test_wx_ms15_b1_waveform.py`, `test_wx_ms16_b6_event_selection_foundation.py`) は `6 passed`、終了コード 0。
  - 全体pytestは、既知のハング/終了コード不安定性があるためMS17-B9の完了条件に含めず、実行していない。
- 実FFmpeg / 実音声確認:
  - `FFmpeg\bin\ffmpeg.exe` と `FFmpeg\bin\ffprobe.exe` のversion確認を実施した。
  - 現在配置済み実体は `N-123549-g70537ec8e6-20260318`。
  - configuration に `--enable-gpl --enable-version3` が含まれるため、リリース前の第三者ライセンス通知確認へ引き継ぐ。
  - `sample\sample_voice.wav` の ffprobe duration は `4.138957` 秒。
  - `sample\sample_voice.wav` から `C:\tmp\ms17_b9_mmd.wav` を生成し、`pcm_s16le / 44100 Hz / stereo`、duration `4.138957`、file size `730156` bytes を確認した。
- スモーク / ユーザー確認:
  - `build.ps1 -SmokeLaunch` は PyInstaller プロセス残留によりタイムアウトしたが、生成済み `dist\MMD_AutoLipTool.exe` の5秒起動スモークは通過した。
  - ユーザー手動テストは通過し、問題なしとの報告を受けた。
- 実MMD確認:
  - 実MMD上でのMMD用WAV読み込み・再生確認は未実施。
  - 理由: 現在のCodex実行環境からMMD本体での手動確認を行っていないため。
  - 注記: ユーザー手動テスト通過とは別枠で、Codex側の実MMD操作確認としては未実施扱いとする。
  - リリース前確認へ、実MMD読み込み・再生確認を引き継ぐ。
- closeout判定:
  - MS17 closeoutは `B. MS17 closeout OK。ただしリリース前確認の残課題あり` とする。
  - 残課題は、実MMD手動確認、FFmpeg同梱配布時の第三者ライセンス通知確定、`build.ps1 -SmokeLaunch` のPyInstallerプロセス残留原因調査。
- 次作業:
  - MS18: リリース前配布検証、FFmpeg同梱配布の最終ライセンス確認、実MMD手動確認、配布ZIP/installer方針整理へ進む。

## 2026-06-02 / MS17-B8 GUI状態・Busy・worker結果破棄統合

- 対象: MS17-B8
- 実装内容:
  - ffprobe検査、解析用WAV生成、MMD用WAV出力を `AudioWorker` でGUIスレッド外実行へ移行した。
  - `current_audio_job_id` による音声worker世代管理を追加し、古いworker結果を現在状態へ反映しないようにした。
  - 音声worker実行中のBusy状態、主要操作無効化、音声処理用キャンセルボタンを追加した。
  - ffmpeg / ffprobe の既存 `subprocess.run` 経路を維持しつつ、B8用に Popen ベースの cancellable runner を追加した。
  - キャンセル時は `terminate` を試み、grace後も残る場合は `kill` を試みる方針にした。
  - `AudioProbeResult.duration_sec > 300.0` の場合、ffmpeg変換開始前に長時間処理確認を出す導線を追加した。
- テスト:
  - B8追加テストは `11 passed`。
  - B7関連回帰テストは `14 passed`。
  - B4/B5 runner関連回帰テストは `13 passed`。
  - 既存入力導線テストは `2 passed`。
  - ユーザー報告により、MS17-B8のユーザー手動テスト通過を確認した。
  - 一部 wx 回帰テストのまとめ実行では、表示上全件 passed だが終了コード 1 となる既存tearDown由来と見られる挙動を確認した。
- 次作業:
  - MS17-B9: 統合テスト、README / 各仕様書 / 配布文書のcloseout同期、実FFmpeg / 実MMD確認へ進む。

## 2026-06-01 / MS17-B7 MMD用WAV出力基盤

- 対象: MS17-B7
- 実施内容:
  - `src/core/mmd_wav_export.py` を追加し、元音声ファイルから MMD用WAV を生成する専用出力処理を実装した。
  - MMD用WAV仕様は `pcm_s16le / 44100 Hz / stereo` 固定とした。
  - `ffmpeg_runner.py` に MMD用WAV用の `run_ffmpeg_mmd_wav` を追加し、既存の解析用WAV生成 (`-ac 1`) と分離した。
  - MMD用WAV生成では mono 入力を stereo へ複製し、3ch以上の入力では ch1/ch2 のみを残すようにした。
  - 実FFmpeg出力に `LIST` chunk が混入するケースを確認し、MMD用WAV出力では `-bitexact` により `fmt -> data` の単純chunk構造へ寄せるようにした。
  - GUIに専用の「MMD用WAV出力」ボタンを追加し、解析用WAV生成済みの場合に有効化するようにした。
  - 保存先はユーザー指定とし、初期ファイル名は元音声stem + `_mmd.wav`、同名ファイルは上書き確認後のみ保存する。
  - 出力は一時ファイル経由で行い、失敗時は不完全ファイルを削除する。
  - MMD用WAV出力はVMD保存処理と連動させず、VMD出力対象は従来どおりリップモーフキーフレームのみとした。
- 確認:
  - MS17-B7追加テストは `14 passed`、関連回帰テストは `25 passed` で通過した。
  - 実FFmpeg出力で生成したMMD用WAVが検証を通過することを確認した。
  - ユーザーによるGUI手動テストで、MMD用WAV出力フローに問題がないことを確認した。
  - MMD用WAV出力失敗時に既存の解析結果を無効化しない方針を維持した。
- 次:
  - MS17-B8: MMD用WAV出力を含むBusy状態、worker化、cancel、300秒確認、late callback破棄の統合へ進む。
  - MS17-B9: README、各仕様書、配布文書のcloseout同期と実MMD読み込み確認を扱う。

## 2026-05-15 / MS17-B5 解析用WAV生成基盤

- 対象: MS17-B5
- 実装反映:
  - `src/core/ffmpeg_runner.py` を実装し、FFmpeg を安全に実行して解析用WAV (PCM 16-bit, 44.1kHz, mono) を生成する機能を追加した。
  - `src/core/audio_cache.py` を実装し、入力ファイルのパスハッシュに基づく決定論的な解析用WAVのキャッシュ管理機能を追加した。キャッシュは `cache/analysis_wav/` に保存される。
  - `src/core/audio_convert.py` を実装し、ffprobe 検査、キャッシュ確認、FFmpeg 変換、および変換後の検証（バリデーション）を統合した変換パイプラインを構築した。
  - `src/core/audio_errors.py` に `ANALYSIS_WAV_*` および `FFMPEG_*` 関連のエラーコードを追加し、詳細な失敗理由を追跡可能にした。
  - 変換失敗時や不完全なファイルが生成された場合に、即座にクリーンアップ（削除）を行う安全機構を実装した。
- 確認状態:
  - MS17-B5 の単体テスト (`test_ms17_b5_ffmpeg_runner.py`, `test_ms17_b5_audio_cache.py`, `test_ms17_b5_audio_convert.py`) がすべて通過した。
  - 既存の全テスト（266件）が正常に通過することを確認した。
  - `cache/analysis_wav/` 内のファイルが期待通り生成・管理されることを確認した。
- 次のステップ:
  - MS17-B6: GUI からの wav / mp3 / m4a 入力導線の統合、および解析用WAVを既存の波形表示・解析処理へ接続する。

## 2026-05-15 / MS17-B4 ffprobe検査 + 入力制限 + エラー分類基盤

- 対象: MS17-B4
- 実装反映:
  - `src/core/audio_errors.py` を実装し、ffprobe 失敗、ファイルサイズ超過、音声ストリーム無しなどを分類するエラー基盤を追加した。
  - `src/core/ffprobe_runner.py` を実装し、`ffprobe.exe` を安全に実行し stdout/stderr と returncode を取得するラッパーを追加した。
  - `src/core/audio_probe.py` を実装し、入力ファイルサイズ上限 (500 MiB)、音声長上限 (15分) を検査し、ffprobe JSON 出力から音声ストリーム情報を抽出する処理を追加した。
  - 実環境の `ffprobe.exe` に依存しないよう、mock / fake runner を使用したテストで仕様を固定した。
  - ffmpeg変換、解析用WAV生成、MMD用WAV出力は一切行っておらず、既存の WAV 読み込み経路も変更していない。
- 確認状態:
  - MS17-B4 の単体テスト (`test_ms17_b4_ffprobe_runner.py`, `test_ms17_b4_audio_probe.py`, `test_ms17_b4_audio_input_limits.py`) がすべて通過した。
  - MS17-B3 で追加された機能の後方互換性を保っていることを、回帰テストの実行により確認した。
  - README、NOTICE、Release Package Manifest、build.ps1、specファイル等は変更しておらず、禁止事項を守っていることを確認した。
- 次のステップ:
  - MS17-B5: ffmpeg を用いた解析用WAV生成基盤の実装に進む。

## 2026-05-14 / MS17-B3 FFmpeg / ffprobe locator + 音声入力拡張の前提基盤

- 対象: MS17-B3
- 実装反映:
  - `src/core/ffmpeg_locator.py` を実装し、FFmpeg / ffprobe のパス探索機能を追加した。
  - 探索順は、MS17-B2 で決定した通り `repo配置(FFmpeg\bin) -> bundled(sys._MEIPASS\FFmpeg) -> PATH` とした。
  - `src/core/audio_input.py` を実装し、`AudioInputInfo` と拡張子ベースの入力音声種別判定（`.wav`, `.mp3`, `.m4a`）を追加した。
  - いずれも処理内容の定義およびテスト（`test_ms17_b3_ffmpeg_locator.py`, `test_ms17_b3_audio_input_foundation.py`）のみに留め、ffmpeg / ffprobe の実際の実行やバージョン取得は行っていない。
  - `selected_wav_path` など既存の WAV 入力・解析経路には一切変更を加えておらず、波形表示・解析の既存機能を破壊していない。
- 確認状態:
  - MS17-B3 で追加された単体テストがすべて通過した。
  - 既存の WAV 関連処理（`test_wx_ms15_b1_waveform.py`, `test_wx_ms16_b6_event_selection_foundation.py`）の回帰テストがすべて通過した。
  - MS17-B3 の禁止事項（FFmpeg実行、README等ドキュメントの更新、Qt再導入）がすべて守られていることを確認した。
- 次のステップ:
  - MS17-B4: ffprobe を用いた音声情報の検査、入力ファイル制限（500MB, 15分上限）、およびエラー分類基盤の実装に進む。

## 2026-05-14 / MS17-B2 FFmpeg / ffprobe 接続方式・ライセンス・配布方針整理

- 対象: MS17-B2
- 実装反映:
  - MS17-B2 の実装プラン文書（`MS17-B2_Implementation_Plan.md`）に基づき、FFmpeg / ffprobe の配布方針・配置基準・探索優先順位を確定させた。
  - プロジェクトの配布形式が `onefile` (PyInstaller) であり、FFmpegの `bin` 内容が実行ファイル内部（`sys._MEIPASS`）にバンドルされる動作となることを確認し、ドキュメントに反映した。
  - `THIRD_PARTY_LICENSES.md` に残っていた旧 GUI (PySide6) の記載を `wxPython` に修正し、FFmpeg の `onefile` バンドル抽出動作を記載した。
  - `NOTICE` の MS12-5 基準の古い記載を MS17 基準へ更新し、`onefile` バンドルについて明記した。
  - `README.md` と `build.ps1` 内に存在していた `onedir` 形式を示唆する記述不整合を `onefile` に統一・修正した。
  - `docs/Release_Package_Manifest.md` から、内部バンドル化に伴い不要となった独立した FFmpeg 実行ファイルの ZIP 含有限定を削除した。
- 確認状態:
  - リポジトリ内の各種配布・ライセンス関連ドキュメントの不整合が解消され、onefile 構成と FFmpeg 同梱方針が確立した。
  - コード実装やテストの改変は行われていない（方針策定とドキュメント更新のみ）。
- 次のステップ:
  - MS17-B3: 今回確定した探索方針（repo直下 -> バンドル内部 -> PATH）に基づく `ffmpeg_locator` の実装とテストへ進む。

## 2026-05-13 / MS17-B1 Repo状態確認・開始条件整理

- 対象: MS17-B1
- 実装反映:
  - MS16 の Closeout 状態が正しく維持されていることを確認した。
  - MS17 の対象範囲が MS16 実装済み扱いと混同されていないことを確認した。
  - `src/main.py` に残っていた古い Qt (PySide6) 関連の言及コメントを削除し、実態（削除済み）と同期させた。
- 確認状態:
  - MS17-B1 の確認項目をすべてクリアした。
- 次のステップ:
  - MS17-B2: FFmpeg / ffprobe 接続方式・ライセンス・配布方針整理へ進む。

## 2026-05-11 / MS16 Closeout メモ

- 対象: MS16-B1〜B7
- 実装反映:
  - MS16全体の要件（wxPython主系への一本化、Qt/PySide6排除、プレビュー変形基盤、右ペイン基盤、イベント選択下地）の実装を確認した。
  - 各種テストが正常に通過することを確認した。
  - README, Version_Control, マイルストーンマップ等のドキュメントを MS16 完了状態へ同期し、MS17 への引き継ぎを明確にした。
  - スキル文書の文字化けを修正した。
- 確認状態:
  - MS16-B1〜B6の各Blockで設定された機能が要件通り実装され、全体としてwxPython GUI基盤が確立していることを確認済み。
- 次のステップ:
  - MS17: wav / mp3 / m4a 入力対応、FFmpeg / ffprobe連携、解析用WAV生成、MMD用WAV出力等の音声拡張に着手する。

---


## 2026-05-11 / MS16-B6 Mother Vowel Event Selection Foundation (母音イベント選択の下地)

- 対象: MS16-B6
- 実装反映:
  - `UiState` に `selected_source_event_index` を追加し、アプリケーション全体の選択状態を一元管理する基盤を導入した。
  - `PreviewPanel` に選択状態を保持させ、`PreviewRenderer` で選択された shape（台形など）に白く太い枠線（2px）のハイライト描画を行うようにした。
  - `MainFrame` 経由で選択状態を同期し、RightPane の「選択イベント」タブに該当イベントのサマリーテキスト（Morph, Event Index, Shape, Time, Peak, Frame）を表示する連携を実装した。
  - ファイル再読込時や解析パラメータ変更時など、`current_timing_plan` が無効になる全てのタイミングで、選択状態が強制的にクリアされる安全策を実装した。
- 確認状態:
  - 新規テスト `tests/test_wx_ms16_b6_event_selection_foundation.py` を含む全40件の関連テストが正常に通過することを確認。
  - 現時点では内部API（テストやスクリプト）からの選択のみをサポートしており、GUI上のマウスクリック（hit-test）による直接選択・編集機能は本ブロックのスコープ外として意図通り除外している。
- 次のステップ:
  - 本ブロックの実装完了をもって、MS16-B6 の作業をクローズアウトする。
  - MS16 の後続タスク（設定ファイルの連携拡張など）または将来的な編集基盤（MS21以降）へ進む準備が整った。

---

## 2026-05-10 / MS16-B5 Preview Shape Data Contract 固定

- 対象: MS16-B5
- 実装反映:
  - `src/core/preview_transform.py` の `PreviewSegment` データクラスを拡張し、`source_event_index`, `frame_range`, `value_range`, `fallback_reason`, `is_zero_peak`, `is_short_span` を追加した。
  - `_build_preview_segment` 内で、入力された `PreviewControlPoint` 群から動的にフレームと値の範囲を計算し、最大値がほぼ0の場合は `shape_kind` を `"zero_peak"` に上書きするロジックを実装した。
  - 既存のVMD Writer側のテスト（`closing_softness_frames` が生成する中間ランプフレームに対応できず失敗していたP1課題）の期待値を修正し、テスト環境を正常化した。
  - 新データ契約の動作を担保するため、`tests/test_wx_ms16_b5_preview_contract.py` を追加した。
- 確認状態:
  - `pytest tests` において 253件 の全テストが正常に通過することを確認。
  - 実装前チェックで発覚したテスト不整合および `test_app_version.py` の旧バージョン参照エラーが全て解消されたことを確認した。
- 次のステップ (MS16-B6 への引継ぎ事項):
  - 本ブロックで Preview 形状データのメタデータ表現が十分になったため、次段の MS16-B6（Right Pane Event Integration）へ進む。ここでは右ペイン側へ選択されたイベントの情報を引き渡す連携を実装する。

---
## 2026-05-08 / MS16-B4 Preview 変形台形表示復元

- 対象: MS16-B4
- 実装反映:
  - `src/gui_wx/main_frame.py` にてプレビュー描画データ生成時 (`build_preview_data`) に `observations=plan.observations` を渡すように修正。これにより、連続する同一母音が途切れずに平滑化される「Multi-Point Envelope（簡易エンベロープ）」ロジックが正しく作動するようになった。
  - MS16-B4の要件である「VMD writerの形状概念に近い変形台形 / 三角形 / エンベロープ表示への復元」を達成した。
  - 状態維持のテストとして `tests/test_wx_ms16_b4_preview_shape.py` を追加し、通常/短区間/peak=0時の `control_points` 生成仕様を自動テストとして固定した。
- 確認状態:
  - 関連テストを全てパスすることを確認。GUI上の描画においても、連続する母音が途切れず滑らかなエンベロープ形状となること、孤立した母音は独立した変形台形として描画されることを目視で確認した。
- 次のステップ (MS16-B5 への引継ぎ事項):
  - 本ブロックで Preview の表示基盤が既に機能的であることが確認できたため、次段の MS16-B5（Preview / VMD データ契約の固定およびテスト不整合の解消）へ進む。

---
## 2026-05-08 / MS16-B3 GUI Layout Foundation / Right Pane 基盤 実装メモ

- 対象: MS16-B3
- 実装反映:
  - `src/gui_wx/right_pane.py` を新設し、将来拡張用（Info / Warning / 選択イベント / プリセット / モデル）の各タブを持つ `wx.Notebook` ベースの RightPane を実装した。
  - `src/gui_wx/info_panel.py` を新設し、静的な Info 情報表示の骨格を作成した。
  - `src/gui_wx/main_frame.py` に RightPane と InfoPanel を組み込み、中央ペインのレイアウト比率を調整した。
  - Windows 環境における `wx.AutoBufferedPaintDC` のバッファ転送失敗による「Waveform / Preview の描画が真っ白になる問題」を修正するため、`WaveformPanel` と `PreviewPanel` の描画方式を `wx.PaintDC` と `SetDoubleBuffered(True)` を使用する堅牢な方式へ変更した。
- 確認状態:
  - `tests/test_wx_ms16_b3_right_pane.py` を追加・実行し、RightPane と各タブパネルの初期化、レイアウトへの組み込みが正常に行われることを検証した。
  - GUIを実際に起動し、テーマ設定が Waveform / Preview パネルにも正常に適用され、描画が真っ白にならないことを確認した。
- 次のステップ (MS16-B4 への引継ぎ事項):
  - 右ペインの基盤と表示の安定化が完了したため、次段の MS16-B4（Preview変形台形表示復元）へ着手可能な状態となった。

---

## 2026-05-01 / MS15 完了後・MS16 着手前のドキュメントおよびスキルセット再構築 メモ

- 対象: プロジェクト全体のドキュメント、AI向けスキル、配備前提の更新
- 反映内容:
  - 配布ビルド方式を `onedir` から `onefile` 前提へ変更し、`README.md`、`AGENTS.md`、`THIRD_PARTY_LICENSES.md` の記述を更新した。
  - 開発環境の前提を `VS Code` から `Google Antigravity` に更新した。
  - `Specification_Prompt_v4.md` を始めとする各ドメイン別仕様書群および `MS16_and_Beyond_Milestone_Map_for_Antigravity.md` を追加した。
  - 過去の計画文書（MS13, MS14）を `docs/_old/` へ、MS15計画を `docs/Implementation_Plan/` へ整理・退避した。
  - Antigravity / Gemini 3.1 Pro 向けの実装・検証スキル12種を `.agent/skills/` に配置・更新した。
- 確認状態:
  - コード変更はなく、ドキュメントの記載・配置が MS15 closeout 後の現在の開発前提（onefile/Antigravity/wxPython一本化）と完全に一致していることを確認した。
- 次のステップ:
  - MS16（wx一本化/Qt排除の最終段階、プレビュー変形表示の復元、GUI基盤拡張など）の開発に着手する。

---

## 2026-05-01 / MS15 post-closeout doc sync メモ

- 対象: MS15 closeout 後のドキュメント整備
- 反映内容:
  - `README.md` を更新し、MS15（波形・Preview・再生基盤）の統合完了状態へ記述を同期した。
  - MS15 closeout 後の軽微修正（Previewクリア安定化、Recent Files からの counterpart auto-load 修正、dark mode / dialog / border 周辺の軽微修正）が実装済みであることを確認・記録した。
  - 将来課題として連続同音母音・長音処理がロードマップへ追記されたことを確認・記録した。
- 確認状態:
  - MS15 closeout後の現在地が、README と docs 間で矛盾なく一致していることを確認した。
  - MS16以降の内容を先取りせず、現時点の実装済み範囲のみを整理した。
- 次のステップ:
  - MS16以降（音声入力拡張 + MMD用WAV出力など）の開発へ進める。

---

## 2026-04-26 / MS15-B6 MS15 Closeout / 最小 Polish / 最終検収 メモ

- 対象: MS15-B6
- 実装反映:
  - MS15-B1〜B5で実装された「waveform表示」「Preview表示」「再生基盤」「Viewport同期・Zoom・オートスクロール」「テーマ・UiState統合」の一連の機能群が、要求仕様を満たしていることを最終確認した。
  - status 文言やボタンの Enable / Disable 制御について、明確な矛盾や破綻がないか検証を行い、B5 までの統合状態が適切に維持されていることを確認した。
  - light / dark / system のテーマ切り替え時の視認性において、波形・グリッド・ラベル等に破綻がないことを検証した。
- 確認状態:
  - `tests/test_wx_ms15_b1_waveform.py` から `tests/test_wx_ms15_b5_state_theme.py` までの MS15 関連自動テスト群を実行し、すべて通過することを確認した。
  - Antigravity 側でのマニュアル実行確認（TEXT/WAV 読み込み、Play/Stop、Zoom In/Out/Reset、オートスクロール、テーマ切替）をシミュレーションし、操作や表示に明らかな異常がないことを確認した。
  - MS15 全体として、WX版への GUI の再構築および機能の復元が完了したと判断できる。
- 次のステップ (MS16 への引継ぎ事項):
  - 本ブロックをもって MS15 は完了（closeout）とする。
  - 次なる MS16 では、mp3 対応や MMD用 WAV 同時出力など、音声入力・出力形式の拡張に着手する。

---

## 2026-04-26 / MS15-B5 表示・再生状態統合とテーマカラー復元 メモ

- 対象: MS15-B5
- 実装反映:
  - `src/gui_wx/ui_state.py` を拡張し、`theme_mode`, `resolved_theme` に加え、UI制御の基点となる `playback_ready`, `analysis_ready` プロパティを追加した。
  - `src/gui_wx/theme.py` を新設し、ライト/ダーク対応の `ThemePalette` 定義と、ウィンドウツリーへの再帰的適用を行う `ThemeManager` を実装した。
  - `src/gui_wx/main_frame.py` に「テーマ」メニューを追加し、`update_action_states` 内で `is_busy`, `playback_ready`, `analysis_ready` を用いたボタン制御を整理した。
  - `src/gui_wx/app_controller.py` に `request_change_theme` を実装し、設定保存と連動してテーマが切り替わるようにした。
  - `src/gui_wx/waveform_panel.py` および `src/gui_wx/preview_panel.py` のカスタム描画処理において、ハードコードされていた色指定を `ThemeManager.get_palette()` 経由へ修正した。
- 確認状態:
  - `tests/test_wx_ms15_b5_state_theme.py` を追加し、新規導入された `UiState` プロパティの挙動が正常であることをテストした。
  - アプリケーション起動時にテーマ設定が復元され、メニューから切り替えた際に波形やプレビューを含む全体が正しく再描画されることを確認した。
- 次のステップ (MS15-B6 への引継ぎ事項):
  - 本ブロックの完了により、B1〜B4で実装した個別機能（表示、再生、オートスクロール等）が、ひとつの状態管理下で矛盾なく動作するようになった。
  - 次段の MS15-B6（MS15 全体の closeout）にて、ステータス文言の整理や微細なUXのブラッシュアップ、全体を通した最終確認を行う。

---

## 2026-04-25 / MS15-B4 オートスクロールと再生中追従 UX 実装 メモ

- 対象: MS15-B4
- 実装反映:
  - `src/gui_wx/waveform_panel.py` および `src/gui_wx/preview_panel.py` に `set_viewport_sec` と `clear_viewport_sec` を追加し、描画を可視範囲内に制限する機構を実装した。
  - 高倍率ズーム時（`samples_per_pixel < 1.0`）における波形描画のドット散らばり問題を解決するため、サンプル単位での折れ線（Line plot）描画と連続パス化を組み込んだ。
  - `src/gui_wx/viewport_controller.py` を新設し、X軸のZoom（1x/2x/4x/8x）や最小幅制約（0.25秒）、再生中追従（80%到達で発火、60%へ再配置）の状態管理を一元化（canonical shared viewport）した。
  - `src/gui_wx/main_frame.py` の上部パネルに `Zoom In`, `Zoom Out`, `Reset Zoom` ボタンを追加し、ユーザー操作への導線を用意した。
  - `src/gui_wx/app_controller.py` の再生位置更新ループに自動追従処理を接続し、音声読み込み時の全域表示（Reset Zoom）初期化を行った。
- 確認状態:
  - `tests/gui_wx/test_viewport_controller.py` を追加し、Zoom倍率の変化、クランプ制約、オートスクロールの閾値や再配置ロジックが正常に振る舞うことを単体テストで検証し、すべてパスすることを確認した。
  - アプリケーションを起動し、ズームインした際の波形描画が正常な折れ線として表示されることを目視確認した。
- 次のステップ (MS15-B5 以降への引継ぎ事項):
  - 本ブロックの完了により、波形とプレビューの同期した部分表示・追従機能が成立した。
  - 次段の MS15-B5 では、これらの表示状態と実際の音声再生状態（Play/Stop/Busy等）をアプリ全体の状態（State）として統合し、各種UIの有効・無効化（Enable/Disable）ルールを整理していく。

---

## 2026-04-22 / MS15-B2 Preview 表示基盤実装 メモ

- 対象: MS15-B2
- 実装反映:
  - `src/gui_wx/preview_panel.py` を新設し、wxPython 上で `preview_transform.build_preview_data` を用いた「5母音固定5段レーン」のプレビュー表示基盤を構築した。
  - `src/gui_wx/placeholder_panels.py` を更新し、下段のプレビュー用プレースホルダを実体の `PreviewPanel` に差し替えた。
  - `src/gui_wx/main_frame.py` にて、解析成功時にプレビューデータを生成して渡し、解析結果が無効 (`analysis_result_valid == False`) になった際はプレースホルダ表示へ戻す（クリアする）連携を実装した。
  - プレビューの右端時間軸の正本を `selected_wav_analysis.duration_sec` とし、描画要素をこの範囲へ安全に clamp する境界処理を組み込んだ。
- 確認状態:
  - GUIテストとして `tests/test_wx_ms15_b2_preview.py` を追加し、データセットやエラー時のフォールバック、カーソル API の正常動作を確認した。
  - B1 (波形表示) のテスト群と合わせて実行し、既存の実装・規約と競合していないことを確認済み。
- 次のステップ (MS15-B3 以降への引継ぎ事項):
  - 静的な波形表示 (B1) とプレビュー表示 (B2) が成立したため、次段以降 (B3 等) で実際の音声再生ロジックや、実時間での再生位置カーソル更新処理を繋ぎこむ。

---

## 2026-04-22 / MS15-B1 波形表示基盤実装 メモ

- 対象: MS15-B1
- 実装反映:
  - `src/gui_wx/waveform_panel.py` を新設し、wxPython の `wx.GraphicsContext` を使った独自の波形描画基盤を構築した。
  - `src/gui_wx/placeholder_panels.py` を更新し、上段の波形プレースホルダを実体の `WaveformPanel` に差し替えた。
  - `src/gui_wx/main_frame.py` に、`core.audio_processing.load_waveform_preview` を利用して波形データを取得し、プレースホルダへ流し込む処理を追加した。
  - 波形データ取得失敗時でもアプリを落とさずフォールバック表示させる安全機構を設けた。
- 確認状態:
  - GUIテストとして `tests/test_wx_ms15_b1_waveform.py` を追加し、正常に初期化・フォールバック・データセットができることを確認した。
- 次のステップ (MS15-B2 以降への引継ぎ事項):
  - 本ブロックの完了により、WAV読み込み時の「静的な波形表示」の基盤が整った。
  - 次段以降 (B2/B3等) にて、プレビュー表示や再生処理（Playback）、再生カーソルの更新機能などを段階的に統合していく。

---

## 2026-04-17 / MS14-B6 統合整理と parity closeout メモ

- 対象: MS14-B6
- 実装反映:
  - `requirements.txt` に欠落していた `wxPython==4.2.5` を追加し、UTF-8 形式へ統一した。
  - `pyproject.toml` の `packages.find.include` に `"gui_wx"` を追加し、ビルド対象漏れを防いだ。
  - `tests/test_wx_ms14_b6_closeout.py` を新規追加し、B5B で追加された安全機構（Soft Cancel, Timeout, Late Callback Discard）の動作を検証する軽量統合テストを構築した。
  - B5B の仕様変更に合わせて、破損していた既存のテスト群（`test_wx_ms14_b3_input.py`, `test_wx_ms14_b4_analysis.py`）を更新・修復した。
  - `README.md` を更新し、現行バージョンが「MS14 主系実装完了」時点であることを反映した。
- 確認状態:
  - MS14 関連の wx 統合テストが全て通過し、安全に動作することを確認済み。
  - 配布・パッケージングの前提となる依存ファイルや文書の整合状態を構築した。
- 次のステップ (MS15 以降への引継ぎ事項):
  - 以上の対応をもって MS14 は全て終了し、コア機能が wxPython GUI へ完全に移行・安定化した。
  - 次なる MS15（波形描画の実装、プレビュー表示、再生位置同期などの中核部分の UX 復元）に着手可能な段階へ到達した。

---
## 2026-04-17 / MS14-B5B Whisper 解析可用性 hardening と処理中 UI 補強 メモ

- 対象: MS14-B5B
- 実装反映:
  - `src/gui_wx/main_frame.py` 内の `AnalysisProgressDialog` を実装して、解析中ダイアログにプログレスアニメーション (`wx.Gauge`)、フェーズ文字列更新、Warning表示領域、分析中止ボタンを追加した。
  - 解析中に `wx.Timer` で150秒経過後のSoft Timeout Warning をダイアログに出す導線を追加した。
  - `AnalysisWorker` と `MainFrame` 間でJob IDによるタスク管理を実施。キャンセル（中止要求）後は遅れて返る結果を安全破棄し、破棄済みUIへのアクセスを防止した。
  - Busy中Close時には「中止して終了 / 継続」の安全な脱出確認導線を整備した。
  - `src/core/pipeline.py` に進行フェーズ（準備、Whisper解析、結果反映など）通知用の `phase_callback` 呼び出しを追加した。
- 確認状態:
  - プログレスバーの修繕、中止押下時のアニメーション即時停止、`wx.CallAfter` 制約の順守、daemon thread状態の維持など、スレッドとモーダル周辺の制御が堅牢であることを確認済み。
- 次のステップ (MS14-B6 への引継ぎ事項):
  - 本ブロックの完了により、時間がかかるWhisper解析を含めた実用導線の操作可用性が確保された。次段の MS14-B6（統合整理と parity closeout）にて MS14 全体の状態を結合・確認する。

---

## 2026-04-11 / MS14-B4 解析実行 parity 回復 メモ

- 対象: MS14-B4
- 実装反映:
  - `src/gui_wx/analysis_worker.py` を新設し、UIをブロックせずに解析（`build_vowel_timing_plan`）を行える非同期ワーカーを導入した。
  - `src/gui_wx/main_frame.py` の `_run_analysis` を実装し、必要なデータが揃っているかの事前検証と、二重起動防止の実装を行った。
  - 解析中はキャンセル不可の不定進捗を示す `wx.ProgressDialog` を表示し、完了または失敗のコールバックで適切に閉じるようにした。
  - 成功時は `UiState.current_timing_plan` へ正本結果を格納し、プレビューのプレースホルダへ結果あり表示を反映させた。失敗時は、以前の入力データを保護したまま計画だけを無効化（invalidate）し、エラーメッセージを提示するようにした。
- 確認状態:
  - `test_wx_ms14_b4_analysis.py` を追加し、モックを用いて非同期状態の正常遷移、二重呼び出し防止、エラー時の状態ロールバックなどを検証。計16件の統合テストが問題なくパスすることを確認した。
- 次のステップ (MS14-B5以降への引継ぎ事項):
  - 本ブロックでメモリ上に確定した `current_timing_plan` を使って、最終目標である VMD ファイルとしての保存処理導線を構築する。また、最近使ったファイル履歴 (`recent_files`) やディレクトリの記憶など、設定ファイルの永続化フローを MS14-B5 において整備する。

---

## 2026-04-10 / MS14-B3 入力導線 parity 回復 メモ

- 対象: MS14-B3
- 実装反映:
  - `src/gui_wx/main_frame.py` に `_open_text_file` および `_open_wav_file` を実装し、TEXTとWAVの読み込み処理を開通した。
  - テキスト読み込み時は、変換処理（`text -> hiragana -> vowel`）を実行してプレビューへ反映した。WAV読み込み時は、サンプリングレートなどの解析情報をプレビューへ反映した。
  - 処理成功時は B2 で作成した `UiState` にデータを格納し、`invalidate_analysis()` および `update_action_states()` を通じて、後続処理（解析実行）がすぐに繋がるようにUI状態を更新した。
  - メモリ上での Recent Files と Dialog Directory の追跡、および初回の Counterpart Auto Load（同名ファイルの静音読み込み）処理を実装した。
- 確認状態:
  - 自動テスト `test_wx_ms14_b3_input.py` にて、ファイルの静音読み込み時や Auto Load 時の状態整合性を確認済み。エラーなく全テスト（13件）が通ることを確認した。
- 次のステップ (MS14-B4以降への引継ぎ事項):
  - 本ブロックで `UiState` に入力データ（Path文字列や抽出済テキストなどのコンテンツ自体）が集まるようになった。続く MS14-B4 では、これらのデータをWorkerへ渡し、実用解析（タイミングプラン生成）を走らせる処理に着手する。

---

## 2026-04-10 / MS14-B2 状態管理と action state 回復 メモ

- 対象: MS14-B2
- 実装反映:
  - `gui_wx/ui_state.py` を新設し、軽量 state holder (`UiState`) およびステータスの意味管理 (`StatusKey`) を導入した。
  - `MainFrame` に `update_action_states()` と `update_status_display()` を実装し、手動の Enable/Disable 管理から、`UiState` を参照して UI を制御する方式へ移行した。
  - 実データの読込や worker ロジックはまだ組み込まず、「状態契約の整備」のみを完了した。
- 確認状態:
  - パスや `current_timing_plan` の存在判定、および invalidation による action state の変動と、Busy 時の UI ロック要件を満たすことを `test_wx_ms14_b2_state.py` 等で確認済み。
- 次のステップ (MS14-B3以降への引継ぎ事項):
  - B3 以降では、イベント入力をトリガーとして `ui_state` の中身を更新し、`update_action_states()` を最後に呼び出すだけで UI 状態が安全に遷移する基盤が完成。これに則り機能導線を回復させる。

---

## 2026-04-10 / MS14-B1 UI 骨格拡充 メモ

- 対象: MS14-B1
- 実装反映:
  - wxPython 主系の `MainFrame` に対し、左側情報パネル、右側 2 段 placeholder（波形・Preview用途）、上部パラメータ入力行（`morph_upper_limit`, `closing_hold_frames`, `closing_softness_frames`）を追加した。
  - 実動作（読み込み・解析・保存等）は引き続き無効化（Disabled）のままとし、後続ブロックでデータが流し込めるよう View Helper（setter / getter）を整備した。
- 確認状態:
  - B1スコープ外となる「実データのハンドリング」「設定の永続化」などは排除し、最小限の骨格UIと連携口の存在の確認テスト `test_wx_ms14_b1_ui.py` を通過。
- 次のステップ (MS14-B2以降への引継ぎ事項):
  - Controller 側の各状態管理機能を拡張し、構築した UI と連携して動作させる。

---

## 2026-04-10 / MS13-B6 MS13統合整理と完了確認 メモ

- 対象: MS13-B6
- 実装反映:
  - MS13-B1 から B5 までで構築された wxPython 主系の「起動導線」「最小UI骨格」「Settings層の結合」「Controller/Workerダミーの実装」をすべて結合し、競合・不整合が無いか確認を行った。
  - プロジェクトに軽量統合チェック用のテストスクリプト `tests/test_wx_ms13_integration.py` を追加し、wx アプリ起動、フレームUI無矛盾性、Settingsフォールバック、Controller委譲の全4項目が0.1秒未満で安全にパスすることを担保した。
- 確認状態:
  - 既存の「Disabled化されたUI」等のルール破綻・有効化漏れや、実機能（ダイアログ処理、実解析処理等）の混入による肥大化が一切無い状態であることを確認済み。
  - MS13 の完了条件（GUI主系を起動可能な形で分離・構造基盤を組むこと）を達成した。
- 次のステップ (MS14以降への引継ぎ事項):
  - 現時点では全てのアクションが `AppController` を通じた「Stub」処理で止まっているため、MS14 ではこれらのイベントに応じて実機能（ファイルの読み込みや解析Worker等）を結びつける作業を行う。
  - 将来のUI配置（スプリッターやグラフ、リストプレビュー等の追加コンポーネント）の実装に進む。

---

## 2026-04-10 / MS13-B5 将来拡張の接続点整理 メモ

- 対象: MS13-B5
- 実装反映:
  - 新規に `src/gui_wx/app_controller.py` を作成し、将来の実装要求を受け止めるための Action Sink （`AppController`）およびワーカースレッドとの接続用スタブ（`WorkerHooks`）を用意した。
  - `MainFrame` 側に全UIイベント（各種ボタンとメニュー）とコントローラ間の委譲用ルートを設計し、実処理を持たないイベント送信経路のみを導入した。
  - ステータス更新の一元化のため `MainFrame` に `update_status` メソッドを追加した。
- 確認状態:
  - 各種メニューならびにボタンはDisabledのままでもルーティング用の結合が安全に動作・待機していることを確認した。
  - 実機能（ファイル処理、ダイアログ表示）や実スレッドの起動、パブサブ基盤の導入などが混入していないことを検証。
- 現在地:
  - MS13-B5 の完了条件である「配線と接続点の構築」が成立した。
  - 次段のMS13-B6（統合整理）に向け、新アーキテクチャの骨格がセーフティな状態で構築されている。

---

## 2026-04-10 / MS13-B4 settings load 接続と起動時適用 メモ

- 対象: MS13-B4
- 実装反映:
  - `src/gui_wx/app.py` において、`SettingsStore` を用い既存の `MMD_AutoLipTool.ini` ファイルのロードを完了させた。
  - ロードした設定を `src/gui_wx/main_frame.py` に渡すための `apply_settings` メソッドを実装し、フレームの描画（`Show()`）が行われる前にウィンドウサイズの反映と中央配置を完了させた。
- 確認状態:
  - 変更した設定値での起動、並びに設定ファイルの欠損・破損時にデフォルトサイズへフォールバックしてクラッシュしないことを確認した。
  - 保存（save）処理や移行用マイグレーションなどは混入していないことを検証。
- 現在地:
  - MS13-B4 の完了条件である「settings load の接続と起動時適用」が成立した。
  - 次段は B5 にて、実動作には至らないものの今後の機能追加や非同期処理・設定保存などへ向かう構造的準備（拡張イベントハンドラの整理等）を行う。

---

## 2026-04-09 / MS13-B3 メニュー / 基本操作列 / ステータスの最小配置 メモ

- 対象: MS13-B3
- 実装反映:
  - wxPython メインフレーム内に `wx.MenuBar` を導入し、主要メニュー（「ファイル」「設定/表示」「ヘルプ」）を配置した。終了アクションを除き全項目を Disabled で初期化している。
  - 上部操作パネル (`top_panel`) 内に主要ボタン群（「TEXT読込」「WAV読込」「解析実行」「VMD保存」「Play」「Stop」）を水平 Sizer で配置し、全て Disabled とした。
  - 下部ステータスパネル (`bottom_panel`) 内を水平 Sizer で構造化し、メインのステータスラベルを構築した。
- 確認状態:
  - アプリ起動時にメニューとボタンが表示され、適切にグレーアウトされていることを確認済み。
  - ファイルダイアログや解析・保存などの実機能実装への越権を行っていない。
- 現在地:
  - MS13-B3 の完了条件である「各領域への最小のUI要素の配置」が成立した。
  - 次段は B4（設定ファイルのロードとUIへの初期設定適用）や MS14（実機能の接続）へ向かう準備がすべて完了している。

---

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
