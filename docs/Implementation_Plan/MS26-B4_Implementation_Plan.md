# MS26-B4 Implementation Plan

## 1. 文書情報

- 対象: MS26-B4 finding解消・再検証・文書同期・Closeout
- 作成日: 2026-09-11
- 計画作成基準: `feature/MS26-implementation` / `2d366fa3c1e3963fcc9e1923ec638002808e6bf4` (`Record MS26-B3 user GUI verification report`)
- 作成開始時のworking tree: clean
- 正本: [MS26 Block Breakdown](MS26_Block_Breakdown.md) §7 MS26-B4、§9.6、§11.6、§12、§16、および[Roadmap](../MS20_and_Beyond_Roadmap.md) §13〜§15
- 証拠台帳の正本: [MS26-B1計画](MS26-B1_Implementation_Plan.md) §16
- 状態: **MS26 CloseOut A（2026-09-12）。B1 / B2の自動gate、B3のユーザー報告によるGUI・実MMD受入、追加GUI / recovery / Whisper手動gate、B4 targeted revalidation、最終文書監査を確認済み。実MMD上の音声・モーフ同期良好はユーザー確認として受入記録に反映した。MS27はdeferred。**
- 計画作成時点の成果物は本ファイルの新規作成だけであり、以下のB4実行手順、既存文書の更新、コード・テストの限定補修は将来の実行範囲を定めるものであった。2026-09-12の部分実施記録は§15に追記する。
- 計画作成担当の成果をメインエージェントが現行リポジトリと照合し、必要な限定修正と最終検証を行う。最終的な採否・統合・検証責任はメインエージェントにある。

## 2. 背景

MS26はMS20〜MS25の機能基準を統合し、自動回帰、Windows 11上のGUI、実MMDでの受入を対応付けるマイルストーンである。B4はB1〜B3の証拠とfindingを最終到達状態へ結び直し、必要な補修と再検証を経てCloseoutを判定する。

### 2.1 計画作成時点の到達状態

| 対象 | 現行記録 | 根拠と証明範囲 |
| --- | --- | --- |
| B1 | baseline / contract gate Passed、実装後チェックPassed | B1計画§16.2。静的baseline・契約・ledger整備の通過であり、自動テストの代用ではない |
| B2 | automated cross-boundary regression Passed、duration finding resolved | [B2計画](MS26-B2_Implementation_Plan.md) §15.2〜§15.6。補修後unit 25 passed、実FFmpeg 24測定case、full 1067 passed / 4 skipped、各pytest終了コード0という既存実行記録 |
| B3 material / environment | AC03はユーザー報告で通過・問題なし | `MS26-B3-001`、[B3計画](MS26-B3_Implementation_Plan.md) §14.3〜§14.6。MMD Ver 9.32、model path、入力 / 出力音声path、実MMD上の音声・モーフ同期良好をユーザー報告で確認。PMX hashは本環境から独立取得できず、補助identityの未取得として記録 |
| B3 GUI | AC03および追加GUI gateはユーザー報告で通過・問題なし | `MS26-B3-002` / `MS26-B3-004`、[B3計画](MS26-B3_Implementation_Plan.md) §14.1、§14.3〜§14.6。CodexによるGUI操作は未実施。ユーザー報告により必要gateの結果を受入記録へ反映 |
| B3 actual MMD | AC04はユーザー報告で通過・問題なし。4主要ケースと音声・モーフ同期を確認済み | `MS26-B3-002` / `MS26-B3-003`、[B3計画](MS26-B3_Implementation_Plan.md) §14.3〜§14.6。Codexによる実MMD操作は未実施。ユーザー報告を実MMD受入証拠として採用し、artifact一組はread-only確認済み |
| B4 | 最終監査・CloseOut A完了 | `MS26-B4-003`、本計画§16。B4-AC01〜08を照合し、未解消のP1 / P2 / P3なし、B2-R05は非確定観測として分類 |
| MS27 | deferred | onefile、SmokeLaunch、配布物・ライセンス・release readinessは後続の責務 |

B2実装コミット`46a3f32`から計画基準HEADまでの`git diff --name-status`は文書4件のみで、production / testの変更はない。B2計画§15.6にあるduration関連3ファイルのSHA-256は、今回の読み取りで現行ファイルと一致した。これはコード・テストの連続性の根拠であり、現在の環境でpytestや実MMDを再実行した証拠ではない。

B2の4 skipはWindowsのsymlink生成権限不足`WinError 1314`の記録で、MS25 B6のWindows collision / fault gateと新規duration testにはskipがない。B2-R05には終了コード0と併せて`Exception in thread whisper-availability-1:`という見出しが記録されている。原因・影響・既存性は未確定であり、例外がなかったとは扱わない。

### 2.2 参照した根拠

- [MS20 Index](../MS20_and_Beyond_Index.md) §2: 現在地と日付付き履歴。過去の「未着手」記録を最新状態へ転用しない。
- B1計画§8、§10、§11、§15、§16: ledger、失効規則、B3開始条件、B1/B2/B3の証拠境界。
- B2計画§8〜§12、§15: test-only duration、必須回帰、補修前失敗・補修後結果、最終hash、未確定のdaemon観測。
- B3計画§6〜§12、§14.1: 承認済み素材・設定、4主要ケース、保護・復旧、実MMD担当、未検証時の扱い。
- [Pipeline仕様](../Pipeline_Data_Contract_Specification.md) §5.6〜§5.8、§6.1、[GUI State仕様](../GUI_State_Theme_Specification.md) §8.6、[Error Handling仕様](../Error_Handling_Specification.md) §15.6: 無効化、current state、同一snapshot、terminal、cleanup、既存出力保護。
- [VMD Output仕様](../VMD_Output_Specification.md) の30fps・morph名契約と§22.4、[MMD Audio WAV仕様](../MMD_Audio_WAV_Compatibility_Specification.md) §5〜§8、§10: 出力形式と時間軸。
- `README.md`、`readme_mmdautolip.txt`: 現行の個別保存、一括出力、Whisper、実MMD確認の利用者向け説明。
- §7の現行コード・テスト: 実在と関数・テストの責務を静的に照合した。網羅的なコードレビューやテスト実行の完了を意味しない。

## 3. 目的

1. B1〜B3の結果、未検証、findingを同じ最終到達状態に対応付ける。
2. 実証された契約違反について、原因、対象ファイル、最小補修、再検証範囲を固定する。
3. 自動テスト、ユーザーGUI報告、実MMD結果をそれぞれの証明範囲で扱う。
4. Closeout A / B / Cと、その判定に不足する証拠・判断を明確にする。
5. MS26の機能受入とMS27のbuild・配布検証の境界を維持する。

## 4. In Scope

将来のB4実行で扱う範囲は次のとおり。

- B1 ledger、B2コマンド結果、B3ケース結果の照合とfinding一覧の作成。
- B3から引き継いだ問題の再現確認、影響分類、既存契約へ戻すための限定補修。
- 証拠不足と製品不具合を分け、追加証拠または明示判断で処理すること。
- 変更によりstaleとなる証拠の特定、対象テスト・横断回帰・full gate、必要なGUI / 実MMD再確認の計画と結果照合。
- B1 ledgerのB4行、および必要な計画・状態・利用者向け文書の実到達状態同期。
- P1 / P2 / P3、未検証、対象外、MS27移管項目を含むCloseout判定。

B3の不足ケースはB3計画を使って補完する。担当・素材・操作の権限が未確定の項目は停止条件として扱い、B4への移行を理由に別素材や別の受入手順へ変更しない。

## 5. Out of Scope

- 新機能、広範なrefactor、UI再設計、任意morph mapping、モデル改変、セッション保存。
- duration差を保存時validator、production error code、DTO、個別保存・deliveryの拒否条件へ追加すること。B2のユーザー判断Aを維持する。
- WAVのcodec / sample rate / stereo固定、VMDの30fps・形式・文字encoding、既存fingerprint schemaの変更。
- `presets.json`、`profiles.json`、`MMD_AutoLipTool.ini`の直接編集・コピー・stage。ユーザー素材・既存成果物の編集、移動、削除。
- Whisper weights、MMD、モデル、音声のdownloadやリポジトリへの追加。新しい依存、network処理、cloud ASR。
- dependency / lock、設定の永続化契約、build設定、license / package artifactの変更。onefile、SmokeLaunch、ZIP生成、MS27の先行実施。将来の手動再検証で必要な既存GUIからの設定選択・適用・復帰は、B3計画の範囲に従う。
- stage、commit、branch変更、push、merge、tag、release、公開。commitを検証の前提にしない。

今回の計画作成では、上記に加えてコード・テスト・既存文書を一切変更しない。既存ledgerの更新もB4実行時の予定に留める。

## 6. 前提条件

### 6.1 着手条件を分ける

| 作業 | 必要条件 | 未充足時 |
| --- | --- | --- |
| 本計画作成・静的な準備 | 現行文書・コード・Gitを読み取れること | 不足を記録。B3未完でも計画は作成できる |
| B4 finding整理・補修 | B4実行依頼、再現情報または検証可能な既存契約違反、変更対象と受入条件 | finding候補または証拠不足として保留。原因を推測して編集しない |
| B3不足ケースの補完 | B3 material / environment gate、担当、承認済み素材・設定・出力先、該当操作の依頼 | 依存するGUI / 実MMD操作を止める。独立した証拠整理は進められる |
| MS26 Closeout A | §12の全条件、最終到達状態に有効な自動・GUI・実MMD証拠 | Aにしない。B/Cの判定または不足情報の報告へ進む |

B3の手動結果が失敗や部分確認であっても、引き継げるfindingと証拠があればB4で整理できる。B3の全面合格を補修開始の条件にはしない。一方、B3開始条件の不足を後付けの推測で解消したことにはしない。

### 6.2 現在残る未確定事項と停止条件

| 項目 | 既存記録 | B4への影響・停止条件 |
| --- | --- | --- |
| OS・MMD | B3記録にOS `25H2` / build `26200.9445`。製品名のresource取得値は空だが、ユーザーからMMD `Ver 9.32`と使用model pathの報告を受領 | MMD version / model pathはユーザー報告で補完済み。PMX hashは本環境から独立取得できず、補助identityの制限として記録 |
| 指定PMXのmorph名 | 日本語・英字双方があり、日本語・ラテンの実MMD確認は問題なしとのユーザー報告。Codexで実名一覧は未取得 | 英語表示名とVMDが参照する実名を区別し、実際の`あ / い / う / え / お`と`A / I / U / E / O`の対応を台帳へ補完する。不一致は別名へ自動置換しない |
| 素材・Whisper | B3計画§6に承認済みMMD / PMX / audio / TEXT / `small.pt`のpath・hash。入力音声pathと出力MMD用WAV pathはユーザーから提示済み | 入力 / 出力のroleは補完済み。4ケースごとのartifact対応と追加手動確認はユーザー報告で確認済み。個別操作ログ、PMX hash / morph一覧は未取得だが、機能受入を阻害するfindingとは分類しない |
| profile / preset | B3計画§8、B3-01に既存Latin profile、`PresetTest1`、built-in presetのIDと値 | 同名で代用せずIDと解決値を確認。日本語側はプロファイルなし、上限0.82。Latin側はprofile適用後の上限0.82と標準preset明示適用を確認する |
| GUIの個別証拠 | 2026-09-11の手動GUI通過、2026-09-12のAC03 / AC04、4主要ケースおよび追加GUI・復旧・状態確認のユーザー報告。入力 / 出力音声pathも提示済み | ユーザー報告を受入証拠として採用し、詳細操作ログ・画面記録が添付されていないことは明示した。GUI操作はCodex未実施 |
| 実MMD | AC04および`B3-T-JP` / `B3-T-LA` / `B3-V-JP` / `B3-V-LA`、追加の実MMD確認、音声・モーフ同期は、ユーザー報告で確認済み・問題なし | ユーザー実施結果として受入記録へ反映した。4ケースのartifact対応はユーザー確認として採用し、Codex確認済みartifact一組は静的read-only証拠として区別した |
| 観測しにくいケース | cancel / closeの競合、GUIで安全なfailure再現、通信観測、長音イベントの有無 | cancel / close / failure recoveryはユーザー報告で確認済み。通信観測と長音イベントの有無は個別測定を行っていないが、MS26必須受入の未解消findingとは分類しない。障害注入・権限変更・新規tool導入・音声書換えへ拡張しない |
| daemon例外 | B2-R05の見出しだけでは原因・影響を確定できない | B4 targeted revalidationとユーザーのWhisper手動gateでは再現・機能影響を確認しなかった。原因未確定・影響未観測の非確定観測として記録し、確定P1 / P2 / P3 findingには分類しない。未再現を無害性の証明とは扱わない |

ローカル`.venv`と既存FFmpeg/ffprobeを使う。B2のPython 3.14.3実績と`pyproject.toml`のPython >=3.11宣言を区別し、Python 3.11 / 3.12の実行互換性は未検証のまま残す。環境再構築は本計画の前提にしない。

## 7. 対象ファイル

### 7.1 今回の作成対象と将来の記録先

| 区分 | パス | 扱い |
| --- | --- | --- |
| 今回の新規作成 | `docs/Implementation_Plan/MS26-B4_Implementation_Plan.md` | 唯一の変更対象 |
| B4実行時の証拠正本 | `docs/Implementation_Plan/MS26-B1_Implementation_Plan.md` §16 | 既存13列を維持し、B4 finding・再検証・判定の行を追加する予定 |
| B4実行時の状態同期 | B2 / B3各計画、`docs/Implementation_Plan/MS26_Block_Breakdown.md`、`docs/MS20_and_Beyond_Index.md`、`docs/MS20_and_Beyond_Roadmap.md` | 過去記録を残し、最新状態と証拠参照を同期する予定 |
| 必要時の文書同期 | `README.md`、`readme_mmdautolip.txt`、§2.2の5仕様、`docs/repo_milestone.md`、`docs/Version_Control.md` | 実到達状態との不一致だけを補正。履歴2文書は該当箇所だけを検索・閲覧する |

### 7.2 現行コードの責務と限定補修候補

以下は実在する確認対象であり、一括変更リストではない。findingの原因に対応するファイルだけを補修対象として選ぶ。

| 境界 | 実在するパス | 既存責務・補修時に保持する点 |
| --- | --- | --- |
| 解析・出力意味 | `src/core/pipeline.py`、`src/core/output_diagnostics.py`、`src/gui_wx/output_diagnostics_adapter.py` | TEXT / voice_onlyからtiming plan、VMD入力、診断を形成。`analysis_pending_rebuild`と`ms21-effective-output-v1`の境界 |
| GUI snapshot | `src/gui_wx/main_frame.py`、`src/gui_wx/ui_state.py` | `capture_current_delivery_state`、`build_current_delivery_commit_snapshot`、保存可否。capture内で同じeffective plan・writer state・morph namesを使う |
| delivery transaction | `src/core/delivery_package.py` | start gate、source identity、commit fingerprint、owned staging、no-clobber確定、`DeliveryTerminalResult` |
| 成果物adapter | `src/core/delivery_artifacts.py`、`src/core/diagnostic_report.py` | VMD→MMD WAV→report。現在のeffective plan、元音声、同一snapshotを使い、sourceを変換前後に検査する |
| WAV | `src/core/audio_convert.py`、`src/core/mmd_wav_export.py`、`src/core/ffmpeg_runner.py` | 解析mono / MMD stereo、通常・cancellable runner、format validation、失敗保護。result durationは入力probe由来 |
| VMD | `src/vmd_writer/effective_shape_adapter.py`、`src/vmd_writer/writer.py`、`src/vmd_writer/validator.py` | 同じframe tupleの出力と`validate_morph_vmd_readback`。実MMDの見た目は証明しない |
| GUI worker・終了 | `src/gui_wx/app_controller.py`、`src/gui_wx/audio_worker.py`、`src/gui_wx/worker_state.py` | job / kind / projection binding、Busy、cancel、close、terminal一回受理、late結果破棄 |
| profile / Whisper関連確認 | `src/core/model_profile_state.py`、`src/core/morph_name_sets.py`、`src/core/whisper_model_runtime.py`、`src/gui_wx/analysis_worker.py` | profile解決、Japanese / Latin順序、selected / active / loaded / analysis identity |
| daemon観測の調査入口 | `src/gui_wx/whisper_availability_worker.py`、`src/gui_wx/app_controller.py` | `WhisperAvailabilityWorker`のlocal scanと結果通知、controllerのscan lifecycle。例外見出しの原因と断定しない |

### 7.3 テスト入口

- duration: `tests/ms26_wav_duration_helpers.py`、`tests/test_ms26_b2_wav_duration.py`、`tests/test_ms26_b2_wav_duration_integration.py`。
- snapshot / artifact: `tests/test_ms25_b1_current_state_gate.py`、`tests/test_ms25_b3_delivery_artifacts.py`、`tests/test_ms25_b3_vmd_readback_validation.py`、`tests/test_ms25_b4_delivery_report_identity.py`。
- transaction / GUI / fault: `tests/test_ms25_b2_delivery_orchestration.py`、`tests/test_ms25_b2_delivery_commit.py`、`tests/test_ms25_b2_windows_paths.py`、`tests/test_ms25_b5_delivery_worker.py`、`tests/test_ms25_b5_delivery_gui.py`、`tests/test_ms25_b6_delivery_failure_recovery.py`、`tests/test_ms25_b6_windows_collision_faults.py`、`tests/test_ms25_b6_delivery_gui_recovery.py`。
- Whisper観測: `tests/test_ms24_whisper_model_availability_worker.py`、`tests/test_ms24_whisper_model_runtime.py`、`tests/test_ms24_no_implicit_download.py`、`tests/test_whisper_model_store.py`。
- 共通回帰: §11のMS17-B7、MS19〜MS24、`tests/test_pipeline_and_vmd.py`、VMD writer群。
- 環境・import入口: `pyproject.toml`、`tests/conftest.py`、`.venv/Scripts/python.exe`。`tests/conftest.py`は`src`と`tests`をimport pathへ追加する。`pytest.ini`は現行rootに存在しないため実行前提にしない。

B4専用テストファイルの新設は現時点では確定しない。既存テストで表現できない再現が得られた場合だけ、対象契約・期待failure / success・ファイル名をB4 findingへ追記し、既存testの弱体化を避ける。

## 8. 実装方針

### 8.1 findingを分類してから補修する

| 分類 | 処理 |
| --- | --- |
| 既存契約違反が再現できる | 原因・最小変更・関連テスト・手動影響を固定し、許可されたB4実行範囲で補修する |
| 証拠・素材・環境が不足 | 未検証として不足内容と所有者を記録。コードを変更して不足を埋めない |
| 仕様の意味が一意でない | コード・仕様・既存判断を並べ、結果を変える選択だけをユーザーへ確認する |
| 表現・参照だけの不一致 | 意味を変えない文書補正。runtime証拠を失効させない根拠を記録する |
| MS27固有または対象外 | 所有先、影響、再開条件を明示。MS26必須の実MMD確認をMS27へ送らない |

優先度はP1＝直ちに扱う重大問題、P2＝次作業前に解消する問題、P3＝記録・表現上の軽微な問題とする。再現不能、原因未確定、素材不足を根拠なく製品不具合のP2等へ確定しない。データ破壊、不完全なfinal公開、誤ったsource / morph / snapshotの成功扱い等が確認された場合は、影響する操作の継続を止める。

findingには一意の`MS26-B4-F-*`、関連B1/B2/B3 evidence ID・ケースID、観測事実、期待契約、再現条件、優先度または未分類理由、原因の確度、影響、対象ファイル、解消方法、再検証、残課題を記録する。B2のRF-001〜006はresolvedの既存記録として照合し、再発の証拠なしにopenへ戻さない。

### 8.2 stale化と再利用

- 検証対象はHEADに未コミット差分と未追跡ファイルのpath / hashを加えたworking treeの内容で識別する。検証のためのcommitは不要。
- production / test / GUI / 対象契約の変更があれば、影響する旧行をstaleとして理由・変更後identity・再検証先IDを追記する。初回失敗や旧結果は消さない。
- 文書のみでも受入条件や対象素材の意味を変える変更なら関連証拠を再評価する。単なる誤字・参照・状態記録は非失効の根拠を残して再利用できる。
- runtimeが不変でもPython / 依存 / FFmpeg / OS / Whisper / PMX / profile / preset / audio / TEXTが変わった場合、影響する自動・手動証拠を再評価する。Git差分なしだけで外部環境まで同一としない。
- 旧B2結果は元のHEAD/tree・実行日を残し、最終到達状態への対応付けを新しいB4行へ記録する。「現在HEADで実行した」と書き換えない。
- 同じIDを別試行に再利用しない。既存`MS26-B4-001`は集約行として保持し、個別再検証には未使用IDを確認して`MS26-B4-002`以降を採番する。B3補完はB3の新規IDとして同じledgerへ記録し、B4が参照する。

### 8.3 限定補修と停止境界

限定補修は、確認済みのfindingを既存契約へ戻す最小変更とする。先に再現テストまたは再現手順を固定し、修正後に同じ期待条件で確認する。既存コードの名称や過去の計画だけを正解としない。

保存時duration拒否、新しい依存、音声 / VMD形式変更、MMDモデル改変、広範な設計変更が必要になる場合はB4の限定補修を越える。独立した証拠整理は続け、該当修正だけを止めて具体的な選択と影響を報告する。

## 9. 詳細ステップ

### B4-01: 最終照合のbaselineを固定

1. Index、Block Breakdown、本計画、B1 ledgerの最新行を読み、`git status`、`git branch`、`git log --oneline -n 10`、`git rev-parse HEAD`を一つずつ確認する。
2. 既存変更を保護し、B2実装コミット以降の差分とB2§15.6のtest hashを照合する。B4着手時に今回のplan基準と異なれば、新しいHEAD/treeを記録する。
3. 自動証拠に必要なPython / 依存 / FFmpeg identity、手動証拠の素材・設定identityを対応付ける。現在の環境で未確認の値をB2/B3の過去記録から補わない。
4. 証拠を有効・stale・未検証・deferredに分類する。この段階ではCloseoutを宣言しない。

### B4-02: B3結果と不足をケースへ対応付ける

主要4ケース`B3-T-JP`、`B3-T-LA`、`B3-V-JP`、`B3-V-LA`それぞれについて、入力mode、素材identity、profile / preset、生成設定、Whisper identity、同じ一括出力のVMD / WAV / report、実施者、日時、HEAD/treeを確認する。`B3-V-JP`は`B3-V-EDIT`の編集適用・再解析後の出力であることを確認する。

GUI報告には、`B3-G-PLAYBACK`、`B3-G-STATE`、`B3-V-EDIT`、`B3-S-DECAY`、`B3-S-PRESET1`、profileロック / 解除、`B3-D-COLLISION`、`B3-D-CANCEL`、`B3-D-FAIL`、`B3-D-CLOSE`、`B3-W-SELECT`、`B3-W-MISSING`と復帰を対応付ける。既存の「通過・問題なし」はそのまま残し、詳細不明の欄だけを不明とする。新たな再実施は不足またはstaleな範囲を対象にする。

各一括出力について、実際に観測できたprimary status、committed相当、finalの有無、cleanup警告、owned staging残留を照合する。内部DTO値が見えなければ`unobserved`とする。`partial_output_cleanup_failed`相当は、primaryがcancelやsuccessであってもcleanup合格にしない。処理が先に完了したcancel / closeは競合・観測不能として残す。

実MMDはB3-06に従いユーザーが確認する。各ケースの一括出力由来のVMDとWAVを同じ組として、新規状態・同じ開始フレームで読み込む。VMD読込、WAV読込、音声再生、実モーフの動作、発話の開始・中盤・終端の同期、閉口・開口・長音の見た目を別々に記録する。問題は時刻 / フレームと現象を残し、手動位置補正後の結果を未補正出力の合格へ転用しない。

### B4-03: findingを処理方針へ対応付ける

- B2 resolved finding、B3の実不具合、素材・証拠不足、daemon観測を区別して一覧にする。
- daemon見出しについては既存ログ、再現時期、scan / notification / shutdownとの対応、UIの失敗表示、プロセス終了コードを確認する。`WhisperAvailabilityWorker.run()`はlocal scan結果を通知する入口だが、見出しだけでは例外箇所を特定できない。現行のworker testは注入した同期callbackによる確認であり、実wx終了時の安全性全体の証明ではない。
- 追加再現が必要なら、当該testや既存GUI起動・終了の小さい確認を選び、フルテスト反復だけに頼らない。結果から原因・影響を限定できなければ未確定として残す。
- 各findingの解消方法、変更対象、最小回帰、B3再確認対象を記録してから補修へ進む。証拠不足だけならB4-04のコード変更を省略する。

### B4-04: 必要な限定補修と差分監査

確認済みfindingに限って補修し、最小テストを実行する。検証を広げる前に、差分がfindingの原因へ限定されていること、既存契約と失敗保護を維持していることを確認する。runtime data、設定、依存、build、ユーザー素材へ変更が及んだ場合は作業範囲を再点検する。

テストの弱体化、skip追加、閾値緩和、例外の握りつぶしで通過させない。既存の無関係な失敗は今回の補修へ混ぜず、関係・受入影響を報告する。

### B4-05: 変更後の再検証

§11に従い最小テスト→影響横断群→full pytest→compileall→diff checkの順で実施する。修正の追加があれば、その変更が失効させる証拠だけを起点に再評価し、必要なgateを変更後状態で揃える。

出力意味、morph名、WAV形式・時間軸、playback、delivery結果やGUI操作へ影響する修正は、B3の該当ケースを再実施する。新しく生成した成果物を新しいidentityで記録し、旧成果物・旧失敗を上書きしない。GUI表示だけの変更でもその操作の手動確認は必要だが、実MMDへ影響しない根拠を示せる場合は実MMD全件の再実施を機械的に要求しない。

### B4-06: 証拠・文書を同期

B1§16の13列（evidence ID、owner、requirement、source、HEAD、executor、environment / material identity、action、expected result、actual result / exit code、reproducibility、evidence location、limitation / status）を維持する。finding、再検証コマンド、ユーザー報告、Closeout判定の参照関係を同じledgerで追えるようにする。本計画に実施概要を追記する場合も別の証拠正本は作らない。

README、配布用readme、5仕様、Block Breakdown、Index、Roadmap、milestone / version-controlの関連箇所を照合する。正しく記載済みの文書は「確認・変更不要」と記録し、履歴を現在状態へ書き換えない。B4やMS26の完了状態は、次の判定結果とユーザーによるcloseout決定に合わせて同期する。

### B4-07: Closeout判定と引き継ぎ

§12のA/B/C条件と未処理項目を並べ、証拠付きの判定を報告する。A判定の条件充足とユーザーのcloseout決定を区別し、明示された決定・同期依頼があればその範囲の文書同期を完了する。同じ決定への許可を繰り返し求めない。

MS27へ渡すのは機能基準HEAD/tree、受入済み条件、既知の制限、Python未検証範囲、package / release側で必要な確認事項である。MS26の未解決必須条件をMS27へ移しただけでMS26を完了にしない。報告後、MS27やGit変更へ自動移行しない。

## 10. 状態遷移 / データ契約

### 10.1 B4と証拠の状態

```text
planned
  -> B4実行依頼 / baseline照合
  -> 証拠・finding整理
       -> 証拠不足: 該当gate保留 / B3補完
       -> 契約違反: 最小補修 / 影響証拠stale / 再検証
  -> 最終状態への対応付け / 文書照合
  -> A条件充足 / B条件付き継続 / C不合格
```

B/Cの報告を完了したことと、B4の全面受入・MS26 Closeoutを完了したことは別である。今回の状態は`partial execution`（AC03 / AC04はユーザー報告で通過、最終A/B/C未判定）であり、この遷移を実施済みとして記録しない。

### 10.2 維持するruntime契約

| 契約 | B4で維持・再検証する内容 |
| --- | --- |
| 入力と時間軸 | user input audio、internal analysis WAV、MMD-use WAVを分離。MMD用WAVは元音声から生成。無音trim・開始位置補正を追加しない |
| duration | `wave`の実frames / rate、`Fraction(1, 20)`以内をtest-onlyで確認。44100Hzで差2205 samplesはpass、2206はfailure。DTO同士のduration比較で代用しない |
| effective output | Preview / writer / diagnostics / report / deliveryは同じ有効な生成状態に対応。書き起こし編集後の再解析待ちをVMD / delivery成功へ流さない。診断reportの保存可否は別に判定 |
| morph / VMD | 30fps、morph-only、解決済みordered names、Japanese / Latin意味順を維持。MMD側の実在確認は別gate |
| Whisper | selected / active / loaded / analysis identityを分け、未ロードと異常を混同しない。暗黙download・外部送信なしの自動証拠と実機観測を分ける |
| delivery | 同一snapshotで3成果物を生成・検証後、source identity / fingerprint guardを通して確定。collisionでmerge / replace / delete / automatic renameしない |
| terminal / cleanup | commit前cancelはowned staging cleanup、commit後はfinalを削除しない。primary resultとcleanup statusを併記。Busy解除・close・late結果破棄は現行bindingとterminalを基準にする |

## 11. テスト方針

### 11.1 今回の計画検証とB4実行時の境界

今回行うのは本計画の再読、パス・関数・テスト入口と契約の静的照合、tracked / untrackedの差分確認だけである。pytest、compileall、GUI起動、実FFmpeg変換、実Whisper解析、実MMD操作は実施しない。

B4実行時も、変更・失敗・未解決の具体的リスクがなく、B2/B3証拠を最終状態へ対応付けられる場合は成功済み全件を反復しない。環境同一性や証拠の所在が確認できない場合は、その不足に対応するgateを選んで再取得する。

### 11.2 影響別の最小入口

| finding / 変更 | 先に確認するテスト | 次に必要となる範囲 |
| --- | --- | --- |
| PCM測定・変換 | B2 duration unit、実FFmpeg integration、MS17-B7 | audio_convert / runner回帰、MS25、pipeline/VMD。WAV形式・時間軸に影響すればB3出力・実MMD |
| snapshot・report・morph | MS25 B1 current state、B3 artifacts / VMD readback、B4 report identity | MS20〜MS24、pipeline/VMD、writer。出力意味が変われば対応するB3主要ケース |
| transaction / cancel / cleanup | MS25 B2、B5 worker / GUI、B6 3ファイル | MS25全群と関連worker。B3-D-COLLISION / CANCEL / FAIL / CLOSEおよび生成結果の該当確認 |
| Whisper scan / shutdown | MS24 availability worker、runtime、no implicit download | controller / lifecycle関連回帰を原因に応じて選択。B3起動・終了、W-SELECT / W-MISSINGと復帰 |
| 意味不変の文書補正のみ | 参照・状態・ledger列構造、diff check | runtime非失効の根拠を記録。自動・手動全件の再実行は不要 |

### 11.3 補修後の必須gate

production / test / GUIを補修した場合、Block Breakdown§11.6に従い、修正対象テスト、影響cross-boundary、full pytest、compileall、diff checkを通す。以下のB2責務別入口から影響する群を選び、選択理由・対象の和集合を記録する。影響を限定できない場合は列挙群をすべて含める。

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_ms17_b7_mmd_wav_export.py tests/test_ms17_b7_mmd_wav_failure_cleanup.py tests/test_ms17_b7_mmd_wav_save_dialog.py tests/test_ms17_b7_mmd_wav_overwrite_confirm.py tests/test_ms17_b7_mmd_wav_button_state.py
.\.venv\Scripts\python.exe -m pytest tests -k "ms25"
.\.venv\Scripts\python.exe -m pytest tests -k "ms19 or ms20 or ms21 or ms22 or ms23 or ms24"
.\.venv\Scripts\python.exe -m pytest tests/test_ms26_b2_wav_duration.py
.\.venv\Scripts\python.exe -m pytest -s tests/test_ms26_b2_wav_duration_integration.py
.\.venv\Scripts\python.exe -m pytest tests/test_pipeline_and_vmd.py
.\.venv\Scripts\python.exe -m pytest tests -k "vmd_writer"
```

production / test / GUI補修後の最終gate:

```powershell
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe -m compileall -q src tests
git diff --check
```

各行は別々の単独コマンドとして実行する。0件収集、必要群の欠落、pass表示・終了コード非0を通過にしない。実行日時、HEAD/tree、完全なcommand、実行者、pass / fail / error / skip、process exit code、証拠所在を残す。B2の既存件数を新しい検証の固定期待値にはしない。

duration再検証は通常runner 20条件＋cancellable runner 4条件の24測定case、source SHA-256、両出力のframes / rate / durationを記録する。必要tool / encoder不足、比較不能、超過をmock・skip・codec切替で回避しない。FFmpeg/ffprobeは既存locatorのrepo-local優先 / PATH fallbackで解決する。

skipは各testと理由・受入影響を確認する。B2の4 symlink権限skipは参照情報であり、今回も同じとして自動承認しない。MS25 B6のWindows junction / sharing violation等の必須fault gateやduration required caseの欠落は通過にしない。

未追跡の本計画はstageせずに次のコマンドで検査する。他に未追跡成果物がある将来の補修では、各実パスへ同様に一つずつ実行する。

```powershell
git -c core.autocrlf=false diff --no-index --check -- NUL docs/Implementation_Plan/MS26-B4_Implementation_Plan.md
```

no-indexの診断なし終了コード1は新規差分を表し、pytest非0と区別する。whitespace診断やその他のエラーがあれば通過にしない。

### 11.4 手動再検証と終了条件

B3ケースは実施者・環境・素材・設定・artifact identity・操作・期待結果・実結果・観測限界を記録する。GUIの通過から実MMD passを推定しない。実MMD4主要ケースはそれぞれ同じ一括出力のVMD / WAVを用いる。追加preset出力や個別保存を主要ケースへ混ぜない。

必要なgateが成功し、追加変更・失敗・未解決リスクがなければ判定へ進む。未検証が残る場合は際限なくテストを反復せず、§12の不足項目として報告する。

## 12. 受け入れ条件

### 12.1 この計画文書の受入

- B4の範囲、停止条件、補修条件、実在する責務・テスト入口が具体的である。
- B1/B2 Passed、B3 user-reported AC03 / AC04 pass、material / case-level evidenceの未提示、B4は計画作成時点の未実施と§15の部分実施、MS27 deferredを区別している。
- stale / 再利用 / 再実行条件、実MMD4ケース、A/B/C境界が追跡可能である。
- 計画作成時の変更は本ファイルだけで、既存文書・コード・テスト・runtime data・設定・依存・buildを変更していない。後日のB4部分実施で変更した文書は§15に明記する。
- 再読、パス照合、tracked / untracked差分検査を行い、未実行の検証を明記している。

### 12.2 B4全面受入・Closeout Aの条件

| ID | 条件 |
| --- | --- |
| B4-AC01 | B1/B2の必須証拠が最終HEAD/treeへ対応し、再利用根拠または必要な再検証結果を追える |
| B4-AC02 | 必須自動gateがpassかつprocess exit 0。skip理由・影響を記録し、required gateを欠いていない |
| B4-AC03 | B3 material / environment gateを通過し、GUI個別ケース・設定・出力・実施者が追跡できる。B3の必須GUI操作が期待結果を満たし、必須項目の未検証・観測不能・不合格を残していない |
| B4-AC04 | B3主要4ケースの実MMD読込・再生・morph・同期・見た目を個別判定し、必須の未検証・不合格がない |
| B4-AC05 | findingに原因の確度、処理、影響、再検証があり、P1 / P2 / P3の未解消がない。未分類の観測を隠していない |
| B4-AC06 | 変更後にstaleな証拠を最終passへ使っていない。手動影響のある補修後は該当GUI / 実MMDを再確認した |
| B4-AC07 | 文書とledgerが実際の到達状態に一致し、歴史的記録、ユーザー報告、未検証、対象外を保持している |
| B4-AC08 | MS27へ渡す機能基準と残る配布検証を明示し、MS26でbuild / release readiness完了を主張していない |

### 12.3 Closeout A / B / C

以下はBlock Breakdownの「A、条件付き継続、不合格」を本計画で具体化した判定規則である。

| 判定 | 境界 | 状態・次の扱い |
| --- | --- | --- |
| A: MS26機能受入条件充足 | B4-AC01〜08を満たし、必須未検証・未解消findingなし | MS26 closeout決定の根拠を提示できる。ユーザー決定に応じて同期し、MS27へ進める条件を記録する。MS27実行・公開の許可にはならない |
| B: 条件付き継続 / 受入保留 | 判明しているP1なし。未検証・観測不能・非致命的な残件について、影響・所有者・必要な証拠・再開条件を具体化できる | MS26の全面完了ではない。残件を許容・延期する場合はユーザー判断、理由、影響、期限または明確な再確認時点を記録する。MS27を既定で開始しない |
| C: 不合格 / 補修が必要 | P1、未処理のP2、必須自動gateの失敗、必須手動ケースでの契約違反、既存出力保護違反等が残る | 影響操作を止め、限定補修と再検証、または範囲を越える判断へ戻す。MS26完了・MS27着手可とはしない |

情報が足りずB/Cも確定できない場合は「判定保留」と不足証拠を報告する。単に「許容」と書いてfindingを消さない。ユーザー判断で延期した未解決事項は実測による解消とは区別し、未解消findingを残したままAへ格上げしない。

日本語専用profileの適用はB3で対象外とされた範囲であり、「プロファイルなし」の日本語出力と混同しない。B3のMP3/M4A実素材確認、Python 3.11/3.12、MS27のbuild・配布検証もそれぞれ未検証範囲を保持する。これら既定の対象外と、B3主要4ケース・必須操作の欠落を同じ扱いにしない。

**計画作成時点ではB3 material / environmentとactual MMDの証拠が不足しており、Aの条件は未充足である。B4の最終A/B/C判定自体は今回実施していない。**

## 13. リスクと対策

| リスク | 対策 |
| --- | --- |
| GUI通過報告を全ケース・実MMDpassへ展開する | 報告の確度を維持し、ケース / artifact対応と実MMD結果を個別に取得する |
| B3の不足をすべて「素材未提供」として扱う | 承認済みpath・hashと、未確認のversion / morph / 結果を分ける。既得情報を再要求しない |
| 同じHEADなら証拠が有効と誤認する | working tree、環境、外部素材・設定を併せて識別する |
| daemon見出しを既存不具合または無害と断定する | 原因未確定の観測を残し、再現条件・影響を限定してから処理する |
| duration自動testを保存時保護・リップ同期保証へ転用する | ユーザー判断Aを維持し、PCM時間差と実MMD観察を別gateにする |
| cleanup残留をcancel成功・close成功で隠す | primary / committed / cleanupを分け、残留や警告をfindingとして保持する |
| 回帰対象が足りない、または不要な全件反復になる | finding→責務→テスト→手動caseを対応付け、補修後の必須full gateを守る |
| Closeout文書が先に完了状態になる | 判定根拠とユーザーのcloseout決定へ同期する。B/C報告は全面完了にしない |

## 14. Codex 実装時の注意

- 本計画の保存で終了する今回の依頼と、将来のB4実行依頼を区別する。
- 通常の範囲内調査・最小補修・関連検証を別々の承認工程にしない。追加権限や結果を変える未解決の選択がある部分だけ停止する。
- コマンドは一つずつ実行し、結果と終了コードを確認する。サブエージェントが担当する場合もシェル実行を重ねず、独自に再委譲しない。
- 編集はfindingに限定し、既存変更を保護する。runtime JSON / INIへ直接触れず、テストは一時領域と既存のmanaged persistenceを使う。
- GUI再検証で設定を操作する場合はB3計画の既存GUI導線を使い、開始時設定への復帰と残った差を記録する。ユーザー素材や検証成果物を無断削除しない。
- 証拠にない因果・実施者・再現回数・環境値を補わない。観測結果、推論、未確認事項を分ける。
- 完了報告は、作成 / 変更ファイル、参照根拠、findingと処理、実施command / exit、未実施検証、A/B/Cまたは判定保留、残課題、変更していない範囲を示す。
- 計画担当の提出後、メインエージェントが内容と現行状態を照合し最終検証する。B4実施、MS26 closeout決定、MS27、Git変更へ自動的に進めない。

## 15. B4部分実施記録（2026-09-12）

- 実施主体: メインエージェント（Codex）。対象HEADは`fe4c95c`（`Document MS26-B4 implementation plan`）で、B2実装コミット`46a3f32`以降にproduction code / test codeの変更がないことを確認した。
- B3承認素材5件（MMD executable、PMX、audio、TEXT、repo-local `small.pt`）のSHA-256を再確認し、B3計画§6の記録と一致した。ユーザーからMMD Ver 9.32、使用model path、入力音声path、出力MMD用WAV path、日本語・ラテンおよび4主要ケース確認済みとの報告を受領した。MMD画面versionと4ケースの実MMD操作はメイン側では未実施で、PMX hash / morph一覧とケース別artifact対応は未提示である。
- ユーザーから「手動テスト通過。問題なし」との報告を受領した。ケース別の実施範囲、GUI / 実MMDの区別、操作ログ、スクリーンショット、出力artifactの所在は提示されていないため、ユーザー報告として記録し、B3の詳細証拠や実MMD個別判定へは推測で展開しない。
- ユーザーからAC03 / AC04をチェックし問題なしとの報告を受領した。AC03 / AC04はユーザー報告で通過扱いとする。`B3-T-JP`、`B3-T-LA`、`B3-V-JP`、`B3-V-LA`、日本語・ラテンの確認済み結果も提示されたが、PMX hash / morph一覧、4ケースごとの出力・操作ログ・artifact対応は未提示のため、ケース別追跡可能性は未完了として保持する。
- 外部生成物のread-only確認では、`D:\Visual Works\Kanna Work\Voice\MMD_AutoLipTool説明1B_MMD`にVMD、MMD用WAV、diagnostic reportの3ファイルを確認した。入力音声は`D:\Visual Works\Kanna Work\Voice\MMD_AutoLipTool説明1.wav`、出力MMD用WAVは`D:\Visual Works\Kanna Work\Voice\MMD_AutoLipTool説明1B_MMD\MMD_AutoLipTool説明1_mmd.wav`として記録する。reportは`text_audio` / `Custom` / `decay`であり、主要4ケースとの対応は未確定である。
- 次のtargeted pytestを3コマンドで単独実行した。
  - `.\\.venv\\Scripts\\python.exe -m pytest -rs tests/test_ms24_whisper_model_availability_worker.py tests/test_ms24_whisper_model_runtime.py tests/test_ms24_no_implicit_download.py tests/test_whisper_model_store.py`：25 passed、2 skipped、process exit code `0`。skipはsymlink作成権限不足（`WinError 1314`）。
  - `.\\.venv\\Scripts\\python.exe -m pytest -rs tests/test_ms24_b4_controller.py`：3 passed、process exit code `0`。
  - `.\\.venv\\Scripts\\python.exe -m pytest -rs tests/test_wx_ms24_whisper_model_ui.py`：4 passed、process exit code `0`。
- 上記範囲では新たな確定契約違反・P1 / P2 / P3を確認しなかった。B2-R05の`Exception in thread whisper-availability-1:`見出しはこのテストで再現せず、原因・影響は未確定のため、コード補修を行っていない。これはdaemon観測が無かったことや無害であることの証明ではない。
- 部分実施で変更したのは本計画、B1 evidence ledger、MS26 Block Breakdown、MS20 Indexの文書4件だけであり、production code、test code、runtime JSON / INI、依存、build、外部素材は変更していない。`MS26-B4-002`としてB1計画§16へ記録した。
- 部分実施時点では、詳細証拠の台帳転記、PMX morph / hashの個別記録、B4-AC01〜08の全面確認、確定findingの集約再検証が残っていた。その後の最終監査とユーザー追加確認は§16に記録し、現在の判定はMS26 CloseOut Aとする。MS27はdeferredのままとする。

## 16. 最終整理・MS26 CloseOut A（2026-09-12）

- 実施主体: メインエージェント（証拠・計画・文書の最終照合）、ユーザー（GUI・実MMDの手動確認）。CodexはGUI / 実MMDを操作していない。
- B1 / B2の自動gate、B4 targeted revalidation、B3のユーザー報告によるGUI・実MMD受入、追加GUI / recovery / Whisper gate、生成artifactのread-only確認を照合した。
- ユーザーは、MMD Ver 9.32、指定model、入力音声、出力MMD用WAVを用いて、日本語・ラテン、`B3-T-JP`、`B3-T-LA`、`B3-V-JP`、`B3-V-LA`を確認し、実MMD上の音声・モーフ同期も良好であると確認した。これはユーザー報告として受入証拠へ反映する。
- B4-AC01〜08は、既存の自動検証記録、ユーザー報告、生成artifactの静的確認、MS26のOut of Scope（MS27移管）を対応付け、すべて充足と判定した。AC03 / AC04はユーザー実施の受入結果であり、Codex実施結果とは区別する。
- B2-R05の`Exception in thread whisper-availability-1:`は、full pytest終了後の観測事実として保持する。B4 targeted revalidationでは再現せず、ユーザーのWhisper未配置・no-download・復旧確認でも機能影響は報告されなかった。原因は確定していないため、確定P1 / P2 / P3 findingではなく「非確定・影響未観測の観測」として処理し、コード補修は行わない。再現なしを無害性の証明とは扱わない。
- PMX hashは現在のCodex環境から提示pathを解決できず独立取得していない。model path、MMD version、ユーザーの実MMD上のmorph同期確認を機能受入の根拠とし、hash未取得は補助identityの制限として記録する。
- 判定: **MS26 CloseOut A**。MS26の機能統合・自動回帰・ユーザーGUI / 実MMD受入・文書同期を完了扱いとする。PyInstaller onefile、SmokeLaunch、配布物、license / package / release readinessはMS27へ移管し、MS26の完了範囲には含めない。
