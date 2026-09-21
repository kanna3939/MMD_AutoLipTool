# MS20 and Beyond Roadmap

## 1. 文書情報

- 文書名: MS20 and Beyond Roadmap
- 配置: `docs/MS20_and_Beyond_Roadmap.md`
- 対象リポジトリ: `MMD_AutoLipTool-dev`
- 作成日: 2026-07-13
- 基準ブランチ: `feature/MS20`
- 基準コミット: `edbcf2b Close out MS19`
- 基準状態:
  - MS16: wxPython 主系移行・GUI拡張基盤完了
  - MS17: 音声入力拡張・MMD用WAV出力完了
  - MS18: Release Readiness / Refactor / Security Hardening CloseOut済み
  - MS19: Voice-only Input / Workspace Reset / Closeout 完了（A）
- 文書ステータス: **Active Planning Baseline**
- 正本扱い:
  - 本書は、MS20以降の番号、機能採否、依存関係を定める計画正本である。
  - 各MSの実装は、別途Block BreakdownとImplementation Planを作成・承認してから開始する。
  - 本書に記載した機能は計画済みであり、実装済みまたは検証済みであることを意味しない。

## 2. 文書目的

MS16からMS19までに作成されたロードマップ、GUI将来構想、Block Breakdown、Implementation Planには、完了済み実装と未実装の将来候補が混在している。

また、従来のMS20は発音イベント単位編集だけを対象としていたが、MS19 closeout後の再監査により、以下の機能をVer.1.0候補へ向けた開発範囲で扱う方針が確定した。

- RightPane Info本実装
- Warning Panel本実装
- 出力診断レポート
- 発音イベント単位編集
- Undo / Redo・編集履歴
- 長音専用の口形維持 / 自然減衰
- 生成設定プリセット
- モデル別プロファイル
- Whisperモデルサイズ選択
- 組み込み英字5母音モーフセット
- MMD持ち込み用一括出力

本書では、これらを一つの巨大なMS20へ投入せず、責務と依存関係に従ってMS20以降へリナンバリングする。

## 3. 旧式ドキュメントの扱い

### 3.1 基本方針

MS16からMS19までのロードマップ系文書は、今後の実装順を決める正本ではなく、完了済みマイルストーンと過去の設計判断を確認するための履歴資料として扱う。

旧文書は削除しない。過去の実装根拠、受け入れ条件、テスト履歴、責務境界を追跡できるように保持する。

旧文書に書かれた将来MS番号を、そのまま現在の作業番号として使用してはならない。本書または本書承認後に作成する新Indexから、現在有効なMS番号を確認する。

### 3.2 旧式ロードマップ・索引

以下は、本書承認後に旧式ロードマップまたは移行前Indexとして扱う。

| 文書 | 新しい扱い | 注意 |
| :--- | :--- | :--- |
| `docs/Ver0_4_Expansion_Roadmap_for_Antigravity.md` | 旧構想資料 | 既に旧文書扱い。新規作業の正本にしない |
| `docs/MS16_and_Beyond_Milestone_Map_for_Antigravity.md` | MS16以降の旧マイルストーン構想 | 採用候補の由来確認に限って参照する |
| `docs/MS16_GUI_Layout_Spec_for_Antigravity.md` | MS16 GUI設計履歴 | 現存GUI基盤の意図は参照できるが、将来MS番号は無効 |
| `docs/MS18_and_Beyond_Roadmap.md` | MS18 / MS19実施履歴と旧MS20構想 | MS18 / MS19の完了記録は有効。MS20以降の番号は本書へ移行する |
| `docs/MS17_and_Beyond_Index.md` | MS17からMS19までの移行前Index | MS19完了状態の確認用。新規MSのrouting正本にはしない |

### 3.3 完了済みImplementation Plan

以下は旧式だから破棄するのではなく、完了済みマイルストーンの実施記録として保持する。

- `docs/Implementation_Plan/MS16-*.md`
- `docs/Implementation_Plan/MS16_Block_Breakdown.md`
- `docs/Implementation_Plan/MS17-*.md`
- `docs/Implementation_Plan/MS17_Block_Breakdown.md`
- `docs/Implementation_Plan/MS18-*.md`
- `docs/Implementation_Plan/MS18_Block_Breakdown.md`
- `docs/Implementation_Plan/MS19-*.md`
- `docs/Implementation_Plan/MS19_Block_Breakdown.md`

完了済みImplementation PlanのMS番号は変更しない。履歴のリナンバリングは、実施済みコミット、テスト記録、変更履歴との対応を壊すため行わない。

### 3.4 継続して有効な仕様書

次の仕様書は、旧MS番号への参照が含まれていても、実装契約のうち現行コードと一致する部分は引き続き有効である。

- `docs/Pipeline_Data_Contract_Specification.md`
- `docs/GUI_State_Theme_Specification.md`
- `docs/Error_Handling_Specification.md`
- `docs/VMD_Output_Specification.md`
- `docs/MMD_Audio_WAV_Compatibility_Specification.md`

ただし、新MSの実装前チェックでは、各記述を現行コードと再照合する。旧MS番号だけを根拠に機能の実装済み・未実装を断定しない。

## 4. 現在の製品基準線

MS20開始前の実装済み基準は次のとおりである。

- wxPython GUIが主系である。
- Qt / PySide6系は凍結されている。
- TEXTあり入力と音声のみ入力が成立している。
- wav / mp3 / m4a入力に対応している。
- 入力音声、解析用WAV、MMD用WAVは別のデータ役割として管理される。
- Preview、waveform、playback、viewportが存在する。
- VMD出力とMMD用WAV出力は個別の保存導線として成立している。
- `新規作業...` で現在の作業データを初期化できる。
- RightPaneには `Info / Warning / 選択イベント / プリセット / モデルプロファイル` のタブ基盤がある。
- RightPaneのInfo / Warning / プリセット / モデルプロファイルは本格実装されていない。
- 選択イベントは内部状態と読み取り専用summaryの下地だけがあり、ユーザー操作による選択・編集は成立していない。
- Whisperモデル名は内部引数を持つが、GUIでは実質的に`small`固定である。
- VMD出力モーフ名は `あ / い / う / え / お` 固定である。

## 5. 機能採否レジストリ

### 5.1 Ver.1.0候補ロードマップへ採用する機能

| 機能 | 状態 | 確定配置 |
| :--- | :--- | :--- |
| RightPane Info本実装 | 採用 | MS20 |
| Warning Panel本実装 | 採用 | MS20 |
| 出力診断レポート | 採用 | MS20 |
| 発音イベント単位編集 | 採用 | MS21 |
| Undo / Redo・編集履歴 | 採用 | MS21 |
| 長音専用の口形維持 / 自然減衰 | 採用 | MS22 |
| 既存の同音母音処理の監査と残存問題の限定改善 | 採用 | MS22 |
| 生成設定プリセット | 採用 | MS22 |
| モデル別プロファイル | 採用 | MS23 |
| 組み込み英字モーフセット `A / I / U / E / O` | 採用 | MS23 |
| Whisperモデルサイズ選択 | 採用 | MS24 |
| MMD持ち込み用一括出力 | 採用 | MS25 |
| 機能統合・全体回帰・実MMD closeout | 採用 | MS26 |
| Ver.1.0実装到達・公開境界の整理 | 採用 | MS27 |

### 5.2 実装しない機能

以下はVer.1.0候補の対象外という意味ではなく、現時点の製品方針として実装しない。

- ひらがな修正UI
  - 日本語本文または音声のみ入力の書き起こし本文を修正し、ひらがな・母音列を再生成する。
  - ひらがな欄そのものを編集可能にはしない。
- 他ASR backend設計・選択
- セッション保存・再読込
- VMD読み戻し編集
- 任意キーフレーム編集
- 歌唱専用最適化
- 外部クラウドASR

### 5.3 Ver.1以降まで保留する機能

以下は不採用ではない。ただし、MS20からMS27までの完了条件には含めない。

- 歌唱・楽曲利用時の完全なUX整理
- 調整レイヤーのセッション外永続化
- モデル別モーフ名マッピング
- ユーザー定義モーフセット
- 口角、笑い、まばたき、困り顔等の追加表情
- 英語音声・英語テキストからの本格的な多言語リップ生成

### 5.4 既存候補として再評価する項目

以下は従来ロードマップに候補があるが、本書作成時点では採用を確定しない。

- cache / temp管理改善
  - MS27完了後の独立修正・運用検討として、必要最小限の改善要否を再評価する。
- installer等の配布方式追加
  - MS27完了後の別工程として必要性を判断する。

## 6. 確定マイルストーン一覧

| MS | 名称 | 主目的 | 主な依存 |
| :--- | :--- | :--- | :--- |
| MS20 | RightPane Information / Warning / Output Diagnostics | 情報・警告・診断の共通基盤を完成させる | MS19 closeout |
| MS21 | Per-Event Lip Adjustment / In-Memory Edit History | 発音イベント選択・補正・Undo / Redoを成立させる | MS20 |
| MS22 | Long-Vowel Expression / Generation Presets | 長音表現と再利用可能な生成設定を導入する | MS21 |
| MS23 | Model Profiles / Built-in Morph Name Sets | モデル別数値設定と組み込みモーフ名セットを導入する | MS22 |
| MS24 | Whisper Model Selection | ローカルWhisperモデルサイズ選択を安全に導入する | MS20、MS23設定基盤 |
| MS25 | MMD Delivery Package Export | VMD・MMD用WAV・診断レポートを一括出力する | MS20、MS21、MS23、MS24 |
| MS26 | Final Feature Integration / Actual MMD Closeout | 全機能統合、全体回帰、実MMD受け入れを確定する | MS20からMS25 |
| MS27 | Ver.1.0 Closeout / Release Boundary | Ver.1.0の実装到達状態を確定し、公開・追加のリリースパッケージ整備を別工程へ分離する | MS26 |

MS20からMS27までの番号と依存順は確定し、MS27は完了済みとする。各MS内のBlock数は、Implementation Plan作成前に作業量とリスクを再評価して決定する。
MS28はこの全体系列に追加せず、MS27完了後の独立した修正実装トラックとして扱う。

## 7. MS20: RightPane Information / Warning / Output Diagnostics

### 7.1 目的

後続機能が共通利用できる情報表示・警告・診断データ契約を先に完成させる。

### 7.2 In Scope

- RightPane Infoタブに解析概要、再生位置、現在frame、現在母音を表示
- Warningタブに `INFO / WARNING / ERROR` のseverityを持つ構造化診断を表示
- 入力情報、解析情報、生成情報、保存可否の表示契約
- `timing source`、anchor数、fallback、warning、イベント数、最大フレーム等の診断項目整理
- VMD保存前診断
- 診断レポートのcoreデータ契約
- `ERROR` がある状態では保存不可
- `WARNING` がある状態では、同一状態につき一度だけ保存確認
- 専用保存操作によるUTF-8の `<base>_report.txt` 出力
- 新規作業、入力変更、再解析、失敗、late result破棄時の表示更新・クリア規則
- 長い情報・警告を扱えるスクロール可能UI
- 対象テストとdocs同期

### 7.3 Out of Scope

- 発音イベント編集
- プリセット・モデルプロファイル編集
- セッション保存
- 歌唱音声の自動判定
- VMD / MMD用WAVの一括出力

### 7.4 完了条件

- Info / Warningがプレースホルダーではなく、現行状態から生成された情報を表示する。
- Infoは解析概要と再生中の位置・frame・母音を同じ状態から表示する。
- Warningは `INFO / WARNING / ERROR` を区別し、保存可否と確認ルールがseverityと一致する。
- 診断表示とレポートが同じデータ契約を参照する。
- 専用保存操作から `<base>_report.txt` をUTF-8で出力できる。
- 古い入力・解析結果・警告を次の作業へ残さない。

## 8. MS21: Per-Event Lip Adjustment / In-Memory Edit History

### 8.1 目的

自動解析結果を破壊せず、発音イベント単位の補正をPreviewとVMDへ反映する。

### 8.2 In Scope

- Preview上のイベントhit-testと選択
- 選択とパン操作の競合回避
- RightPane選択イベントタブの本実装
- 開口量、開始 / 終了、hold、softness、slopeの補正契約
- base timing planとuser adjustment layerの分離
- Previewとwriterが共通の補正resolverを参照する構造
- 選択イベントreset、全編集reset
- セッション内Undo / Redoと最小編集履歴
- adjustment layerのsnapshot履歴方式
- 履歴上限50操作、連続する数値変更の1操作への集約
- 操作中のPreviewへの即時反映
- Busy、再解析、入力変更、新規作業時の状態遷移
- TEXTあり / voice_only双方の回帰確認

### 8.3 Out of Scope

- adjustment layerのセッション外永続化
- VMD読み戻し
- 任意キーフレーム編集
- 汎用タイムライン編集
- 複数イベント一括編集
- 母音種別の変更

### 8.4 完了条件

- ユーザー操作でイベントを選択・補正できる。
- 補正結果がPreviewとVMDへ同じ意味で反映される。
- 元解析結果と補正差分が分離される。
- Undo / Redo履歴はアプリ終了時に破棄される。
- adjustment layerと履歴はセッション外へ保存されない。

## 9. MS22: Long-Vowel Expression / Generation Presets

### 9.1 目的

長音を通常の母音複製だけで扱わず、維持または自然減衰として表現できるようにし、生成傾向をプリセットとして再利用可能にする。

### 9.2 In Scope

- 長音区間のデータ契約
- presetから選択する長音の `hold / decay` モード（既定は `hold`）
- Preview / writer整合
- 長音設定とイベント補正の優先順位
- 組み込み生成プリセットとユーザープリセット
- ユーザープリセット用の単一versioned `presets.json`
- ユーザープリセットは初期上限100件とし、将来の上限拡張を可能にする
- プリセットの選択・適用・復元
- プリセット適用のUndo / Redo連携
- 右ペインまたは上部UIへのプリセット導線
- 既存の同音母音処理を監査し、残存する問題だけを限定改善

### 9.3 Out of Scope

- 歌唱専用アルゴリズム
- ユーザー定義モーフセット
- セッション保存
- モデル別プロファイル本体

### 9.4 完了条件

- 長音表現の維持 / 減衰方針がPreviewとVMDで一致する。
- 組み込みプリセットと上限内のユーザープリセットを選択・適用できる。
- プリセットと個別イベント補正の優先順位が説明されている。

## 10. MS23: Model Profiles / Built-in Morph Name Sets

### 10.1 目的

MMDモデルや用途ごとに数値設定を再利用し、固定された組み込みモーフ名セットを安全に切り替えられるようにする。

### 10.2 In Scope

- モデル別プロファイルの保存・選択・更新・削除方針
- 単一versioned `profiles.json`、初期上限100件、将来拡張可能な上限契約
- `profiles.json` を既存INIと同じ保存場所に配置
- `morph_upper_limit`、hold、softness、標準プリセット等の再利用
- プリセットとモデルプロファイルの責務分離
- 組み込みモーフ名セット:
  - 日本語: `あ / い / う / え / お`
  - 英字: `A / I / U / E / O`
- writer、Preview、診断、一括出力で使用するモーフ名契約
- 既存日本語モーフ出力との後方互換性
- 適用優先順位: `イベント補正 > model profile > preset > application default`
- profileが日本語／英字モーフセットを保持し、profile未選択時はglobal既定の日本語セットを使用

### 10.3 Out of Scope

- PMX / PMD読込
- モデルファイル解析
- 任意モーフ名マッピング
- ユーザー定義モーフセット
- 追加表情モーフ
- 英語音声認識・英語音素処理

### 10.4 重要契約

英字モーフセットは、英語音声対応ではない。既存の日本語5母音イベントを、MMDモデル側の英字モーフ名へ出力する組み込み命名プロファイルである。

### 10.5 完了条件

- モデル別数値設定を保存・再利用できる。
- 日本語モーフ名と英字モーフ名を明示的に切り替えられる。
- デフォルトは既存の日本語モーフ名を維持する。

## 11. MS24: Whisper Model Selection

### 11.1 目的

TEXT + 音声およびvoice-onlyの全Whisper timing経路で使用するローカルWhisperモデルを、ユーザーが処理負荷と概算必要容量を理解したうえで選択できるようにする。

### 11.2 In Scope

- 選択可能モデル `small / medium / turbo`
- モデル名、必要容量、処理負荷、推奨用途の説明
- GUI選択と設定保存
- AnalysisWorker / pipelineへの明示的なmodel引渡し
- 選択モデル名のInfo / 診断レポート反映
- モデル未配置、load失敗、メモリ不足等の状態復帰
- PyInstaller / 配布サイズへの影響確認
- ユーザー確認後に限定した前景download操作
- 専用workerによる進捗、キャンセル、空き容量、一時ファイル、SHA256検証の管理
- 公式URL、SHA256、容量をrepo内versioned manifestで固定
- source / frozenの`src.core` manifest resource runtime解決と、installed packageの`core/whisper_models.json` package-data配置マッピング
- 既定保存先をexe隣接 `models` とし、書込不可時は書込可能な保存先選択を促して設定に保存
- download済みモデルの削除

### 11.3 Out of Scope

- 他ASR backend
- 外部クラウドASR
- 音声データの外部送信
- 無通知のバックグラウンドダウンロード
- ユーザー操作によらない通信
- 英語・多言語リップ生成の本格対応
- 既存アプリ全体の`src.core` / `core` installed namespace統一、およびinstalled `core.whisper_models` runtime importの補修（package工程）

### 11.4 ネットワーク例外契約

ユーザーがモデル取得を明示操作し、確認した後の前景downloadだけをネットワーク例外とする。cloud ASR、他ASR backend、音声送信、background通信は禁止する。

### 11.5 完了条件

- 選択したモデルが解析処理と診断表示へ一貫して渡る。
- 未配置・読込失敗時に古い解析結果を保存可能状態として残さない。
- ネットワーク依存や配布影響が明文化されている。
- manifestとSHA256により取得物を検証でき、削除も明示操作で完了できる。

## 12. MS25: MMD Delivery Package Export

### 12.1 目的

現在の作業で生成したMMD持ち込み用成果物を、分かりやすい一つの出力単位として保存する。

### 12.2 In Scope

- 一括出力対象:
  - 編集反映済みVMD
  - MMD用WAV
  - 出力診断レポート
- 親directoryと編集可能なfolder名を指定し、既定名は `<audio_stem>_MMD`
- 現在状態から全成果物を再生成
- 一時directoryで全体を生成・検証し、全成功時だけ確定
- 同名の既存filesystem entry（空・空でないdirectory、file、symlink、reparse pointを含む）がある場合は別名指定を要求し、merge・置換を行わない
- Windowsの通常filesystem API互換性を優先し、各path componentをUTF-16 code unit 255以下、絶対staging / final / 成果物pathをNUL終端を含めずUTF-16 code unit 240以下とする。超過時は暗黙renameせず拒否する
- 部分失敗時のcleanupと既存出力保護
- 個別VMD保存・個別MMD用WAV出力との共存
- 使用プリセット、モデルプロファイル、モーフ名セット、Whisperモデル名のレポート記録
- MMDユーザー向けREADME / 配布説明同期

### 12.3 Out of Scope

- `.autolip`等のセッションファイル
- MMDプロジェクトファイル管理
- MMD本体のディレクトリ構成管理
- 自動ZIP化の必須化
- ZIP出力
- 保存後のMMD自動起動

### 12.4 出力契約

一括出力は専用directory作成とし、既存の個別保存済みファイルを再利用しない。ZIP、session file、MMD自動起動は対象外とする。

### 12.5 完了条件

- VMD、MMD用WAV、診断レポートを一貫した名前で出力できる。
- 失敗時に既存成果物を壊さない。
- 個別保存導線を維持する。
- 出力先衝突時に既存directoryを変更しない。

### 12.6 現在状態（2026-09-04）

- MS25-B1〜B6は実装済みである。B6専用testは`26 passed`、B6直接回帰は`134 passed, 2 skipped`、指定cross-boundary回帰は`94 passed`、全pytestは`1041 passed, 4 skipped`で、いずれもprocess exit code `0`。Windows実filesystemのjunction collisionとsharing violationもskipなしで確認し、`compileall -q src tests`と`git diff --check`もexit code `0`である。
- B5の手動GUIテストはユーザー報告で通過した。これはユーザー確認の範囲に限定した記録であり、Codex自身のGUI実行結果ではない。
- B6の手動GUIテストはユーザー報告で通過した。これはユーザー確認の範囲に限定した記録であり、Codex自身のGUI実行結果ではない。
- MS25-B6 Implementation Planは`9841de4 Document MS25-B6 implementation plan`として作成され、その後のB6実装・文書同期は`5300905 Implement MS25-B6 delivery recovery hardening`としてcommit済みである。B6専用testの責務・ファイル名、MS25 routing、`output_path_inspection_failed`のError code一覧を文書上補正し、B6の自動検証・Windows fault gate・ユーザー報告の手動GUI確認まで反映済みである。
- 2026-09-04にMS25-B7を検証HEAD `0b25c5c Document MS25-B7 implementation plan`で実施した。B6 required gateは`26 passed`、MS25-B1〜B6 aggregateは`160 passed, 2 skipped`、cross-boundary 4群は合計`322 passed`、全pytestは`1041 passed, 4 skipped`で、各process exit codeは`0`だった。4 skipはWindows symlink作成権限不足（WinError 1314）に限定され、B6 required Windows fault gateにはない。`compileall -q src tests`と`git diff --check`もexit code `0`である。
- README、`readme_mmdautolip.txt`、Pipeline / GUI State / Error Handling / VMD Output正文仕様を現行挙動と照合し、必要事項が反映済みのため追加変更不要と判定した。Index、Block Breakdown、B6 plan、B7 plan、milestone、Version ControlをB7実績へ同期した。B7実施中のproduction code、test code、GUI、dependency、build設定、license、runtime user dataの変更はない。
- MS25-B7のfull cross-boundary regression、全pytest、static gate、文書同期、P1 / P2 / P3 finding再確認を完了し、MS25 Closeout Aと判定した。B5 / B6の手動GUI確認はユーザー報告として範囲限定で再利用し、B7でfresh GUIは行っていない。実MMDでのVMD / WAV読込・再生・リップ同期はMS26、Python 3.11 / 3.12の互換性確認は未検証、PyInstaller onefileとpackage / release readinessはMS27へ引き継ぐ。

## 13. MS26: Final Feature Integration / Actual MMD Closeout

### 13.1 目的

MS20からMS25までの成果を統合し、機能間の整合、全体回帰、実MMD受け入れを完了する。

### 13.2 In Scope

- MS20からMS25までの成果監査
- TEXTあり / voice_only回帰
- Preview / writer / RightPane / Warning / report整合
- プリセット、モデルプロファイル、モーフ名セットの互換性確認
- Whisperモデル選択の機能統合確認
- MMD持ち込み用一括出力確認
- 全体テスト
- Windows 11実機確認
- 実MMDでのVMD / WAV読込・再生・リップ同期確認
- READMEと機能仕様の到達状態同期
- Ver.1以降保留事項の明示

### 13.3 Out of Scope

- GitHub Release公開
- tag作成
- remote push
- PyInstaller onefile buildとSmokeLaunch
- 配布物・ライセンス・package manifestのrelease readiness監査
- installer新規導入
- Ver.1以降保留機能の先行実装

### 13.4 完了条件

- P1 / P2が解消またはユーザー判断で明示的に処理されている。
- 自動テスト、Windows 11実機、実MMD確認の結果が記録されている。
- 実装済み、未実装、保留、非採用が文書上で一致している。
- MS27のrelease readiness確認へ進めるか判定できる。

### 13.5 現在状態（2026-09-12）

- B1 baseline / contract gateとB2 automated cross-boundary regressionはPassed。B4のWhisper周辺targeted revalidationも、25 passed・2 skipped、controller 3 passed、Whisper UI 4 passed、各process exit code `0`として記録済みである。
- ユーザー報告として、MMD `Ver 9.32`、指定model、入力音声、出力MMD用WAVを使用し、日本語・ラテンおよび`B3-T-JP`、`B3-T-LA`、`B3-V-JP`、`B3-V-LA`を確認し問題なし。生成物一組はread-only内容確認済みである。
- 追加のGUI再生、voice-only編集・再解析、状態・保存可否、delivery保護・復旧、Whisper未配置・no-download、profile / preset適用と復帰も、ユーザー確認で問題なしとして`MS26-B3-004`へ記録する。
- 4ケースごとのartifact対応および実MMD上の音声・モーフ同期は、ユーザー報告で確認済みとして受入記録へ反映した。B4最終監査でB4-AC01〜08を充足と判定し、B2-R05 daemon候補は再現なし・機能影響未観測の非確定観測として分類した。PMX hashは本環境から独立取得できず、補助identityの制限として記録する。MS26 CloseOut Aを確定し、MS27のpackage / release readinessはdeferredとする。

## 14. MS27: Ver.1.0 Closeout / Release Boundary

### 14.1 目的

MS26で受け入れた機能基準とVer.1.0の実装到達状態を整理し、公開操作と追加のリリースパッケージ整備を別工程へ分離する。追加のpackage作成・再buildはMS27の完了条件に含めない。

### 14.2 In Scope

- 既存のPyInstaller onefile build・SmokeLaunch証跡の状態確認
- 既存の配布成果物・依存関係・license証跡のread-only確認
- `LICENSE`、`NOTICE`、`THIRD_PARTY_LICENSES.md`、package manifestの整合確認
- README、配布用readme、変更履歴の同期
- 既存のVer.1.0 release readiness記録の位置づけ確認
- 既存のbuild・配布・license証跡がある場合の状態確認

### 14.3 Out of Scope

- GitHub Release公開
- tag作成
- remote push
- installer新規導入
- Ver.1以降保留機能の先行実装
- 新規リリースパッケージ作成、ZIP再生成、追加build

公開、tag作成、pushは、MS27の判定とは別にユーザーの明示承認を必要とする。

### 14.4 完了条件

- Ver.1.0の実装到達状態と残る未検証事項が記録されている。
- 公開、tag、push、merge、公開用source archive生成がMS27の完了条件から分離されている。
- 新規リリースパッケージの作成・再buildを行わずにMS27を完了判定できる。

### 14.5 現在状態（2026-09-19）

- MS27-B1〜B5は実施済み。B3のG-LICENSE、B4のG-ARTIFACT、B5のG-PACKAGEはいずれもPassである。
- B5では候補#07で確認した過剰なmodule除外を限定補修し、候補#08を再build・SmokeLaunch・内部監査・ZIP組立・展開・配布実行まで再検証した。候補#08 EXEは425824202 bytes、SHA-256 `AF3B8FD65E3A518F5960EB4D697BE81AA773A1DAE312703552902D97D4CE4223`、FileVersion / ProductVersionは`1.0.0`。ZIPは423274681 bytes、SHA-256 `D963D5F619D48C59B2287992BF6AB350B23AA8DE240686477EA59093F9DB9086`である。
- ZIPは必須5ファイルと`licenses/`を含む157 filesで、展開・実行先とのhash一致、weights / runtime data / sample非同梱、同梱FFmpeg 10 entriesを確認した。配布実行ではrepo外cwd、Windows標準PATHのみ、Python環境変数なしで、音声3形式、モデル未配置時の安全な停止、既存smallモデルでの両解析mode、Preview、VMD保存、通常終了・再起動・残留なしを確認した。
- スプラッシュ`Ver. 1.0.0`はユーザー目視確認として記録し、Codex自身の画面取得結果とは扱わない。対象回帰は`8 passed, 21 subtests passed`、process exit code `0`。実MMDはB5で再操作しておらず、MS26のユーザー報告を再判定していない。
- 2026-09-18にB6の候補・証跡・文書監査を完了した。候補#08のEXE / ZIP hashとB5保存証跡は一致し、B1〜B5のPassを継承した。候補sourceのspecは現HEADと同一bytesであり、`THIRD_PARTY_LICENSES.md`の現HEAD差分は候補後の状態記録として候補採用版から分離した。配布bytesを変更する場合はB4/B5の再実施が必要である。
- Python 3.11 / 3.12のsource / build互換性は未検証だが、2026-09-18のユーザー決定によりWindows onefile公開判定の条件から外した。FFmpegは`origin/main`が`2151d7b`を指し、FFmpeg 10 entriesとLICENSE / NOTICE / THIRD_PARTY_LICENSES / Manifestを追跡し、候補branchの`FFmpeg/bin`に差分がないことを確認した。ユーザーはGitHub上の既存公開を規約上問題なしと判断しており、Codexは法的適合を独自に保証しない。exact provider archive identityはB3の非阻害provenance limitationとして維持する。
- よってB6監査報告と既存package/readiness確認は完了記録として保持する。2026-09-18のユーザー決定によりMS27は完了済みとし、追加のリリースパッケージ整備、GitHub公開、tag、push、merge、公開用source archive生成はMS27の完了条件に含めない別工程とする。

## 15. マイルストーン依存関係

```text
MS19 Closeout
  ↓
MS20 Info / Warning / Diagnostics
  ↓
MS21 Per-Event Adjustment / Undo-Redo
  ↓
MS22 Long-Vowel / Presets
  ↓
MS23 Model Profiles / Built-in Morph Names
  ↓
MS24 Whisper Model Selection
  ↓
MS25 Delivery Package
  ↓
MS26 Final Feature Integration / Actual MMD Closeout
  ↓
MS27 Ver.1.0 Closeout / Release Boundary
```

MS24は解析入力側、MS25は出力側の機能である。MS25の診断レポートへ選択Whisperモデル名を記録するためMS24を先とする。MS26で機能受け入れを完了し、MS27はVer.1.0の実装到達状態と公開境界の整理をもって完了とする。追加のbuild・配布パッケージ整備はMS27の完了条件に含めない。

## MS28: Ver.1.0 独立修正実装マイルストーン

### 位置づけ

MS28はMS20〜MS27の全体マイルストーン系列・依存関係・MS27完了判定へ追加しない。Ver.1.0実装後に発見された不具合を、独立した修正実装トラックとして扱う。

### 目的

- TEXT＋音声解析後に母音タイムラインが表示されない問題の原因確認と限定修正
- 音声のみ解析後に母音スムーズ等の生成設定が反映されず、0へ戻る問題の原因確認と限定修正
- 修正によるPreview、Writer、UI同期、Undo / Redo、fail-closed契約の回帰防止

### MS28-B1 / B2の現在地

- `docs/Implementation_Plan/MS28-B1_Implementation_Plan.md`を作成済み。
- 長音後続境界の欠落とrequired-zero conflictによるresolver失敗を主対象とする。
- MS28-B1のproduction code・test code修正は実装済みであり、MS28-B2ではB1の変更を維持したまま隣接long sourceの4分岐、同一frame handoff、R06/R07/R13/R14回帰を追加実装した。
- B2 resolverは39 passed、pipeline / Previewは4 passed、adapter・specは9 passed・21 subtests、全suiteは1100 passed・4 skipped・88 subtests・process exit code `0`、`git diff --check`もexit code `0`である。
- 実Whisperによるユーザー提供ファイルの再解析、native GUI、実MMD、EXE、buildは未実施・未検証である。版数、依存関係、spec / build設定、runtime data、配布成果物はB2で変更していない。

### MS28の対象外

- MS27の完了状態、既存package/readiness証跡、Ver.1.0の公開境界の変更
- GitHub Release、tag、push、merge、公開用source archive生成
- 新機能追加、依存関係変更、配布方式変更、runtime dataの直接編集

## 16. 横断データ・状態契約

### 16.1 表示と正本

- RightPane、Info、Warning、Previewは表示であり、解析・編集・出力の正本ではない。
- 表示文字列からtiming plan、adjustment、writer inputを復元しない。
- 診断表示と `<base>_report.txt` は同じ構造化診断データから生成する。

### 16.2 編集状態

- base timing planを直接破壊しない。
- user adjustment layerを分離する。
- Undo / Redo履歴はセッション内のみ保持する。
- セッション保存・再読込は実装しない。
- 新規作業、入力変更、再解析時のadjustment維持・破棄規則をMS21で固定する。

### 16.3 永続化対象

保存してよいもの:

- アプリ設定
- 生成設定プリセット
- モデル別プロファイル
- Whisperモデル選択
- ダイアログ履歴・Recent Files等の既存設定

保存しないもの:

- 現在の入力ファイル参照を含む作業セッション
- timing plan
- ASR raw result
- user adjustment layer
- Undo / Redo履歴

`presets.json` と `profiles.json` は既存INIと同じ保存場所に置く。どちらもversionを持つ単一JSONファイルとし、初期上限は100件、将来拡張可能とする。

### 16.4 モーフ名

- MS23までは既存の `あ / い / う / え / お` を唯一の出力契約として維持する。
- MS23で、既存日本語名と組み込み英字名を切替可能にする。
- profile未選択時はglobal既定の日本語セットを使用する。
- 任意マッピング、ユーザー定義セット、追加表情はVer.1以降まで保留する。

### 16.5 ネットワーク

- 外部クラウドASRは実装しない。
- 音声データを外部送信しない。
- バックグラウンドネットワークアクセスを追加しない。
- MS24では、ユーザー確認後の前景モデルdownloadだけを例外とする。
- 暗黙の自動downloadとbackground通信を禁止する。

## 17. ドキュメント移行手順

本書作成後、直ちに旧文書を大量改稿するのではなく、次の順序で移行する。

### Phase 1: 本書のActive Planning Baseline化

- 機能採否がユーザー判断と一致するか確認する。
- MS20からMS27の番号、分割、依存順を本書で確定する。
- 本書の機能は計画状態であり、実装済みとは扱わない。

### Phase 2: 新Index作成

- `docs/MS20_and_Beyond_Index.md` を新設し、MS20以降のrouting正本とする。
- `docs/MS17_and_Beyond_Index.md` は履歴Indexとして残し、新正本への案内だけを追加する。

Indexには、現在のブランチ、アクティブMS、正本ロードマップ、現行仕様書、対象コード、テスト入口だけを簡潔に記載する。

### Phase 3: 旧文書へのLegacy表示

- 旧式ロードマップ冒頭へLegacy / Historicalの表示を追加する。
- 本書へのリンクを追加する。
- 完了済み記録本文は書き換えない。
- 旧MS番号を新MS番号へ機械的に置換しない。
- 対象は、本書の3.2に記載した5文書に限定する。

### Phase 4: 現行仕様の同期

必要な仕様書だけを対象に、以下を同期する。

- RightPane / Warning / 診断契約
- adjustment layer / Undo / Redo
- 長音 / preset
- model profile / morph name set
- Whisper model selection
- 一括出力

### Phase 5: 各MSのImplementation Plan作成

各MSの開始前に、Block BreakdownとB1 Implementation Planを作成する。ロードマップ本文だけを実装指示として使用しない。

## 18. 受け入れ条件（本ロードマップ整理）

本書の整理作業は、以下を満たした時点で承認可能とする。

- MS16からMS19の完了記録を改変していない。
- 旧式ロードマップとActive Planning Baselineの役割が分離されている。
- 採用、非採用、Ver.1以降保留、再評価候補が区別されている。
- MS20からMS27の確定番号と主目的が重複していない。
- マイルストーン間の依存関係が説明されている。
- セッション保存を実装しない方針と、プリセット / プロファイルを保存する方針が矛盾なく分離されている。
- 英字モーフセットと英語音声対応が混同されていない。
- 外部クラウドASRと他ASR backendを実装しない方針が明記されている。
- MMD持ち込み用一括出力とアプリ配布packageが区別されている。

## 19. 確定済み設計判断

| 論点 | 確定内容 |
| --- | --- |
| MS20診断レポート | 専用保存操作からUTF-8の `<base>_report.txt` を出力 |
| MS21 Undo / Redo | adjustment layerのsnapshot方式、最大50操作、連続数値変更は1操作へ集約 |
| MS22同音母音 | 既存実装を監査し、残存問題のみ限定改善 |
| MS22 preset | 組み込み＋ユーザーpreset、単一versioned `presets.json`、初期上限100件 |
| MS23 profile | 単一versioned `profiles.json`、既存INIと同位置、初期上限100件 |
| MS24 model / network | `small / medium / turbo`、確認後の前景downloadだけを例外化 |
| MS25一括出力 | 専用directoryへ全成果物を再生成。ZIP・merge・置換は行わない |
| closeout分割 | MS26は機能受け入れ、MS27はVer.1.0実装到達と公開境界の整理。追加package整備は完了条件外 |

## 20. 次に行う作業

MS20-B1のpre-implementation checkと契約固定は2026-07-14に完了した。MS20-B2は2026-07-15に `b6f4254 Implement MS20-B2 diagnostics core foundation` で実装し、UI非依存diagnostics core、canonical fingerprint、writer timing plan共有helper、core testを追加した。B2単体12件、非正duration回帰1件、限定回帰24件はpass表示・終了コード0、全体380件はpass表示・既知wx終了処理由来の終了コード1だった。GUI、UiState、Warning、save policy、report、依存関係、packageは変更していない。

MS20-B3 Implementation Planは2026-07-15に作成し、pre-implementation checkで検出した `clear_info()` 契約、analysis error / cancelのInfo回帰、parameter変更時の二重Preview更新を計画へ反映した。2026-07-16にwx非依存GUI adapter、RightPane Infoの縦scroll表示、MainFrame同期、解析中maskを実装した。B3 adapter単体12件、B3 RightPaneとMS16 RightPane回帰16件、workspace reset回帰8件はpass表示・終了コード0だった。指定限定回帰56件と全体406件はpass表示、failure / error表示なし、既知wx終了処理由来のprocess exit code 1だった。同日、ユーザー手動GUI確認10項目がすべて通過し、問題なしと報告された。確認後の微修正として「再解析が必要」の文字列だけをボールド＋theme別オレンジ系文字色にし、微修正後のユーザーチェックも通過・問題なしと報告された。

MS20-B4 Implementation Planは2026-07-16に作成した。同日のpre-implementation checkで検出した空表示契約、非有限位置、停止後遅延callback、theme追従、routing HEADのP2 / P3をplan内で解消し、wx非依存playback context、RightPaneの独立 `[再生]` label、MainFrame軽量同期を実装した。現在母音はtiming planの半開区間で解決し、gap / 区間外は母音なし、overlapはpeak時刻への距離で決定する。timer経路はB2 snapshot、B3 formatter、Layout / FitInside、Preview再構築を呼ばず、再生位置はfingerprintへ含めない。B4新規24件、関連回帰28件・29件・8件は全件pass表示・終了コード0、全体430件は全件pass表示、failure / error表示なし、既知wx終了処理由来のprocess exit code 1だった。Pause、MCI、Preview cursor、Warning、save policy、reportは変更していない。同日、ユーザーからGUI確認完了・問題なしと報告され、B4は完了した。

MS20-B5 Implementation Planは2026-07-16に作成した。B5はB2 snapshotをRightPane Warning、VMD保存button / menu、controller guardへ接続し、全severity表示、ERROR保存禁止、WARNINGの同一fingerprint一回確認、analysis failureのworkspace内保持を実装対象とする。VMD保存失敗では解析結果と確認済みfingerprintを保持する。同日の実装前チェックでP1なし、P2 2件、P3 1件を検出し、input mode再判定順序、B5基本clearとB7横断監査の責務境界、Block Breakdownの成果物候補一覧を補正した。2026-07-17の再チェックで検出した旧branch指定、theme test順序依存、Index HEAD表記も補正し、workspace diagnostics state、failure adapter、snapshot共有、Warning全severity表示、severity連動VMD保存policyを実装した。B5 / theme限定17件、diagnostics / RightPane限定64件、state / save / failure限定35件＋subtest 7件、pipeline / VMD 12件はpass表示・終了コード0だった。全体442件＋subtest 7件はpass表示、failure / error表示なし、既知wx終了処理由来の終了コード1だった。同日にユーザーGUI確認13項目がすべて通過し、問題なしと報告された。B5はproduction実装、自動検証、ユーザーGUI確認まで完了した。

MS20-B6 Implementation Planは2026-07-17に作成した。B1のreport契約とB2からB5のsnapshot、fingerprint、RightPane表示、保存policyを現行実装へ照合し、UI非依存formatter、timezone付きGenerated At、固定section / field順、LF、UTF-8 BOMなし、source audio stem由来の既定名、File menu専用導線、ERROR時も許可するreport固有save guardを固定した。same-directory temporary file、byte検証、atomic replace、failure cleanupにより既存正常fileを保護する。report保存先履歴、toolbar button、VMD自動同梱、B7横断closeoutは対象外とした。同日の初回実装前チェックでP1なし、P2 2件、P3なしを検出した。元source audio pathとsnapshot正規化pathの責務を分離して共有adapter resolverを使用し、Windowsではwrite / readbackの全temporary handleをcloseしてから `os.replace()` する契約へ補正した。補正後の再チェックではP1 / P2 / P3の残存なしと判定した。

2026-07-18にUI非依存diagnostic report formatter / atomic writer、共有source audio path resolver、File menu、report固有save guard、dialog / controller flowを実装した。B6 core 13件、B6 GUI flow 10件、MS20 diagnostics回帰50件、state / export / reset回帰28件＋subtest 7件、既存output dialog回帰6件、pipeline / VMD回帰12件はpass表示・終了コード0だった。全体465件は全件pass表示、failure / error表示なし、既知wx終了処理由来のprocess exit code 1だった。compileallと `git diff --check` は終了コード0だった。dependency、package、license、Qt、network、固定モーフは変更していない。同日にユーザーから手動GUI確認14項目はすべて通過し、問題なしと報告された。B6はproduction実装、自動検証、ユーザーGUI確認まで完了した。

MS20-B7 Implementation Planは2026-07-18に作成した。B7はB1からB6のdiagnostics stateをinput / parameter / analysis / cancel / late callback / reset / save failureへ横断統合し、旧failure、snapshot、WARNING確認済みfingerprint、cancel表示状態のclear・rebuild・retain規則を回帰testへ固定する。現行parameter変更時のfailure snapshot clearと、coreに存在する `analysis_cancelled` INFOのUiState / adapter接続を限定補修候補とした。README、`readme_mmdautolip.txt`、Pipeline / GUI / Error仕様をMS20-B6完了状態へ同期し、B8 closeout、package、releaseは対象外とする。計画作成baselineの関連48件＋subtest 7件はpass表示・終了コード0だった。同日の初回実装前チェックでP1なし、P2 2件、P3 1件を検出した。input failure契約をdialog cancel、TEXT commit前失敗、音声選択確定後失敗へ分離し、analysis cancel状態はcurrent jobのterminal success / error callbackでだけ確定する契約へ補正した。audio worker state / Busy actionの既存testも指定回帰へ追加した。補正後の再チェックではP1 / P2 / P3の残存なしと判定した。P3で指定回帰へ追加したaudio worker state / Busy action 3件はpass表示・終了コード0だった。補正後のstate / analysis / late / failure / reset指定回帰は48件＋subtest 7件がpass表示、failure / error表示なし、既知wx終了処理由来の終了コード1だった。

2026-07-19の再チェックでP1なし、P2 2件、P3 1件を検出し、audio正常cancel terminalとlate / duplicate callbackの分離、analysis cancel terminal後の非Busy Statusを補正した。補正後はP1 / P2 / P3の残存なしと判定し、`UiState.analysis_cancelled`、adapter接続、analysis cancel terminal Status、parameter変更時のdiagnostics clear、audio cancelled callback guardを実装した。B7専用11件、MS20 diagnostics 97件、pipeline / VMD 12件はpass表示・終了コード0だった。state / analysis / late / failure / reset 48件＋subtest 7件と全体476件はpass表示、failure / error表示なし、既知wx終了処理由来のprocess exit code 1だった。compileallは終了コード0だった。README、配布用readme、Pipeline / GUI / Error仕様を同期し、dependency、package、license、Qt、network、固定モーフは変更していない。同日にユーザーから手動GUI確認は通過し問題なしと報告され、B7はproduction実装、自動検証、ユーザー手動GUI確認まで完了した。

MS20-B8 Implementation Planは2026-07-19に作成した。B8は新機能Blockではなく、B1からB7のcode、test、user、docsを4系統で総合監査し、findingsをP1 / P2 / P3へ分類してMS20 CloseoutをA / B / Cで判定する。MS20固有、state / GUI / worker / voice_only、pipeline / VMD、全体testを段階実行し、pass表示、fatal exception、process exit codeを分離記録する。B3からB7の既存ユーザーGUI確認は、B8で機能変更や証拠不足がなければ再利用する。Aまたはユーザー承認済みBの場合だけ、B8 plan、Block Breakdown、Index、Roadmap、repo milestone、Version ControlをCloseOut済みへ同期する。production code、test code、dependency、build、package、release、merge、push、tag、MS21実装は対象外である。

2026-07-20にB8実装前チェックとCloseout監査を実施した。実装前チェックではP1 / P2なし、P3 1件を検出し、Block Breakdownの古い成果物候補表記を文書同期で解消した。MS20固有108件とpipeline / VMD 12件はpass表示・process exit code 0、state / GUI / worker / voice_only回帰65件＋subtest 7件と全体476件はpass表示まで完走し、failure / error / fatal stack traceなし、process exit codeは既知baselineと同じ1だった。`compileall src tests` と `git diff --check` はprocess exit code 0だった。B3からB7の通過済みユーザーGUI確認を再利用し、Closeout監査後にユーザーからB8チェック通過・問題なしと報告された。dependency、package、build、license、固定モーフ、network、Qtに変更はない。残存findingはP1 / P2 / P3なしで、自動検証とユーザー確認が揃ったためMS20 CloseoutをA判定で確定した。

MS20実装branchは2026-07-20に `main` へfast-forward合流し、`origin/main` へpushした。`main / origin/main` は `6cd8233 Close out MS20 diagnostics milestone` で同期済みである。同コミットから `feature/MS21-implementation` を作成した。

同日に `docs/Implementation_Plan/MS21_Block_Breakdown.md` を作成した。MS21をB1契約固定、B2 adjustment core / resolver、B3 Preview hit-test / selection、B4 RightPane editor / live Preview、B5 VMD / diagnostics統合、B6 in-memory Undo / Redo、B7 state / regression / docs、B8 Closeoutへ分割した。base timing planとadjustment layerの分離、multi-source grouped shapeのidentity、Preview / writer共通resolver、最大50操作のsnapshot履歴、save-state fingerprint、workspace lifecycleを横断契約として固定した。計画作成baselineはselection foundation 4件とPreview / writer / diagnostics回帰71件がpass表示・process exit code 0、state / reset / analysis / playback回帰32件がpass表示・既知wx終了処理由来のprocess exit code 1だった。production code、test code、dependency、build設定は変更していない。

同日に `docs/Implementation_Plan/MS21-B1_Implementation_Plan.md` を作成した。B1はproduction実装を行わず、plan-local event indexとbase plan identity、base / adjustment / effective境界、field validation、grouping適用順、history transaction、reanalysis rollback、MS20 diagnostics handoffを現行code / testへ照合して固定する。ユーザー判断により、slopeは閉口途中の強度比 `0.0〜1.0`、既定 `0.7` とした。grouped shapeでは開口量・開始・終了を各base event、hold / softness / slopeをgroup末尾eventだけに許可する。解析開始時は旧編集をrollback候補として保持し、current job成功時に破棄、failure / cancel時は旧base再利用可能な場合だけ復元する。計画作成baselineはselection 4件、Preview / grouping / multi-point 52件、diagnostics / save policy 24件、reset / late callback / analysis 15件がpass表示・process exit code 0だった。

同日の初回pre-implementation reviewでP1なし、P2 4件、P3 2件を検出し、B1 planとBlock Breakdownを補正した。canonical `base_event_index` とnegative synthetic `shape_source_token` を分離し、skip / synthetic置換されたeventもreal base provenanceとevent rangeから選択・編集可能とした。automatic candidateよりユーザー補正を優先し、影響candidate spanを補正後eventで再評価する。B2はprovenanceとgroup-aware shared resolverを所有し、B3 hit-test、B4 live Preview、B5 writer / diagnosticsは同じresultのadapterを所有する。midpointなしのslopeは無効化・拒否してlatent overrideを残さず、hold / softnessは現行GUIと同じ0から100の整数範囲とした。既存render-only selection setterの未知index許容は維持し、canonical selection commitだけでinvalid / stale / synthetic tokenを拒否する。production code、GUI、test code、dependency、build設定は変更していない。

修正後再チェックではP1 / P2 / P3の残存なしと判定した。selection 4件、Preview / grouping / multi-point 52件、diagnostics / save policy 24件、reset / late callback / analysis 15件はすべてpass表示、各process exit code 0だった。`git diff --check` もprocess exit code 0だった。

2026-07-21にMS21-B1 pre-implementation checkを実施し、P1なし、P2 2件、P3 1件を検出した。observations省略時のevent identity未定義、analysis failure rollbackと現行正本仕様の競合、commit済み文書を未コミットとする古い前提を特定した。計画指定95件と補完72件はすべてpass表示、各process exit code 0だった。

同日にP2 / P3を解消し、MS21-B1 Adjustment Contract / Current-State Pre-checkを完了した。`base_event_index` はnormalization / sorting前のbase timeline ordinalとし、observationsなしを許可、present時はlength / event index / vowel対応をfail closed検証する。canonical編集単位は30fps整数frame、real event intervalの時間上限はsource duration frameとし、peak overrideはanalysis upper limitから分離した。

B2はwriter非依存の専用 `EffectiveShapePlan` DTO、real base provenance、automatic candidate再評価、group-aware shared resolverを所有する。writerとPreviewはこのcore resultを消費し、個別resolverを持たない。analysis failure時の条件付きrollbackは現行正本仕様からの意図的なMS21将来変更とし、failure ERRORと保存禁止を維持する。cancelではcancel INFO付きfingerprintを再構築する。正本仕様のimplemented表示はB7実装後に同期する。

B1実施後の残存P1 / P2 / P3はない。文書補正後の限定回帰は指定95件と補完72件、合計167件がすべてpass表示、各process exit code 0で、`git diff --check` もprocess exit code 0だった。production code、GUI、test code、dependency、build設定は変更していない。次はMS21-B2 Implementation Planを策定する。

2026-07-21にMS21-B2 Implementation Planを作成した。B2はB1で固定したimmutable adjustment model、base plan identity、canonical snapshot、real base provenance、negative synthetic token、candidate再評価、group-aware `EffectiveShapePlan` をUI非依存coreへ実装する。現行 `preview_transform.py` がwriter private helperを直接importしている依存を解消し、Previewとwriterが同じcore shape resultをconsumeする一方向依存へ段階移行する。

B2ではexisting `write_morph_vmd()` / `build_preview_data()` の互換性を維持し、現行GUI PreviewとVMD保存をadjustment付きresolverへ切り替えない。UiState、RightPane、selection、Undo / Redo、fingerprint / report統合はB3以降の責務である。計画作成baselineのPreview / writer / pipeline / diagnostics関連152件はすべてpass表示、各process exit code 0だった。

同日の実装状態整合レビューではP1なし、P2 4件、P3 1件を検出し、B2 planと関連routing文書で解消した。writer module初期化中のcore direct importは `src/core/__init__.py -> pipeline -> src.vmd_writer -> writer` の循環を起こすため採用せず、writer package初期化後の専用adapterとfunction-local delegation、fresh-process import smokeを固定した。adapterは `src/vmd_writer/__init__.py` から初期化時exportせず、明示module pathで読む。両packageの `__init__.py` は読み取り対象に留める。

MS21 adjustment / `ShapeParameters` のhold / softnessは0から100を厳密検証する一方、legacy writer / Previewは現行どおり非負値の100超を受理する。source duration上限はreal / effective event intervalに限定し、最終tail control pointのduration超過と次shapeがある場合のclampを維持する。shape内部定数はcoreへ移し、既存caller向けwriter定数名とcore compatibility mirrorの一致をtestで固定する。production code、GUI、test code、dependency、build設定は変更していない。

2026-07-22のB2 pre-implementation checkではP1なし、P2 2件、P3 1件を検出し、B2 planと関連routing文書へ反映した。repositoryでは `src.vmd_writer.writer` とtop-level `vmd_writer.writer` が別module / classとしてloadされ、既存testは両者を混在使用するため、新規public APIを `src.core.*` に固定しつつ、legacy writer helperをpackage-relative adapterとstructural boundaryで維持する。src / top-level / mixed importのfresh-process検証を追加した。

candidate observationの `previous_non_zero_event_index`、`next_non_zero_event_index`、`span_start_index`、`span_end_index` は、lookup前に型、範囲、span包含、previous / next bracketing順序を検証し、不正値を `AdjustmentContractError` で拒否する。回帰対象に列挙済みだったselection foundation 4件も実行コマンドへ追加した。

補正後再チェックでは残存P1 / P2 / P3なし。関連回帰156件はすべてpassし、4コマンドともprocess exit code 0だった。`src.*` / top-level import smokeも各process exit code 0であり、両writer moduleと `VowelTimelinePoint` が別objectとなる現行事実を再確認した。`git diff --check` はprocess exit code 0だった。production code、GUI、test code、dependency、build設定は変更していない。B2 planは実装着手可能であり、次はB2実装である。

2026-07-22にMS21-B2を実装した。immutable adjustment model、canonical base identity / snapshot、strict validation、candidate handoff、real / synthetic provenance、group-aware effective shape resolver、tail update transactionをUI非依存coreへ追加した。Preview / writerは同じ `EffectiveShapePlan` をpure adapterで変換する。既存Previewは出力互換を守るためlegacy facadeを経由し、`preview_transform.py` からwriter private helperの直接importを除去した。

B2専用35件と指定回帰156件はすべてpass表示、各process exit code 0だった。全体は511件と7 subtestsがpass表示、failure / error表示なしだが、既知wx終了処理系と同じprocess exit code 1だった。`compileall` はprocess exit code 0である。2026-07-22にユーザーから既存GUI回帰確認は通過・問題なしと報告された。event選択・個別補正・RightPane編集・Undo / RedoはB2で未接続のため、この確認結果には含めない。GUI adjustment導線、VMD保存接続、UiState、Undo / Redo、fingerprint更新は未実装であり、次はMS21-B3 Implementation Plan策定である。

2026-07-22にMS21-B3 Implementation Planを作成した。B3はB2 provenanceからreal base eventのhit regionを構築し、vowel lane、event range、base peak距離、base index tie-breakでPreview clickをcanonical selectionへ接続する。clickとpan dragは4 DIP thresholdで分離し、mouse capture lost、Busy、stale base identity、invalid / synthetic index、空lane、event range外ではselectionを変更しない。existing permissive setterは互換維持し、新しいstrict commit境界だけでcanonical selectionを検証する。

B3ではadjustmentなしのfull resolverをGUI Previewへ接続してgrouped shapeの全real provenanceを使えるようにするが、adjustment state、RightPane編集control、VMD保存、fingerprint、Undo / Redoは先行実装しない。計画作成baselineはselection foundation 4件、Preview / viewport回帰16件、B2 adapter 6件がすべてpass表示・各process exit code 0だった。次はB3 planの実装状態整合チェックである。

同日のB3 plan実装状態整合レビューではP1なし、P2 3件、P3 2件を検出し、B3 planとBlock Breakdownを補正した。base identityはshape parameterやadjustmentによる描画dataset差を識別しないため、panel-local render revisionを分離し、mouse-down時とcommit時にbase identityとrevisionの両方を照合する。event hit regionへevent固有のbase peak frameとpeak valueを追加し、grouped segmentの先頭indexや最大intensityをselected event summaryへ流用しない。existing permissive setterは未知index許容を維持しつつcanonical digestをclearし、strict commitだけがindexとdigestを同時更新する。

P3としてbaseline commandのrepository-local path表記を修正し、RightPane Info回帰を限定対象へ追加した。修正後再チェックでは残存P1 / P2 / P3なし。selection 4件、Preview / viewport 16件、B2 adapter 6件、RightPane / playback / reset / late callback 50件はすべてpass表示・各process exit code 0、`git diff --check` もprocess exit code 0だった。次はB3 pre-implementation checkである。

2026-07-23にMS21-B3を実装した。B2 full resolverをGUI Previewへ接続し、UI非依存hit-test、strict canonical selection commit、grouped event summary、4 DIP click / drag分離、stale base identity / render revision拒否、selection lifecycleを追加した。event補正control、adjustment付きlive Preview、VMD保存 / diagnostics統合、Undo / Redoは先行実装していない。

手動GUI確認中にselection outline描画で未定義 `palette` を参照する `NameError` を検出し、current theme palette取得とrenderer回帰test追加で修正した。修正後はB3新規22件、Preview / selection / viewport回帰50件、全体533件と7 subtestsがすべてpass表示、各process exit code 0だった。`compileall src tests` と `git diff --check` もprocess exit code 0だった。

同日に修正後のユーザーGUI確認は通過・問題なしと報告された。開口維持・閉口スムーズ変更による「再解析が必要」表示は現行global parameter invalidation契約どおりであり、B3 selectionの不具合ではない。MS21-B3はproduction実装、自動検証、ユーザーGUI確認まで完了し、次はMS21-B4 Implementation Plan策定である。

2026-07-23にMS21-B4 Implementation Planを作成した。B4はRightPaneの「選択イベント」タブをstructured editorへ拡張し、base / adjustment / effective値を区別して表示する。peak、start / end frame offset、hold / softness、slopeをB1契約で編集し、canonical `AdjustmentLayerSnapshot` とB2 shared resolverからPreviewを即時更新する。group末尾でないeventのtail fieldと、actual midpointを持たないslopeは無効化する。

現行B2 resultにはeditorが必要とするbase event列と、global / override採用値および次shape clamp後のresolved tail値が不足するため、B4でadditive metadataとして公開する。RightPaneではcandidate、grouping、tailを再計算しない。UiState snapshot、identity / editor revision付きcommit、selected reset、Busy lock、inline validationをB4範囲とし、Undo / Redoとrollback完成はB6 / B7へ残す。

B5でadjusted writerとfingerprintを接続するまで、non-empty adjustmentを一時diagnostic ERRORとして単一snapshotへ接続し、Info、Warning、report、bottom Status、button、menu、controllerを同じsaveabilityでfail closedにしてPreviewと保存VMDのsilent mismatchを防ぐ。計画作成baselineはB2 core 29件、B3 selection 22件、RightPane / Info / theme 21件の計72件がpass表示・各process exit code 0だった。

同日の実装状態整合レビューではP1なし、P2 2件、P3 2件を検出した。個別save guardとdiagnostics表示の不一致を単一snapshotへ統合し、analysis開始時はstateを保持してlock、current job cancel時はadjustment / selection / adjusted Previewを保持、failureは現行どおりclearすると固定した。selected reset後はsnapshot全体がemptyの場合だけ既存saveabilityへ戻し、`EVT_TEXT` をvalidation専用としてEnter / focus / spin event由来の重複typed requestを抑止する契約も追加した。レビュー時のB2 / B3 / RightPane / save / lifecycle回帰は29件、22件、28件、19件、15件がpass表示・各process exit code 0だった。P2 / P3をplanへ反映し、この時点の次工程をB4 pre-implementation checkとした。

2026-07-24のB4 pre-implementation checkではP1なし、P2 2件、P3 2件を検出した。一時diagnostic ERRORをcancel INFO抑止の例外にせず既存ERROR規則へ統一し、cancel Statusと開始前state保持は維持する。bottom Statusも同じdiagnostics snapshotから導出し、non-empty adjustment中は「VMD出力可能」をB5対応待ち表示へ置き換える。Enter commit対象controlへ `wx.TE_PROCESS_ENTER` を明記し、actual midpoint消失時のslope cleanupをtail cleanupとは別のtransaction resultへ記録してnon-modal noticeへ投影する契約を追加した。関連168件はpass表示、成功した各test processのexit codeは0だった。RightPane / Info / theme群の初回実行だけ環境側PowerShell runtime読込失敗によりtest開始前にexit code `-2147450726` となり、同一commandの再実行では21件pass・exit code 0だった。P2 / P3はplanとrouting文書へ反映し、その後の再チェックを経てB4実装へ進んだ。

同日にB4 production実装を行い、RightPane structured editor、canonical adjustment commit、B2 shared resolverによるlive Preview、selected reset、B5接続までの一時保存禁止diagnosticsを接続した。ユーザーGUI確認でhold / softness / slopeの効果が見えにくいことが判明したため、resolver semanticsは変更せず、次の口形による反映制限量とslope非作用を一般ユーザー向け効果noticeとして表示する一時修正も実装した。既存のcleanup / B5対応待ち操作noticeとは別control・別入力チャネルで共存する。

B4限定16件、B2 resolver関連35件、B3 selection / Preview関連22件、RightPane / theme関連21件、diagnostics関連37件、pipeline / VMD関連12件はpass表示・各process exit code 0だった。全体550件と7 subtestsもpass表示・process exit code 0、`compileall src tests` もprocess exit code 0だった。dependency、package、build、license、fixed morph、network、Qt、VMD writerは変更していない。同日にユーザーGUI再確認が通過し、問題なしと報告された。B4は実装、自動検証、ユーザーGUI確認まで完了し、次はMS21-B5 Implementation Plan策定である。

2026-07-25にMS21-B5 Implementation Planを作成した。B5はB2 `EffectiveShapePlan` をPreview、VMD writer、diagnosticsの共通派生元とし、save要求内のsnapshotとTEXTあり / voice-only pipelineへ同じplanを渡す。prepared morph frame writerを追加してlegacy writerのbinary出力を共通化し、candidate、grouping、tail、normalizationを保存経路で再実装しない。

save-state fingerprint schemaは `ms21-effective-output-v1` とし、final normalized effective morph frame、effective per-shape tail、model name、既存path / diagnostic identityをcanonical payloadにする。raw adjustment、base identity、selection、history、playbackは含めないため、effective outputが同じeditではWARNING確認を再利用し、output変更時だけ再確認する。diagnostic reportにはbase identity、adjustment有無、補正event数、effective shape数、morph frame数を固定Adjustment sectionとして追加する。B4の一時 `adjustment_vmd_integration_pending` ERRORとB5待ち表示はwriter統合と同時に撤去する。

計画作成baselineのB2 / B4 / pipeline / VMD / MS20 diagnostics / report関連134件はpass表示、process exit code 0だった。production code、test code、dependency、build設定は変更していない。次はB5 planの実装状態整合チェックである。

2026-07-26のB5 plan実装状態整合レビューではP1なし、P2 2件、P3 2件を検出し、計画とrouting文書へ反映した。README、配布用readme、Pipeline / GUI / Error仕様の同期はB7のState Integration / Regression / Docs所有へ戻し、B5はplan、Block Breakdown、Index、Roadmapの進捗記録に限定する。

effective writer inputは `not_applicable / ready / invalid` の3状態とし、未解析・再解析待ちを追加ERRORにしない。保存対象planのresolver / adapter失敗またはready DTO欠落だけを `effective_writer_input_unavailable` ERROR、fingerprintなしとしてfail closedにする。Adjustment summaryはcanonical adjustment entry数を記録し、effective count未算出を `N/A` として正常な0件から分離する。MS14 / MS19の直接保存testもB5回帰対象へ追加した。レビュー時の関連134件はpass表示・process exit code 0、`git diff --check` もprocess exit code 0だった。P2 / P3は解消済みであり、次は補正後planの再チェックである。

同日にMS21-B5本体を実装した。prepared morph frame writer、TEXTあり / voice-onlyの
effective plan保存接続、`ms21-effective-output-v1` fingerprint、固定Adjustment report
sectionを追加し、B4の一時保存禁止diagnosticとB5待ち表示を撤去した。自動検証と
ユーザーGUI確認は通過・問題なしと報告された。

その後のユーザー検証に基づき、単イベント編集時だけ明示的なcrossfadeを許可する
追加補正計画を策定した。automatic解析結果とglobal tailは後続shape直前clampを維持し、
group末尾eventのpositive end offset、event hold、event softnessだけをmanual intentとする。
zero-only groupを保持したtarget探索、同母音での停止、third active group上限、
comparison outputとの差分帰属、範囲外offsetのcore拒否を固定した。

2026-07-26に追加補正を実装した。overlap内のtarget明示control pointが0.95以上の場合は、
値をclipせずRightPaneの選択event領域へattention noticeを表示する。noticeはdiagnostics、
Warning tab、modal確認、保存可否、fingerprint payloadへ追加しない。新規core / editor
17件を含む限定回帰はすべてpass表示・各process exit code 0だった。全体は576件と
7 subtestsがpass表示したがprocess exit code 1、`compileall src tests` はprocess exit
code 0だった。2026-07-26に追加補正のユーザーGUI確認は通過・問題なしと報告された。
B5は追加補正を含め完了した。

2026-07-26にMS21-B6 Implementation Planを作成した。B6はcanonical adjustment
snapshot全体のbefore / afterを用いるセッション内Undo / Redo、最大50操作、
明示gesture tokenによるcontinuous edit coalescing、reset selected / all、Edit menuと
Ctrl+Z / Ctrl+Yを実装対象とする。canonical no-opではredoを保持し、effective outputが
同じでもrequested snapshotが変わるeditは履歴へ記録する。Undo / Redo後は既存shared
resolverと `sync_ui_state()` を使い、Preview、RightPane、diagnostics、fingerprint、
保存可否を再同期する。mouse / key down-upで取得したtokenだけをcoalesceし、wheel /
tokenなしspinはdiscrete fallbackとする。stale token boundaryはstateを変更しない。
Undo / Redo時は汎用operation noticeへ置き換え、effect / crossfade noticeだけを
restored snapshotから再導出する。cleanup operation noticeは履歴へ保存・再現しない。
historyのdisk保存、selection / viewport / playback履歴、
analysis failure / cancel rollback完成、READMEと正本仕様closeoutは対象外とし、後二者は
B7へ残した。計画作成baselineの関連56件、20件、23件はすべてpass表示・各process exit
code 0だった。production code、test code、dependency、build設定は変更していない。
同日の現行実装との整合レビューではP1なし、P2 2件、P3 1件を検出した。
cleanup operation noticeはUndo / Redo時に再現せず汎用文言へ置換する契約、
mouse / key gestureとwheel / tokenなしdiscrete fallback、stale token完全不変、
既存UiStateと同じidentity引数名へ補正した。修正後の再照合では残存P1 / P2 / P3なし。
同日の実装前チェックではP1なし、P2 2件、P3 1件を検出した。selected event editorの
clean / dirtyと他editable text controlを区別するCtrl+Z / Ctrl+Y routing、
same gesture refresh時のactive token保持、selection / Busy / reset / base変更 /
history clear時のRightPane-local state破棄を固定した。selection / Busy / resetでは
pendingを確定し、base変更 / invalidation / history clearではpendingをtransaction化せず
破棄する。補正後の再照合では残存P1 / P2 / P3なし。関連119件はすべてpass表示・
各process exit code 0であり、B6実装へ着手可能である。

同日にMS21-B6を実装した。canonical adjustment snapshot全体をcurrentとするimmutable
history state、before / after transaction、最大50件、redo管理、canonical no-op、
output-equivalent requested edit、明示gesture tokenによるcoalescingを追加した。
UiStateへhistory所有権を移し、RightPaneのmouse / key gestureとdiscrete fallback、
MainFrameのEdit menu、選択的なCtrl+Z / Ctrl+Y、action state、reset selected / all、
dirty入力guardを接続した。Undo / Redo後は既存shared resolverと `sync_ui_state()` から
Preview、RightPane、diagnostics、fingerprint、保存可否を再同期する。

B6 core 12件、B6 wx 9件、関連回帰99件はすべてpass表示・各process exit code 0だった。
最終全体602件と7 subtestsもpass表示・process exit code 0、`compileall src tests` と
`git diff --check` もprocess exit code 0だった。2026-07-26にユーザー手動GUI確認は
全項目通過・問題なしと報告された。B6は実装、自動検証、ユーザーGUI確認まで完了した。
analysis failure / cancel rollback完成、全lifecycle横断監査、README / 配布用readme /
正本仕様同期はB7へ残る。

2026-07-26にMS21-B7 Implementation Planを作成した。B7はState Integration /
Regression / Docsに、ユーザーから報告されたB6 Undo / Redo処理の重さを軽減する
Adjustment Sync Efficiencyを追加する。B1で固定したanalysis rollbackをcurrent job用の
immutable snapshotとして実装し、success時破棄、failure / cancel時のbase identity一致による
条件付き復元、late / duplicate callback完全不変を扱う。failure復元後はERRORを保持して
VMD保存禁止とする。cancel復元後はprior failureがなければcancel INFO付きfingerprintを
再構築してWARNINGを再確認し、prior failureがあれば既存ERRORを復元してINFOを抑止する。

現行Undo / Redoは選択eventがある場合、1操作でbase input最大5回、base identity最大6回、
effective resolver 3回を構築する経路がある。B7では1同期内だけ有効なderived contextを使い、
base input、identity、effective planを各最大1回へ集約してdiagnostics、Preview、
selected editor、action stateへ共有する。edit / reset selectedでは検証済み
`AdjustmentUpdateResult.effective_plan` をhintとして再利用する。adjustment-only同期では
playback、waveform、parameter control、container全体の不要な更新を省く。stale表示を招く
persistent cache、timer、background threadは導入しない。

計画作成baselineはB6 / analysis / late callback / workspace / diagnostics関連47件、
voice_only / save / report / playback関連62件と7 subtestsがすべてpass表示し、
各process exit code 0だった。production code、test code、dependency、build設定は
変更していない。計画作成時点の次工程はB7 planの実装状態整合レビューだった。

同日のB7 plan実装状態整合レビューではP1なし、P2 3件、P3 1件を検出し、
plan、Block Breakdown、Index、Roadmapへ補正を反映した。history未初期化時は
resolverを先に1回だけ実行し、その`effective_plan`とcanonical snapshotから履歴を
初期化してidentityの二重計算を避ける。audio workerのterminal callbackはcurrent job ID、
expected kind、`RUNNING`状態をすべて満たす場合だけ受理し、PROBEからANALYSIS_WAVへ
同一job IDで遷移した後のduplicate PROBEを含むlate / duplicate / kind不一致を拒否する。

analysis failure / cancelのrollback可否は、`invalidate_analysis()`より前にrollback snapshotの
旧timing planとcurrent audio durationから比較identityを求め、capture時のmorph upper limit、
hold、softnessをidentityとは別にterminal時parameterと完全一致検証して判定する。
rollback表示中のanalysis failureは
`StatusKey.ANALYSIS_FAILED_WITH_ROLLBACK`と固定文言
`解析に失敗しました（前回結果を表示中・保存不可）`で通知する。補正後のplanと現行実装の
間に整合レビュー時点で未解消のP2 / P3はなかった。production codeとtest codeは未変更であり、
この時点の次工程はMS21-B7実装前チェックだった。

2026-07-27のMS21-B7実装前チェックではP1なし、P2 4件、P3 1件を検出した。
P2は、failure rollback後のprior ERRORをretry / cancelで失うこと、selected event editorの
dirty入力をanalysis開始同期が上書きすること、base identityに含まれない3 parameterの
一致判定不足、aggregate wx testとfull suiteがpass表示後にprocess exit code 1となることだった。
P3は実装開始基準commitの古い記載だった。

B7 planへprior failure payload、analysis開始前dirty guard、immutable parameter snapshotと
terminal時の別一致検証を追加し、実装開始基準を`3ccf630`へ更新した。B2で採った循環参照回避を
継承し、B7 helperは`MainFrame`からの一方向importだけを許可する。core / writerからGUIへの
逆import、`UiState`との相互import、package `__init__`からのaggregate exportを禁止し、
fresh-processのhelper先行 / MainFrame先行import smokeをgateとする。

P2 / P3のplan契約は解消済みである。ただしaggregate wx testの終了コードは未解消の実行gateであり、
受け入れ条件を弱めない。full suite 602件と7 subtestsは2回ともpass表示・process exit code 1、
wx抽出91件はpass表示・511件deselected・process exit code 1だった。直接原因をPython / wx
versionだけに帰属せず、B7 Step 0でtest teardownを原因分離・最小補修し、wx aggregateと
full suiteのprocess exit code 0を確認するまでproduction codeを変更しない。

2026-07-27にMS21-B7を実装した。analysis開始時にcurrent job専用rollback snapshotへ
旧timing plan、base identity、adjustment history、selection、prior failure、morph upper
limit / hold / softnessをcaptureする。failureでは同一base / parameterの場合だけ旧stateを
確認用に復元し、current ERRORとVMD保存禁止を維持する。cancelではprior failureがなければ
cancel INFOを生成し、prior failureがあれば既存ERRORを復元してINFOを抑止する。
selected editor dirty入力はjob ID更新前に拒否し、parameter mismatch terminalはresultを
commit / rollbackせず再解析待ちへ移行する。

analysis terminalはcurrent job IDとactive状態、audio worker terminalはcurrent job ID、
expected kind、`RUNNING`状態で受理をguardする。B7 helperはMainFrame所有の一方向依存とし、
package `__init__` export、core / writerからGUIへの逆import、UiStateとの相互importを追加していない。
fresh-processのhelper先行 / MainFrame先行import smokeを追加した。

Undo / Redo効率化では、1同期限定contextからdiagnostics、Preview、selected editor、
action stateへ同じeffective planを渡す。edit / reset selectedのvalidated hintを再利用し、
adjustment-only同期でplayback context、ParameterPanel、PlaceholderContainer全体の不要更新を
省いた。RightPane Infoは同一内容時のwrap / layoutを省略する。

実装中にwx aggregateのaccess violationを再現し、startup splash testが実SplashScreenを
生成したままmock済み`CallLater`により破棄しないことを直接原因として特定した。
SplashScreen test doubleとApp / Frame明示teardownへ限定補修し、wx aggregateをpass表示・
process exit code 0へ戻した。B7専用15件、B3からB6回帰61件、lifecycle回帰47件と
7 subtests、wx aggregate 97件、full suite 617件と7 subtestsもpass表示・process exit
code 0だった。README、配布用readme、Pipeline / GUI /
Error仕様をimplemented状態へ同期した。この時点ではユーザー手動GUI確認前であり、
後続の確認で追加tab補正要望が提示された。

その後のB7ユーザー手動GUI確認で、Previewタイムラインの単母音eventを選択した場合に
RightPaneの「選択イベント」タブへ自動切替する小規模補正が要望された。
2026-07-27に追加補正計画を作成して現行selection / Notebook / lifecycleへ照合し、
残存P1 / P2 / P3なしと判定した。

同日に追加補正を実装した。`RightPane`は固定page indexを使わず
`FindPage(panel_selected_event)`でpageを解決し、Preview user clickのcanonical commit
成功後だけ`ChangeSelection()`する。same-event再clickではeditor tabへ戻り、stale /
Busy request、通常sync、Undo / Redo、analysis rollbackではcurrent tabを維持する。
RightPane 3件、Preview selection 6件、Undo / Redo・B7 lifecycle 12件、
wx aggregate 90件、full suite 618件と7 subtestsはpass表示・各process exit code 0だった。
その後、自動test中にanalysis failure callbackが実`wx.MessageBox`を開く問題を特定した。
productionの通知契約は変更せず、該当test内でMessageBoxをmockして通知呼び出しを検証する
限定補修を行った。補修後のfull suiteも618件と7 subtestsがpass表示・process exit code 0だった。

2026-07-27にユーザーから、追加補正を含むMS21-B7範囲の手動GUI確認は通過し、
問題なしと報告された。MS21-B7は完了し、次工程はMS21-B8 Closeout計画である。

2026-07-31にMS21-B8 Closeout監査を実施した。B1〜B7の証拠台帳、指定回帰、MS17 / MS19 /
MS20回帰、full suite、compileall、git diff check、ユーザー確認範囲、依存・配布境界を
確認し、すべての自動検証はpass表示・process exit code 0だった。P1 / P2 / P3はなく、
MS21 CloseoutをAで確定した。B8ではproduction code、test code、dependency、build /
package / license、fixed morph、VMD形式、network契約を変更していない。実MMDでのVMD /
WAV読み込み・リップ同期はMS26へ引き継ぎ、次工程はMS22のImplementation Plan策定である。

2026-08-01にMS22-B1 Contract Pre-checkを実施し、正規化済み読み列を長音検出正本とするtoken / timeline /
shape契約、decay終端exact `0.0`、preset / `presets.json` / INI責務、output edit history、diagnostics /
fingerprint / lifecycle、B2〜B6のownershipを固定した。指定回帰336件、`compileall src tests`、
`git diff --check`はすべてexit code 0で、P1 / P2 / P3は残存しない。B1ではproduction code、test code、GUI、
dependency、build設定を変更していない。次工程はMS22-B2 Implementation Plan策定であり、MS22のproduction機能は
未実装のまま維持する。

2026-08-01にMS22-B2 Implementation Planを作成した。B2はnormalized readingからimmutable token、timeline
metadata、MS22 identity / adjustment schema、explicit long run、run member別adjustment所有権、hold / decay、
same-vowel隔離、Preview / writer adapter整合をUI非依存coreへ実装する計画である。decayはユーザー判断どおり
長音terminal endでexact `0.0`とし、holdはterminal endまでpeakを維持してclosing edgeを終端後へ置く。
preset JSON / INI、GenerationSettings、state / history / diagnostics、RightPaneはB3以降へ維持する。計画作成時の
関連回帰227件はpass表示・各process exit code 0で、production code、test code、GUI、dependency、build設定は
変更していない。次工程はB2 pre-implementation checkである。

同日のB2 plan実装状態整合レビューではP1なし、P2 2件、P3 2件を検出し、計画とrouting文書へ反映した。
source start / peak同一frameではopening zeroを省略してpeakを優先する。long required zeroと別shapeのpositive
pointが同一morph・同一frameで競合する場合はnormalization前にfail closedとし、異なるmorphの同一frame配置は
受理する。hold / decay双方へnon-`None` resolved tail metadataを付与し、decayはrequested tail / slopeをlatent、
effective tailを0、slope midpointなしとして既存consumerの構造前提を維持する。B2新規test file 5件を必須化し、
adjustment history、selected editor、UI sync context回帰を指定commandへ追加した。計画作成baselineを含む関連
251件はpass表示・各process exit code 0だった。production code、test code、GUI、dependency、build設定は
変更していない。P2 / P3は文書上で解消済みで、当時の次工程はB2 plan再チェックだった。

2026-08-06にMS22-B2実装前チェックを再確認した。source / terminal event frameはsource duration内、
最終shapeのgenerated closing zeroだけは既存resolved final tailによりduration超過可能、次shapeがある場合は
既存clampを維持する契約へBlock BreakdownとB2 planを統一した。source peak frameはbase timeline frameで固定し、
B2 adjustmentはpeak valueだけを変更する。Block BreakdownへMS21-B6 adjustment history、MS21-B4 selected event
editor、MS21-B7 UI sync contextの3回帰を追記した。対象回帰251件、full suite 618件＋7 subtests、
`compileall src tests`、`git diff --check`はすべてpass表示・process exit code 0だった。production code、
test code、GUI、dependency、build設定は変更していない。P1 / P2 / P3の残存はなく、次工程はMS22-B2実装である。

2026-08-06にMS22-B2を実装した。normalized readingの`VowelToken`、timeline metadata、MS22 identity /
adjustment schema、explicit long runのrole / ownership、hold / decay shared resolver、Preview / writer adapter
整合をUI非依存coreへ追加した。B2専用test 26件、関連回帰、full suite 644件＋7 subtests、`compileall src tests`、
`git diff --check`はすべてpass表示・process exit code 0だった。GUI、preset / INI、state / history、diagnostics、
dependency、package、実MMD確認は変更・実施していない。B2のP1 / P2 / P3は残存せず、次工程はMS22-B3
Generation Preset Store / Settings ContractのImplementation Plan策定である。

2026-08-08にMS22-B3 Generation Preset Store / Settings ContractのImplementation Planを作成した。B3はB2の
primitive `LongVowelMode` validationを入力として、immutable `GenerationSettings`、built-in / user preset、
schema version 1の`presets.json`、INI active settings / active preset id、strict validation、atomic save、
invalid JSON時のread-only unavailable、Custom fallbackをUI非依存coreへ実装する計画である。既存`SettingsStore`
の旧callerが新generation keyを省略しても、保存済みactive settingsをdefaultで上書きしない互換条件を受け入れ
条件へ追加した。B3のproduction code、test code、GUIは未実装である。

同日の実装状態再チェックではP1なし、P2 3件、P3 3件を検出した。P2は外部修復後の次回`load()`復帰、
load / mutation / active resolutionのstructured result、既存INIを保持するadditive保存表現であり、P3は既存INIとの
責務表現、update同名判定、B2直接回帰commandの列挙であった。B3 planへこれらを反映し、修正後の再チェックでは
P1 / P2 / P3の残存なしと判定した。コード、test、GUI、依存関係、INI / JSON本体は変更せず、次工程は
MS22-B3実装前チェックである。

2026-08-08にMS22-B3を実装し、`4ee67af Implement MS22-B3 preset store and settings contract`へ記録した。
`GenerationSettings`、built-in / user preset、schema version 1の`presets.json`、INI active settings / active
preset id、strict validation、atomic save、failure isolation、Custom fallbackをUI非依存coreへ追加した。
B3専用test 23件＋19 subtests、指定回帰、full suite 667件＋26 subtests、`compileall`、`git diff --check`を
pass・exit code 0で確認した。実装後レビューのP2 / P3は文書同期と境界・atomic failure test補強で解消した。
B3の選択UI、state / history / diagnostics統合、B4以降、実MMD確認は未実施であり、次工程はMS22-B4
Implementation Plan策定である。

2026-08-08にMS22-B4 Generation State / History / Diagnostics IntegrationのImplementation Planを作成した。
B4はbaseなしでも常在する`GenerationState`、base確定中の`OutputEditState`、adjustment / generation settings /
active preset idを一括復元する最大50件のhistory、resolve-before-commit、output-only parameter、startup / INI、
analysis rollback、diagnostics統合を所有する。B5のRightPane preset selector、管理dialog、terminal event mode controlは
先行実装しない。

現行`BasePlanIdentity`がgeneration settingsを含まないため、`EffectiveShapePlan`だけがresolver入力
`ShapeParameters`のprovenanceをadditiveに保持し、base identity・adjustment・shape parametersの一致をhint guardとする。
これによりnon-no-op preset適用、direct edit、Undo / Redo後のresolver 1回とstale generation hint拒否を両立する。
generation summaryへactive mode / presetとeffective hold / decay run数、adjustment summaryへmode override数を追加するが、
MS21 fingerprint canonical payloadと`ms21-effective-output-v1`は維持する。

計画作成baselineはB2 / B3 / history 53件＋19 subtests、wx state / lifecycle 22件、diagnostics / VMD 62件、
RightPane / warning / save 43件の合計180件＋19 subtestsがpass表示、failure / error表示なし、各process exit code 0だった。
production code、test code、GUI、INI / JSON本体、dependency、build設定は変更していない。B4 production実装とmanual GUI確認、
実MMD確認は未実施である。

同日の自己回帰チェックではP1なし、P2 5件、P3 3件を検出した。`EffectiveShapePlan`をshape-parameter provenanceの
唯一ownerとし、active preset中のsettings同値direct eventはidを保持するno-op、settings同値・id異値のpreset applyは
id-only transactionと固定した。canonical stateからhold / softness controlへのguard付き投影、candidate拒否時の値復元、
I/Oなしcontroller constructorとtemporary startup store、generation変更も含む「出力編集」のUndo / Redo文言も明記した。
さらにstartup / workspace reset / import boundary回帰、generation state単独をworkspace user dataへ数えない条件、
save-disabled後の後続要求を`attempted=False`とする契約を追加した。追加回帰19件を含む関連199件＋19 subtestsはpass表示・
各process exit code 0、`git diff --check`もexit code 0だった。P2 / P3は文書上で解消済みで、次工程は修正後plan再チェックと
B4実装前チェックである。

2026-08-09のB4実装前チェックでは新規P2 3件、P3 2件を検出した。P2は、deleted / mismatched presetをUndo / Redoする際の
history before / after endpointのatomic正規化、`AutoLipToolApp`から`AppController`へ同じtemporary storeを渡すstartup
seam、candidate adjustment `None`をempty snapshotとして扱うstale hint guardである。P3はdiagnostics DTOのmode / count /
active id・display name不変条件と、selected event editor core / wxおよびMS21-B3 pipeline-preview integration回帰の
列挙漏れである。production code、test code、GUIは変更せず、B4 planとBlock Breakdownへ限定反映した。以前解消した契約は
変更せず、修正後再チェックを経てB4実装前チェックを再実行する。

2026-08-09にMS22-B4を実装した。`GenerationState` / `OutputEditState`、最大50件のatomic output history、
output-only generation settings、startup store seam、analysis rollback、diagnostics統合を追加した。
同期context cacheは`OutputEditState`全体（active preset IDを含む）と照合し、id-only Undo / Redo後もresolverを
再実行する回帰を追加した。`AnalysisParameterSnapshot`はmorph upper limitだけを保持する契約へ整理した。
B4専用test、MS20 / MS21 / MS22回帰を確認した。手動確認で判明した母音Preview非表示は、RMS補正後の
別母音を挟む同一モーフ境界競合をpipelineで限定補修した。修正後の関連33件、full suite 686件＋26 subtests、
`compileall`、`git diff --check`をpass・exit code 0で確認した。2026-08-09にユーザーから問題解消と
MS22-B4手動テスト通過が報告された。preset selector UIはMS22-B5、実MMDでのVMD / WAV読み込み・
リップ同期はMS26へ引き継ぐ。

2026-08-09にMS22-B5 Preset UI / Event Override FlowのImplementation Planを作成した。B5は、B4の既存
`commit_generation_settings` / `apply_preset_generation`とB3の`GenerationPresetStore`を利用し、RightPaneの
`プリセット` tabへbuilt-in / user / Customの一覧、明示的な選択とApply、create / update / rename / delete、
mutation failure noticeを接続する。active presetのupdate / delete後は出力を暗黙に再適用せず、必要時にCustomへ
正規化する。terminal continuation eventに限りinherit / hold / decayを選択でき、decay時はterminal zeroを
説明しながらlatent tailを保持してhold復帰時に再利用する。preset mutationとoutput state、選択とApplyを別の
transactionとして扱い、B4のresolver・history・diagnostics・JSON schemaは再実装しない。

計画作成時の関連回帰53件はpass表示・process exit code 0だった。B5のproduction code、test code、GUI、
INI / JSON本体、依存関係、build設定は変更していない。次工程はB5 planの実装状態再チェック、P2 / P3修正、
B5実装前チェックであり、B6の横断docs / lifecycleとMS26の実MMD確認はB5の範囲外として維持する。

同日のB5 plan実装状態整合レビューではP1なし、P2 3件、P3 2件を検出し、計画とrouting文書へ反映して
解消した。active preset update / delete後はeffective resolverを使わず、base-bound historyのcurrent・undo・
redo全endpointまたはbaseなし`GenerationState`を同じsettingsのCustomへ正規化し、追加historyを作らずINI保存要求を
1回行う。load failureとmutation failureはresult型・mutation availability・error codeのmatrixで区別する。
Select / Apply / Create / Update / Deleteのimmutable request DTO、expected revision、mode requestのstr / None型と
discrete transaction、create / update / delete後のselector fallback、B4 generation history直接回帰も固定した。

修正確認ではB3 / B4 state・history関連35件、B2 resolver / selected editor関連32件がpass表示・各process
exit code 0、`git diff --check`もexit code 0だった。production code、test code、GUI、INI / JSON本体、依存関係、
build設定は変更していない。次工程は修正後plan再チェックとB5実装前チェックであり、B6 docsとMS26実MMD確認は
未実施のまま維持する。

2026-08-10にMS22-B5を実装した。RightPaneのpreset tab、stable IDによるSelect / Apply分離、user presetのcreate /
update / rename / delete、load / mutation failure notice、active presetのCustom正規化、terminal continuation event限定の
inherit / hold / decay overrideを接続した。B5専用test 10件、スプラッシュテストを除く既存全体回帰694件、
`compileall src tests`、`git diff --check`をprocess exit code 0で確認し、ユーザーからB5手動GUI確認通過が報告された。
全体実行で発生した既存`tests/test_wx_startup_splash.py`の起動時間依存1件失敗はP3としてMS22-B6へ引き継ぐ。
実MMDでのVMD / WAV読み込み・リップ同期確認はMS26へ維持する。次工程はMS22-B6 Lifecycle Regression / Documentationである。

2026-08-11にMS22-B6 Lifecycle Regression / DocumentationのImplementation Planを作成・再レビューした。B6は、
MS22-B2からB5のgeneration state、preset、long-vowel、output historyを、TEXTあり／voice-only、analysis lifecycle、
save / diagnostics failure、workspace resetへ横断接続し、startup splash / wx teardownを決定論化する。README、配布用readme、
Pipeline / GUI / Error仕様、Index / Roadmap / Block Breakdownの実装状態同期とmanual GUI確認範囲の記録もB6が所有する。
MS22 Closeout判定はB7、実MMD確認はMS26へ維持する。

plan本文の再チェックで検出したP2 4件・P3 2件を解消した後、計画策定状態がBlock Breakdown、Index、Roadmapへ
未反映だったP2 1件を本同期で解消した。計画作成baselineはstartup splash単独2件、MS22 / lifecycle関連122件、
full suite 696件がpass表示・process exit code 0だった。一方、B4 / B5 / splashの既知17件組合せは17件pass表示・
process exit code 1であり、B6の原因分離対象として残る。B6 implementation、B6専用test、manual GUI確認は未実施である。
これは実装前の計画段階の記録である。

2026-08-11にMS22-B6を実装した。non-wx lifecycle 7件、wx lifecycle 9件、splash 3件を追加・決定論化し、
wx終了時のcoalesced save timer停止、`AutoLipToolApp`の遅延Layout / Refresh callback guard、
test teardown helperを限定補修した。B2専用29件、B3〜B5専用45件、
settings / export 13件、B4 / B5 / splash組合せ18件、MS17〜MS21 lifecycle 36件、save / diagnostics 33件、
full suite 713件、`compileall src tests`、`git diff --check`はすべてprocess exit code 0だった。
自動検証後、2026-08-11にユーザーから手動GUI確認通過・問題なしの報告を受領した。これはCodex自身のGUI実行結果とは扱わない。
MS22 Closeout判定はB7、実MMDでのVMD / WAV読み込み・リップ同期確認はMS26へ維持し、次工程はMS22-B7 Closeoutである。

2026-08-11にMS22-B7 MS22 CloseoutのImplementation Planを作成した。B7はB1からB6の要求、実装、test、
ユーザー確認、文書、runtime user data、dependency / package境界を一つの証拠台帳へ統合し、P1 / P2 / P3を
分類してA / B / Cで判定する。計画作成baselineはMS22 B2〜B6専用＋splash 93件、full suite 713件、
`compileall src tests`、`git diff --check`がpass表示・process exit code 0だった。MS21 Closeout基準から
dependency / package / build / license fileの差分はなかった。

current repositoryでtrackedの`presets.json`がuser preset値を保持する点をruntime user data境界のP2候補、
B5 plan / Blockに残るsplash P3 pendingをcurrent status未同期のP3候補としてpre-closeout gateへ固定した。
計画策定中はproduction code、test code、GUI、runtime file、dependency、packageを変更していない。
次工程はMS22-B7実装前チェックであり、Closeout A / B / C判定は未実施である。実MMD確認はMS26へ維持する。

同日のB7計画レビューで、tracked `presets.json`をruntime user data境界のP2、splash current status未同期を
P3として確定した。local `presets.json`を保護したままGit追跡を解除し、`.gitignore`へroot限定の
`/presets.json`と`/MMD_AutoLipTool.ini`を追加した。B5時点のsplash失敗記録は保持し、B6でsplash 3件、
known組合せ18件、full suite 713件がpass・exit code 0だった現在状態をB5 plan、Block、Index、Roadmapへ同期した。
production code、test code、GUI、dependency、packageは変更せず、P2 / P3を分離repairで解消した。

2026-08-12にMS22-B7 Closeout監査を実施した。MS22 direct regression 93件、基盤回帰185件、MS21回帰138件、
MS17 / MS19 / MS20回帰158件、B4 / B5 / splash組合せ18件、full suite 713件、`compileall src tests`、
`git diff --check`をすべてpass・process exit code 0で確認した。P1 / P2 / P3はなく、MS22 CloseoutをAと判定した。
`presets.json` / `MMD_AutoLipTool.ini`のGit追跡対象外・root限定ignore・local保持を確認し、dependency / package /
build / license差分はなかった。production code、test code、GUIは変更していない。B4 / B5 / B6手動GUI確認はユーザー報告の
範囲に限定して再利用し、Codex自身のGUI実行結果とは扱わない。実MMDでのVMD / WAV読み込み・リップ同期確認はMS26へ
deferredのまま維持する。次工程はMS23 Implementation Plan策定であり、MS23実装は開始しない。

2026-08-12にMS23 Model Profiles / Built-in Morph Name SetsのBlock Breakdownを作成し、現行code、test、MS22完了契約へ
再照合した。初回案で検出したP2 7件、P3 2件は計画文書上で解消し、P1はなかった。profile selection、
`morph_upper_limit`のanalysis invalidation、output-only history、preset reference failure、effective output fingerprint、
`/profiles.json`のruntime user data、event adjustment field ownership、B2〜B4の責務を分離した。MS25専用batch DTO / adapterは
先行実装しない。production code、test code、GUIは変更していない。次工程は`default_preset_id`方針のユーザー確認と
MS23-B1 Implementation Plan策定であり、MS23実装は開始していない。実MMD確認はMS26へ維持する。

同日にユーザーはMS23のD1を採用した。profileの`default_preset_id`はpreset値の複製ではなくstable referenceとし、
参照先presetをbaseline、profileのnon-null fieldをoverride、nullable fieldをpreset継承として解決する。active profile中に
別presetをApplyしてもnon-null overrideを維持する。MS23-B1 Implementation Planを作成し、参照中user presetのdelete guard、
active profile mutation、startup unresolved fallback、fingerprint schemaを次のdecision gateとした。production code、test code、
GUIは変更していない。B1 contract pre-checkとMS23実装は未開始であり、実MMD確認はMS26へ維持する。

2026-08-13にMS23-B1 Implementation Planを再チェックし、P2 5件を計画文書上で補正した。B2ではwriterからcoreへの
module-level逆importと`src.*` / top-level class identity依存を禁止し、semantic final normalization完了後にoutput nameだけを
一回mappingする。D1Aとして、profile Apply直後は`default_preset_id`、active profile中の別preset Apply後はINIの
専用キー`active_profile_baseline_preset_id`をcurrent runtime baselineとして再起動でも優先する。active profile中は既存
`active_preset_id=None`とし、preset単独時のCustom正規化は変更しない。
Applyのvalidation / resolution / commit前failureは完全不変、commit後INI save failureはin-memory state / historyを
rollbackしないMS22契約を維持する。初回wx baselineは19件pass表示後にexit code 1だったが、関数単位の切り分け、全8件、
元の19件commandをtest変更なしで再実行し、すべてexit code 0を確認した。production code、test code、GUIは変更していない。
B1はこの時点ではD2〜D5が未確定のためContract Fixedではなく、実MMD確認はMS26へ維持する。

同日、ユーザーはD2〜D5をすべて推奨案Aで採用した。profileから参照中のuser presetは参照変更までdeleteを拒否し、
active user profileのvalue / set updateとdeleteはinactive化まで拒否する。startup unresolved profileはno-profile + Japaneseへ
正規化してINI数値を保持し、valid profileの専用runtime baselineだけがunresolvedならprofile default presetへfallbackする。
canonical fingerprint payload構造と`ms21-effective-output-v1`は維持する。全decision gateは解消済みで、B1 contract pre-checkは
着手可能だが未実施である。production code、test code、GUIは変更しておらず、実MMD確認はMS26へ維持する。

同日のB1実装前チェックでは、active runtime baseline preset mutationとactive profile中global direct editによってbaseline identityと
current effective値が不一致になり得るP2 2件を検出した。ユーザーの解消指示に基づき、D6としてactive runtime baseline presetの
value update / deleteをprofile inactive化または別baseline選択まで拒否し、settings同値Renameだけをmetadata mutationとして許可する。
D7としてactive profile中のglobal generation settings / `morph_upper_limit` direct editはexact no-op以外をcommit前に拒否する。
event adjustment、active profile中の別preset Apply、no-profile時のMS22 direct edit、preset単独時のCustom正規化は変更しない。
P2は計画文書上で補正済みであり、次工程は補正後B1 contract pre-checkのread-only再チェックである。production code、test code、GUIは
変更しておらず、実MMD確認はMS26へ維持する。

2026-08-15のB1再チェックでは、startup seam testが実スプラッシュを生成してaccess violationによるexit code 1を起こすP2を確認した。
splash専用testとの責務を分離するtest isolationを補正し、同一19件commandをpass表示・exit code 0へ復帰させた。live Git記述、
read-only code対象、P1/P2/P3 gate表記のP3も同期して解消した。その後、現行preset schemaとの照合でB1 planに残っていた
profile schemaのunknown key、display name、ID、`default_preset_id`の未確定表現をS1として補正し、文書上のP2を解消した。
MS23 featureのproduction code、test code、GUI実装は開始しておらず、実MMD確認はMS26へ維持する。次工程は補正後B1
contract pre-checkのread-only再チェックである。

同日の一問一答で、built-in ID（`builtin:japanese-vowels` / `builtin:latin-vowels`）、専用core profile state、
`GenerationState`のresolved morph-name set ID、B4のcross-store resolution / mutation guard、workspace reset時のprofile保持、
profile nullable `morph_upper_limit`、startup補正後IDのINI保存を採用した。B1 / Block Breakdown / Index / Roadmapの計画記述を同期し、
exact class名、private helper名、error code名だけをB4 planへ明示的にdeferした。MS23実装は開始しておらず、当時の次工程はfresh read-only
B1 contract pre-checkである。

2026-08-15にfresh read-only B1 contract pre-checkを実施した。現行Git、B1関連計画、MS22 Closeout A、profile未実装の現行code境界、
関連test、dependency / package境界を再照合し、249件がpass表示・全command process exit code 0、`git diff --check`もexit code 0、
P1 / P2 / P3なしを確認した。B1をCompleted / Contract Fixedと判定し、B2 / B3 Implementation Plan策定へ進める状態へ同期した。
これは契約・計画段階の完了であり、MS23 featureのproduction code、test code、GUI実装完了ではない。profile実装、`profiles.json`生成、
`/profiles.json` ignore追加はB3へ、実MMDによるVMD / WAV読み込み・リップ同期確認はMS26へ維持する。

2026-08-16にMS23-B2 Built-in Morph Name Set / Output Mapping Implementation Planを作成した。built-in setの正本をcoreのleaf moduleへ置き、
semantic vowel keyを維持したまま、writer、Preview、diagnosticsへ検証済みordered output namesを明示的に渡す境界を固定した。
final semantic normalization後に一度だけmappingし、日本語default、VMD 30fps、frame number / value / count / sort order、Preview hit-test、
既存fingerprint schemaを維持する。writerからcoreへのmodule-level逆import、`src.*` / top-level class identity依存、profile store、INI、
MS25 batch実装はB2の対象外である。B2のproduction code、test code、GUIは未実装で、planレビュー後に開始する。実MMD確認はMS26へ維持する。

同日のMS23-B2 Implementation Plan再チェックで、P2 4件を計画文書上で補正した。writer / coreのvalidation authority、diagnostics DTOの
allowed-name入力、Previewのsemantic key / display name分離、B2 / B4 fingerprintテスト責務を明示し、既存引数・既存DTO構築・
semantic hit-testを維持する互換境界を固定した。関連回帰162件はpass表示・process exit code 0、`git diff --check`もexit code 0だった。
production code、test code、GUI、runtime user dataは変更しておらず、B2実装は未開始のまま維持する。

同日のMS23-B2実装前チェックで、Previewのempty / empty timeline / clear時にLatin表示が日本語へ戻り得るP2と、
`MorphNameSet`のbuilt-in display nameがB2 DTO契約から欠落しているP2を確認した。B2 planとBlock Breakdownへ、
explicit ordered output-name tupleを空状態にも渡す契約、既存省略時の日本語default、`MorphNameSet`からのdisplay name取得、
B4でのID別表示名表再構築禁止を追記した。production code、test code、GUI、runtime user dataは変更せず、B2実装は未開始である。

同日、MS23-B2を実装した。`MorphNameSet`とJapanese / Latinのbuilt-in mapping、writer / effective-shape adapterの
normalize-before-map境界、Previewのsemantic key / display name分離、diagnosticsのresolved output-name境界、
fresh-process import boundaryを追加した。B2専用24件、関連回帰228件、full suite 738件、`compileall src tests`、
`git diff --check`はすべてpass・process exit code 0だった。既存省略経路の日本語default、VMD 30fps、frame number / value / count /
sort order、Preview hit-test、fingerprint schemaは維持している。手動GUI確認は未実施で、profile store、INI、runtime user data、
B3 / B4 / B5、MS25以降の実装は行っていない。実MMDによるVMD / WAV読み込み・リップ同期確認はMS26へdeferredのままとする。

同日、ユーザーからMS23-B2の手動GUI確認完了・問題なしの報告を受領した。これはユーザー確認の範囲に限定して記録し、
Codex自身のGUI実行結果とは扱わない。profile store、INI、runtime user data、B3 / B4 / B5、MS25以降の実装は行っていない。
実MMDによるVMD / WAV読み込み・リップ同期確認はMS26へdeferredのままとする。

同日、MS23-B3 Model Profile Store / Persistence Implementation Planを作成した。B3はB1で固定したschema v1に従う
immutable profile DTO、INIと同じdirectoryのstrict versioned `profiles.json`、最大100件、structured load / mutation result、
same-directory temporaryとclose-before-`os.replace()`によるatomic Create / Update / Deleteを実装対象とする。INIには
`active_model_profile_id`と`active_profile_baseline_preset_id`をadditiveに追加し、旧callerが新2 keyを省略したsaveでは既存値を
保持する。`/profiles.json`はroot限定ignoreとし、testはtemporary directoryだけを使う。cross-store preset lookup、missing reference、
active profile mutation guard、startup fallback、precedence / state / history / diagnosticsはB4へ残す。計画作成時のread-only baselineは
B2 + preset / settings 53件＋19 subtests、SettingsStore consumer群67件＋19 subtestsがpass表示・各process exit code 0だった。
production code、test code、GUI、runtime user dataは変更していない。次工程はB3 planレビューとfresh read-only
pre-implementation checkであり、B3実装は開始していない。実MMD確認はMS26へ維持する。

同日のB3 Implementation PlanレビューではP1なし、P2 3件、P3 1件を確認した。P2はB1の`morph_upper_limit: finite float`
契約に対してJSON intまで受理していたこと、constructor直後のload前mutation契約がなく既存fileを空collectionで上書きし得たこと、
INI同一directoryのtarget pathを直接検証するtestがなかったことである。P3はB4の将来都合による`src/core/__init__.py`変更余地である。
B1 strict floatへ戻し、constructor直後をunloaded / mutation unavailable、load前mutationを`store_not_loaded`でfile access前拒否、
load前lookupをcontract errorとした。settings path、SettingsStore注入、explicit `profiles_path`、引数排他の直接testを追加し、
package root exportはB4へ完全延期した。production code、test code、GUI、runtime user dataは変更していない。次工程は補正後planの
fresh read-only再チェックである。補正後のread-only回帰は53件＋19 subtests、67件＋19 subtestsがpass表示・各process exit code 0だった。
B3実装は開始しておらず、実MMD確認はMS26へ維持する。

2026-08-17にMS23-B3を実装した。`src/core/model_profiles.py`へimmutable profile DTO、strict schema v1、fail-closed load、load前gate、
lookup、atomic Create / Update / Deleteを追加し、`src/core/settings_store.py`へactive profile identity 2種をadditiveに追加した。
`.gitignore`のroot限定`/profiles.json`とB3専用testも追加した。B3専用21件＋31 subtests、関連回帰、full suite 759件＋57 subtests、
`compileall src tests`、`git diff --check`はprocess exit code 0だった。B3はstore / persistenceとして実装・自動検証済みで、manual GUI確認は必須でない。
cross-store resolution、active profile / runtime baseline guard、GUI、実MMD確認はB4 / B5 / MS26へdeferredである。

同日、MS23-B4 Resolution / State / Diagnostics Implementation Planを作成した。B1で採用済みのD1〜D7・S1〜S7を
実装可能なexact contractへ展開し、専用`ModelProfileState`、resolved morph-name set ID付き`GenerationState`、
profile-aware output history、startup fallbackとidentity-only partial INI save、active profile / runtime baseline / referenced presetの
mutation guard、global direct-edit guardを固定した。VMD保存の実経路である`AppController -> src/core/pipeline.py -> writer`、
Previewのanalyzed / empty / clear、diagnostics / reportへ同じresolved output-name tupleを渡し、canonical fingerprint payloadと
`ms21-effective-output-v1`を維持する。計画作成baselineはcore / store / history / rollback 74件＋50 subtests、wx / lifecycle /
diagnostics / pipeline 99件がpass表示・各process exit code 0だった。planning document以外のproduction code、test code、GUI、
runtime user dataは変更していない。B4 production implementationは未開始で、次工程はplanレビューとfresh read-only実装前チェックである。
profile UIはB5、実MMDによるVMD / WAV読み込み・リップ同期確認はMS26へdeferredのままとする。

同日のB4 plan reviewではP1なし、P2 5件、P3 1件を確認した。推奨修正方針を採用し、profile identityを変更するUndo / Redo後の
full INI save、active profile下のhistory初期endpoint、startup identity-only saveと通常full saveの`full > identity_only > none` priority、
mutation guard overlap時のdeterministic error code、resolution DTO / APIのexact field・型・不変条件、store mutation preflightでのlocal immutable
history candidate settleをplanへ追加した。これはB1とMS22の採用済み契約を具体化する文書補正であり、production code、test code、GUI、runtime
user dataは変更していない。修正後planのread-only再チェックとfresh pre-implementation checkは未実施である。

続くfresh read-only再チェックでは、B1 / B3のstrict float・0.0〜10.0契約に対する`ResolvedModelProfile.morph_upper_limit`の型・上限記載不足をP2として確認した。
ユーザー採用の推奨修正として、strict float、有限、0.0〜10.0、bool / int / string拒否をB4 planとBlock Breakdownへ反映した。production code、test code、GUI、runtime
user dataは変更していない。追加修正後のfresh read-only再チェックとB4実装前チェックは未実施である。

2026-08-18にMS23-B4を実装した。専用`ModelProfileState` / resolution DTO、startup identity correction、profile-aware output history、
cross-store mutation guard、active profile中のglobal direct-edit guard、rollback consistency、pipeline / Preview / diagnostics / reportへの
resolved output-name伝播を接続した。B4専用12件、関連回帰52件をprocess exit code 0で確認し、既存日本語default、preset単独Custom、
VMD 30fps、fingerprint schema、runtime user data境界を維持した。full suiteは`771 passed, 57 subtests passed`まで完走したがprocess exit code 1だった。
B4追加wxテストを除外しても`770 passed, 1 deselected, 57 subtests passed`・exit code 1を再現したため、B4追加テスト固有ではない既存wx終了処理系のknown baselineとして記録する。`compileall src tests`と`git diff --check`はprocess exit code 0だった。
MS23-B4のprofile UI手動確認はB5、実MMDによるVMD / WAV読み込み・リップ同期確認はMS26へdeferredのままとする。

同日、MS23-B4後のfull suiteを`-X faulthandler`付きで再調査し、全テスト終了後のGarbage Collection中に`Windows fatal exception: access violation`を確認した。`-k "not wx"`はprocess exit code 0、`-k "wx"`は同じnative exceptionでexit code 1だった。`tests/helpers.py`の`destroy_wx_app()`を使わないlegacy wx testsに、App ownership不明、重複`wx.App()`生成、frame-only teardown、GC依存が残るため、B4機能のP2ではなくtest lifecycle / verification stabilityのP2としてMS23-B4Bへ分離した。B4Bはtest-harness firstで、App / Frame / Controller / timer / pending callbackの終了順を統一し、wx aggregateとfull suiteのprocess exit code 0を目標とする。production code変更、test変更、GUI変更は未開始であり、次工程はB4B fresh read-only pre-checkである。B5 UIとMS26 actual-MMD verificationの境界は変更しない。

B4B plan reviewでP2 4件、P3 1件を確認した。active Appは「同時に複数存在しない」と定義し、teardown後の順次生成を許可した。MS16 / MS21 / MS22のdirect App / Frame teardownを監査対象へ追加し、Controllerのpending saveをtemporary storeへ隔離してroot runtime user dataを保護する契約を追加した。production code変更はB4B内で行わず、必要時は別planまたは明示承認へ戻す。既知再現commandを`.\.venv\Scripts\python.exe -X faulthandler -m pytest -q tests\test_wx_ms14_b1_ui.py tests\test_wx_ms14_b5_export.py`としてplanへ固定した。修正実装、test変更、GUI変更、stage、commitは未実施である。
同日、MS23-B4Bを実装した。tests/helpers.pyとMS14〜MS23の対象wx test teardownを共通契約へ移行し、owned / reused App、Frame identity単位のidempotence、Controller / timer / pending callback、temporary store、teardown済みAppのsingleton解除、native pending-delete処理を固定した。production code、GUI、runtime user dataは変更していない。既知再現10件、wx aggregate 129 passed 2回、non-wx 644 passed＋57 subtests、full suite 773 passed＋57 subtests 2回、B4/B4B専用14件、compileall src testsはprocess exit code 0だった。B4Bの手動GUI確認は不要であり、B5 profile UIとMS26 actual-MMD確認は未完了のまま維持する。B4B変更は`cc23666 Implement MS23-B4B wx teardown repair`としてcommit済みで、pushは未実施である。
同日、MS23-B5 Model Profile UI Implementation Planを作成した。現行RightPane placeholder、MS22-B5 preset UI、MS23-B3 profile store、B4 resolver / state / history / mutation guard、B4B wx teardownをlive codeへ再照合した。B5はstable profile IDによるSelect / Apply分離、profileなしのJapanese default、nullable override / inherit dialog、active profileのRename-only、Controller-side candidate UUID生成、Busy / dirty / stale guard、profile / preset panel cross-syncを所有する。plan reviewではP1なし、P2 2件、P3 2件を確認し、Create初期値をD1準拠のinherit-firstへ補正した。inactive CRUDではcurrent output / active profile identityを不変とし、active mutationは拒否する。created IDはmutation前後のstable ID集合差から取得し、B4 test候補名も実在ファイルへ同期した。B4 resolver、schema、store、fingerprint、writer / Preview / diagnosticsの再実装は行わず、B6 docs closeoutとMS26 actual-MMD確認も先行しない。計画作成baselineは41 passed＋31 subtests、process exit code 0である。B5のproduction code、test code、GUI、runtime user dataは未変更で、次工程はfresh read-only実装前チェックである。
2026-08-19にMS23-B5を実装した。RightPane / MainFrame / AppControllerのprofile UI接続、Select / Apply分離、CRUD、Busy / stale guard、profile / preset cross-syncを接続し、削除確認結果の`wx.ID_YES`比較修正と削除後のリスト再投影を回帰テストへ固定した。連続する同一母音の長音境界も補正し、`long_vowel_mode=decay`でPreview形状計画が失敗する共通経路を解消した。関連回帰31件、全体785件＋57 subtests、`compileall src tests`、`git diff --check`はprocess exit code 0だった。同日、ユーザーから手動GUI確認完了・問題なしの報告を受領した。これはユーザー確認の範囲に限定して記録し、Codex自身のGUI実行結果とは扱わない。旧ユーザーモデルプロファイルのruntime削除とactive profile参照のクリアはlocal data整理として実施し、`presets.json`は変更していない。実MMD確認はMS26へdeferredであり、次工程はMS23-B6である。

2026-08-20にMS23-B6を実装した。B6専用`tests/test_ms23_b6_model_profile_lifecycle.py` 12件を追加し、profile resolution、writer / Preview / diagnostics / reportのresolved morph-name contract、TEXT / voice-only、empty / failure、startup、guard、atomic failure、reset、長音を横断検証した。必須direct testで`UiState.redo_output_edit_state()`のprofile state再投影欠落を再現したため、既存Undo側と同じ投影を`src/gui_wx/ui_state.py`へ最小追加した。B6専用12件、B2〜B5基盤56件＋31 subtests、wx / B4B / B5 / 長音30件、diagnostics / writer / VMD / Preview93件、lifecycle46件＋7 subtests、wx aggregate136件×2、full suite797件＋57 subtests×2、`compileall src tests`、`git diff --check`はprocess exit code 0だった。README、配布用readme、Pipeline / VMD / GUI / Error仕様、Index、Block Breakdownを同期した。2026-08-20にユーザーからprofile Apply後のUndo / Redoを含む限定手動GUI確認通過・問題なしの報告を受領した。これはユーザー確認の範囲に限定して記録し、Codex自身のGUI実行結果とは扱わない。実MMD確認はMS26へdeferred、MS23全体のcloseoutはB7へ残す。

2026-08-20にMS23-B7 Closeout監査を実施した。MS23 direct 82件＋31 subtests、MS21 / MS22関連90件、diagnostics / report / Preview / writer / VMD174件、lifecycle54件＋7 subtests、wx aggregate136件×2、full suite797件＋57 subtests×2、`compileall src tests`、`git diff --check`はすべてprocess exit code 0だった。runtime user data 3 pathのroot限定ignore・Git非追跡、package / dependency / license / network / Qt境界の差分なしを確認した。B2 / B5 / B6のGUI確認はユーザー報告の範囲だけを再利用し、Codex自身のGUI実行とactual-MMD確認は行っていない。P1 / P2 / P3なし、MS23 CloseoutはAと判定し、次工程をMS24 Implementation Plan策定へhandoffする。実MMD確認はMS26へdeferredである。

2026-08-21にMS24-B1 Implementation Planを作成・補正した。source / frozenの`src.core` manifest resource runtime解決、installed packageの`core/whisper_models.json` package-data配置マッピング、検証済みbytes loader、network-unreachable境界を固定した。現行`core/__init__.py`と`src.core.*`の混在importによりinstalled `core.whisper_models` runtime importは成立しないため、B1のinstalled package gateは静的配置確認に限定し、既存アプリ全体のinstalled namespace補修はpackage工程へ分離した。production code、test code、GUI、依存関係、runtime user dataは未変更であり、次工程は補正後のread-only pre-implementation checkである。実MMD確認はMS26、package / release最終判定はMS27へdeferredである。

2026-08-21にMS24-B1を`eafdc16 Implement MS24-B1 Whisper model contract`で実装した。versioned manifest、catalog、verified-local bytes loader、v20250625 version / alignment-head gate、package/spec境界、B1専用testとword / segment fallback回帰を反映した。B2〜B6の実装、Python 3.13互換性確認、GUI、実モデル、実MMD確認は未完了であり、実MMD確認はMS26、package / release最終判定はMS27へdeferredである。

2026-08-22にMS24-B2 Implementation Planを作成し、P2として確認されたownership permit契約、canonical `.part` cleanup、artifact statusとfailure codeの写像、B2/B3/B4/B5責務、preflight順序を補正した。B2はユーザー確認後かつdownload開始前のlocal-only preflight、atomic promote、B5発行permitの検証を所有し、B4はforeground download orchestration、B5はownership解除とpermit発行を所有する。Block Breakdown、B1 plan、Indexも同期した。次工程は補正後MS24-B2 planのread-only pre-implementation recheckである。

同日、メインエージェントでMS24-B2 Implementation Planを再チェックし、caller-supplied promote path、permit issuerの実装境界、root reparse/junctionのlocal-only境界をP2として、B2 failure codeのB4/B5/B6 handoffをP3として確認した。promoteはmodel keyから解決したcanonical `.part`だけを扱い、permitはB5専用issuer boundaryのopaque capabilityとし、保存先rootと既存親要素のreparse/junction/network redirectを拒否する契約へ補正した。failure codeは上位failure classへ投影した後もdiagnostic detailとして保持する。P1 / P2 / P3の残存はなく、production code、test code、GUI、依存関係、runtime user dataは変更していない。次工程はMS24-B2実装前チェックである。

2026-08-22にMS24-B2を実装し、`b011b37 Implement MS24-B2 model storage core`へ記録した。`whisper_models_dir`のlocal-only解決、availability、canonical `.part`、preflight、atomic promote、B5発行permitの検証付きdeleteを実装し、B3のselected / active identity、B4のHTTP / worker、B5のloaded ownership / cacheは先行実装していない。2026-08-23のtargeted baselineではB2 / B1 / SettingsStore関連40件がpassed、2件がWindows symlink capability依存でskippedとなった。B2はUI非依存Blockとして扱い、手動GUI、実ネットワーク、実モデル、実MMD確認は実施していない。

同日、MS24-B3 Implementation Planを作成し、main-agent recheckで確認されたP2（canonical identity fieldの対応、B2実装済み状態とrouting文書の不一致）を計画書へ反映した。Index、Block Breakdown、MS24-B2 plan、Roadmapの現行状態をB2実装済み・B3 plan作成済みへ同期した。B3のproduction code、test code、GUI、依存関係、runtime user dataは未変更で、次工程はMS24-B3のfresh read-only pre-implementation checkである。実MMD確認はMS26、package / release最終判定はMS27へdeferredである。

2026-08-23のMS24-B3実装前再チェックで、B2の`WhisperModelStore.scan_all()`がモデルartifact全体のSHA256を読むため、`AppController.load_startup_state()`から同期実行すると起動UIを長時間停止させ得るP2を確認した。ユーザー採用方針に基づき、B3 planへ初期`availability_scan_status=pending`の即時投影、B3専用read-only availability scan worker、job ID / panel revision / shutdown guard、late result破棄、scan failureのfail-closed表示を追加した。B3 workerはnetwork、Whisper loader、model load、analysis、directory作成を行わず、既存AudioWorkerとB4 download workerを使用しない。Block Breakdown、Index、Roadmapもこの境界へ同期した。今回もproduction code、test code、GUI、依存関係、runtime user dataは変更しておらず、次工程は補正後MS24-B3のfresh read-only pre-implementation checkである。実MMD確認はMS26、package / release最終判定はMS27へdeferredである。

続くP2/P3解消として、MS24-B3 planと関連routing文書を再補正した。候補選択で変化する`panel_revision`とavailability scan専用の`availability_scan_generation`を分離し、pending中の候補選択がjob IDとscan generationの一致する正当なscan結果を破棄しない契約を追加した。さらに、`availability_scan_failure_code` / `availability_scan_failure_detail`を失敗情報の正本fieldとして固定し、availability workerをdaemon、close時のjob失効、UIスレッドからのjoin禁止、late callbackのno-opとして明文化した。今回もproduction code、test code、GUI、依存関係、runtime user dataは未変更であり、次工程は補正後MS24-B3のfresh read-only pre-implementation checkである。

その後のMS24-B3実装前チェックで、temporary SettingsStore pathだけではB2の既定`models` rootが隔離されず、B3のstartup / availability testがrepositoryのruntime model dataを読む可能性があるP2を確認した。B3 plan、Block Breakdown、Index、Roadmapへ、temporaryな`whisper_models_dir`またはtemporary B2 store/rootの明示注入、repository既定の`models` rootとroot runtime user dataを読まないassertを追加した。production code、test code、GUI、依存関係、runtime user dataは未変更であり、次工程は補正後MS24-B3のfresh read-only pre-implementation checkである。

続くMS24-B3実装前チェックで、明示設定されたrelative / UNC / remote / device pathの`StorageRootResolution`失敗時に、既定`models`へのfallback、store構築、availability worker起動、root作成を禁止するstartup契約が不足しているP2を確認した。B3 planとBlock Breakdownへ、B2 failure code / detailを`availability_scan_status=failed`へ投影し、selected / active identityを保持する契約と専用回帰を追加した。また、関連回帰一覧から漏れていた`tests/test_whisper_timing.py`と`tests/test_ms19_b3_textless_pipeline.py`を追加した。production code、test code、GUI、依存関係、runtime user dataは未変更であり、次工程は補正後MS24-B3のfresh read-only pre-implementation checkである。

その後のMS24-B3実装前再チェックで、B2 `StorageRootResolution`のfield名をB3 planが`failure_detail`と誤記していたP2と、B2 `message`由来のraw technical detailを通常UIへ表示し得るP2を確認した。B3 plan、Block Breakdown、Index、Roadmapを再補正し、B2の正本を`failure_code` / `message`へ統一した。B3はfailure codeから安全なユーザー向け通知を生成し、message由来のraw例外・絶対パスは通常UIへ表示せず、診断・handoff用detailへ限定する。未知のfailure codeはgeneric通知へfail closedし、raw detail非表示の回帰を受け入れ条件へ追加した。production code、test code、GUI、依存関係、runtime user dataは変更していない。次工程は補正後MS24-B3のfresh read-only pre-implementation checkである。

2026-08-23にMS24-B3を実装した。`SettingsStore`のselected / active identity、`UiState`のWhisper selection state、RightPane専用Whisperモデルtab、startup projection、local-only availability scan worker、Busy / stale / shutdown guard、safe failure noticeを追加した。B3追加・関連の限定検証、full suite `846 passed, 2 skipped`、`compileall src tests`、`git diff --check`はprocess exit code `0`で完了した。ユーザーから、起動時表示、候補選択とactive分離、selection-only no-op、availability、theme、Busy / stale、workspace reset、既存tab、scan中closeを含む手動GUI確認が完了し問題なしとの報告を受領した。これはユーザー確認の範囲に限定して記録し、Codex自身のGUI実行結果とは扱わない。実network、実model、実Whisper解析、実MMD確認は未実施で、B4、B5、MS26へ引き継ぐ。現在はworking tree状態で、stage / commit / push / merge / tag / releaseは未実施である。次工程はMS24-B4 Implementation Plan策定である。
2026-08-23にMS24-B4 Implementation Planを作成し、再チェックで確認したP2/P3を補正した。保存先変更は`whisper_models_dir`だけを渡すpartial saveを禁止し、現在の全設定を保持する安全なmerge保存と、theme、window、recent path、selected / active identityの回帰を計画へ追加した。B2内部の対象model verification scanと、controllerの再利用可能な`start_whisper_availability_rescan()`による全体availability projectionを分離した。B3は`a27a26f`でコミット済み、B4 planは作成済みで、次工程はfresh read-only pre-implementation checkである。production code、test code、GUI実装、依存関係、runtime user dataは変更していない。実MMD確認はMS26、package / release最終判定はMS27へdeferredである。

2026-08-24にMS24-B4をworking treeへ実装した。公式manifest URL限定downloader、Content-Length / exact size / redirect / short read / overrun / cancel / cleanupのfail-closed処理、専用management worker、Download & Verify / Cancel / Delete / 保存先変更UI、SettingsStore managed merge、再利用可能な`start_whisper_availability_rescan()`を接続した。B5 permit未接続時のDeleteはblockedとし、active / loaded / analysis identityはB4から変更しない。全pytestは`860 passed, 2 skipped, 77 subtests passed`、`compileall src tests`、`git diff --check`はprocess exit code `0`で完了した。ユーザーから手動GUI確認完了・問題なしの報告を受領したが、これはCodex自身のGUI実行結果とは扱わない。Python 3.13.x互換性確認、B5実production Delete、実MMD確認は未完了で、package / release最終判定はMS27へdeferredである。stage / commit / push / merge / tag / releaseは未実施である。

続くMS24-B4実装プラン再チェックでは、現行`SettingsStore`が`system` themeを`dark`へ正規化するため、全設定保持・System/Light/Dark保持のP2が残っていることを確認した。runtime INIの直接編集禁止とSettingsStore managed persistenceの境界も明記し、`src/core/settings_store.py` / `tests/test_settings_store.py`のtheme round-trip・managed merge回帰をB4対象へ追加した。promote後の全体availability projectionはcontrollerの再利用可能な`start_whisper_availability_rescan()`だけを入口とし、Python 3.13.xの実行ファイルpath・version・process exit codeをcompatibility gateとして記録する。production code、test code、GUI、依存関係、runtime user dataは変更していない。次工程は補正後MS24-B4 planのfresh read-only pre-implementation checkである。

2026-08-25にMS24-B5をworking treeへ実装した。verified-local model request、single-active runtime、Apply / candidate commit-reject、TEXT + 音声・voice-onlyのmodel identity伝播、model-aware rollback、B5 production ownership permit、delete / storage root change / shutdown lifecycleを接続した。解析時の暗黙downloadを禁止し、word timestamp / segment fallbackとMS23の固定morph・Latin profile・preset・diagnostics・fingerprint契約を維持した。B5専用・関連回帰を含む全pytestは`872 passed, 2 skipped`、`compileall -q src`、`git diff --check`はprocess exit code `0`だった。ユーザーからB5手動GUI確認完了・問題なしの報告を受領したが、これはCodex自身のGUI実行結果とは扱わない。Python 3.13.x互換性確認、実MMD確認、MS27 package / release readinessは未確認または別工程である。stage / commit / push / merge / tag / releaseは未実施である。次工程はB5のPython 3.13.x compatibility gate確認後、MS24-B6 Implementation Planへ進む。

2026-08-26にMS24-B6を実装した。`WhisperDiagnosticsSummary`、selected / active / loaded / analysis identityの分離、package version / gate status、safe failure分類、projection generation、Info / report / RightPaneの同一snapshot投影、model-aware rollbackの診断連携を追加した。MS23の固定morph・Latin profile・preset・diagnostics・fingerprint契約、暗黙download禁止、依存値、runtime user data境界は維持した。B6専用・MS20 diagnostics / save policy回帰を含む全pytestは`881 passed, 2 skipped`、`compileall -q src tests`、`git diff --check`はprocess exit code `0`だった。ユーザーからB6手動GUI確認通過・問題なしの報告を受領したが、これはCodex自身のGUI実行結果とは扱わない。Python 3.13.x互換性確認は未実施、実MMD確認はMS26、MS27 package / release readinessはMS27へdeferredである。B6のproduction code・test code変更は`1f1aff2 Implement MS24-B6 diagnostics and recovery`としてcommit済みで、B6のstage / commitは完了している。MS24-B7 Implementation Planは作成済みだが、B7実施・Closeout判定は未着手である。

2026-08-28にMS24-B7 Implementation PlanをP2/P3レビュー結果に基づき補正した。MS23-B2〜B6の直接回帰、保持すべきtiming経路、pipeline / VMD / MMD用WAVの既存回帰対象を具体的なtest fileとして明記し、B2 `VerifiedWhisperCheckpoint` DTOとloader自身の同一open handle再検証・検証済みbytes束縛の責務境界を補正した。また、`pyproject.toml`の`requires-python >=3.11` metadata floorとMS24のPython 3.13.x compatibility gateを分離して記録した。

同日、MS24-B7のintegration regressionとstatic package auditを実施した。MS24直接回帰は`76 passed, 2 skipped`、MS23 direct・MS19 voice-only・MS20 diagnostics・MS21 rollback / pipeline・pipeline / VMD・MS17 MMD用WAV回帰は`163 passed`、現行HEADの全pytestは`881 passed, 2 skipped`で、いずれもprocess exit code `0`だった。`compileall -q src tests`と`git diff --check`もexit code `0`である。`collect_data_files("whisper")`は4件のpackage assetsだけを列挙しmodel weightsを含まず、tracked fileにも`*.pt`、`*.bin`、`*.part`、`models/`の該当ファイルはなかった。README、配布用readme、Release Package Manifest、THIRD_PARTY_LICENSESをMS24のモデル取得・検証・非同梱境界へ同期した。ユーザー判断によりPython 3.14.3をMS24の開発・受入環境として採用し、3.14.3 compatibility gateを合格とした。Python 3.11 / 3.12は今回の受入対象外で、互換性を検証済みとは扱わない。MS24 Closeout判定は未実施である。production code、test code、GUI、依存関係、runtime user dataは変更していない。実MMD確認はMS26、onefile / ZIP / PySide6最終artifact・release readinessはMS27へdeferredである。

2026-08-28にMS24 Closeout Aを判定した。B7-F-002のP3表記を`P3（解消）`へ補正し、B7-F-001 / B7-F-002とも解消済みとして記録した。P1 / P2はなく、MS24-B1〜B6の実装・自動検証・ユーザー手動GUI確認、B7 integration regression、Python 3.14.3 development / acceptance gate、package静的監査、文書同期を照合して合格とした。Python 3.11 / 3.12は今回の受入対象外として未検証扱いを維持する。実MMD確認はMS26、onefile / ZIP / PySide6最終artifact・package / release readinessはMS27へ引き継ぐ。

2026-09-03にMS25-B5をworking treeへ実装した。一括出力menu、destination dialog、delivery専用worker、Busy / cancel / close lifecycle、pre-commit UI bridgeを接続し、false `delivery_busy` を起こすworker state / reference不整合をP3修正した。B5および関連worker / GUI回帰は`29 passed`、全pytestは`1015 passed, 4 skipped`でprocess exit code `0`、`compileall -q src tests`と`git diff --check`もexit code `0`だった。ユーザーから提示したB5手動GUIテスト通過の報告を受領したが、これはユーザー確認の範囲に限定して記録し、Codex自身のGUI実行結果とは扱わない。B6 fault matrix、B7 full cross-boundary regression / closeout、実MMD確認は未完了で、Python 3.11 / 3.12とMS27 package / release readinessは未検証・deferredである。stage / commit / push / merge / tag / releaseは未実施である。
2026-09-04にMS25-B6をworking treeへ実装した。staging identity再確認、OS fault分類、collision優先のno-clobber commit、cleanup failureのterminal化、delivery close状態のreconciliationを反映した。B6専用testは`26 passed`、B6直接回帰は`134 passed, 2 skipped`、指定cross-boundary回帰は`94 passed`、全pytestは`1041 passed, 4 skipped`で、いずれもprocess exit code `0`である。Windows実filesystemのjunction collisionとsharing violationはskipなしで通過した。ユーザーから提示したB6手動GUI確認通過・問題なしの報告を受領したが、これはユーザー確認の範囲に限定して記録し、Codex自身のGUI実行結果とは扱わない。B6のstage / commit、B7のfull regression / closeout、README等の最終同期、実MMD確認、MS27 package / release readinessは未実施または後続である。
