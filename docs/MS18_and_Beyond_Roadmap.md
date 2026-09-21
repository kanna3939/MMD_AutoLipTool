# MS18 and Beyond Roadmap

> [!WARNING]
> **Legacy / Historical Document**
> 本書のMS18・MS19の完了記録は有効な履歴である。MS20以降の番号と計画は [MS20 and Beyond Roadmap](MS20_and_Beyond_Roadmap.md) と [MS20 and Beyond Index](MS20_and_Beyond_Index.md) を使用し、本書の旧番号と完了記録は置換しない。

## 1. 文書情報

- 文書名: MS18 and Beyond Roadmap
- 想定配置先: `docs/MS18_and_Beyond_Roadmap.md`
- 対象リポジトリ: `MMD_AutoLipTool-dev`
- 基準ブランチ: `main`
- 基準状態:
  - MS17-B9 closeout 完了
  - MS17 closeout 後追補として `cache/` の Git 追跡対象外化完了
  - MS18-B1 Repo / Release Readiness / Risk Inventory 完了
  - MS18-B2 Security Preflight Review 完了
  - MS18-B3 Refactor Scope Definition 完了
  - MS18-B4 Safe Refactor Implementation 完了
  - MS18-B5 SmokeLaunch / Process Residual Investigation 完了
  - MS18-B6 Release / Packaging / License Preflight 完了。package化前P2はユーザー判断によりクリア
  - MS18-B7 Actual MMD Manual Verification Closeout 完了。ユーザー確認通過・問題なし
  - MS18 CloseOut 完了
  - `feature/MS17` ではなく `main / origin/main` を正本として扱う
- 作成日: 2026-06-03
- 文書ステータス: Draft
- 旧文書扱い:
  - `docs/Ver0_4_Expansion_Roadmap_for_Antigravity.md` は、MS18以降の正本ロードマップとしては扱わない
  - 旧文書は Ver0.4 初期計画の履歴資料としてのみ参照する
  - 新規作業では、本書を MS18以降のロードマップ正本候補として扱う

## 2. 文書目的

本書は、MS17 closeout 後の `MMD_AutoLipTool` 開発方針を整理し、MS18以降の作業順序・責務境界・実装対象・非対象を明確化するためのロードマップ文書である。

MS17では、wxPython 主系への移行後に、wav / mp3 / m4a 入力、解析用WAV生成、MMD用WAV出力、音声処理 worker 化、Busy制御、キャンセル導線、統合テスト、README / 配布関連文書同期まで完了した。

MS18以降では、すぐに新機能追加へ進むのではなく、まずリリース前の安定化・処理効率化・セキュリティ確認・配布前確認を行う。その後、MS19で音声のみ入力対応、MS20で既存リップモーフ範囲内の発音イベント単位編集へ進む。

## 3. 現在地

### 3.1 MS17までに完了している主な範囲

MS17 closeout 時点で、以下は実装済みとして扱う。

- wxPython 版 GUI 主系
- TEXT 読み込み
- 音声ファイル読み込み
  - wav
  - mp3
  - m4a
- ffprobe による音声検査
- ffmpeg による解析用WAV生成
- 解析用WAVを用いた波形表示・Preview・解析処理
- MMD用WAV出力
  - 専用ボタンからの出力
  - `pcm_s16le / 44100 Hz / stereo` 方針
  - `-bitexact` による単純 chunk 構造寄せ
  - 上書き確認
  - 失敗時 cleanup
- 音声処理 worker 化
- Busy 状態制御
- 音声処理キャンセル導線
- 300秒超過時の長時間処理確認
- late callback 破棄
- README / NOTICE / THIRD_PARTY_LICENSES.md / Release_Package_Manifest の MS17 状態同期
- `cache/` の Git 追跡対象外化

### 3.2 MS17 closeout 後に残っている確認事項

MS18開始時点で扱うべき残課題は以下とする。

- 実MMDでの MMD用WAV 読み込み・再生確認
- `build.ps1 -SmokeLaunch` の PyInstaller プロセス残留原因調査
- FFmpeg 同梱配布時の第三者ライセンス通知確定
- Release package に含めるもの / 含めないものの確定
- 配布前に不要な開発用ファイルが混入しないことの確認
- Windows 11 上でのリリース前動作確認
- 実行ファイル配布時の安全性・説明不足・復旧しやすさの確認

2026-07-03時点では、MS18-B4からMS18-B7まで完了し、MS18はCloseOut済みである。
SmokeLaunch / Process Residual Investigation はMS18-B5で完了した。
Release / Packaging / License Preflight はMS18-B6で完了した。B6で記録したFFmpeg実体のGit追跡とSource code archive同梱、FFmpeg license texts未確定、PyInstaller xref上のPySide6参照は、2026-07-03のユーザー判断によりクリア扱いとした。
実MMD確認はMS18-B7で完了し、ユーザー確認通過・問題なしとして記録済みである。

## 4. MS18以降の基本方針

### 4.1 作業順序

MS18以降は、以下の順に進める。

1. MS18: Release Readiness / Refactor / Security Hardening
2. MS19: Voice-only Input
3. MS20: Per-Event Lip Morph Editing
4. MS21以降: 品質改善・多言語対応・配布改善などの追加検討

### 4.2 MS18の位置づけ

MS18は、新機能追加マイルストーンではない。

MS18は、リリース / package 化の前に、現在の MS17 実装を公開可能な状態へ近づけるための安定化マイルストーンである。

MS18では、次を主対象とする。

- リリース前確認
- セキュリティチェック
- 処理効率化
- 重複コード整理
- 挙動非変更の安全なリファクタリング
- 配布前ライセンス確認
- SmokeLaunch / PyInstaller プロセス残留調査
- 実MMD確認
- package 化前の最終棚卸し

MS18では、次を主対象にしない。

- 音声のみ入力対応
- モーフ編集機能
- VMD writer の全面再設計
- pipeline の意味論変更
- Preview / waveform の仕様変更
- 音声解析品質の大幅変更
- 任意モーフ対応
- 英語対応
- 新しい配布方式の大規模導入

### 4.3 MS19の位置づけ

MS19は、TEXT 必須前提を外し、音声のみ入力から最低限の VMD 生成を成立させるマイルストーンである。

MS19では、音声からの書き起こし、日本語読み生成、母音列変換、既存 pipeline 接続、GUI導線、エラー処理、Preview / VMD 保存までを段階的に扱う。

### 4.4 MS20の位置づけ

MS20は、既存の `あ / い / う / え / お` リップモーフ範囲内で、発音イベント単位の編集機能を追加するマイルストーンである。

MS20で扱う「モーフ編集機能」は、任意モーフ編集ではない。

MS20では、既存のリップ生成結果に対して、イベント単位で開口量・閉口・スロープ・保持時間などを調整できる方向を検討する。

## 5. MS18: Release Readiness / Refactor / Security Hardening

### 5.1 目的

MS18の目的は、MS17 closeout 後の実装を、リリース / package 化に進められる状態へ安定化することである。

特に、次を重視する。

- リリース前に残課題を棚卸しする
- セキュリティ上の弱点を確認する
- 重複コードや非効率な処理を整理する
- 挙動非変更の範囲で安全にリファクタリングする
- 配布物とライセンス通知を確認する
- 実MMDでの確認を完了させる
- package 化前の判定材料を揃える

### 5.2 MS18で許可するリファクタリング

MS18で許可するリファクタリングは、次に限定する。

- 重複コードの整理
- 明確に無駄な処理の削減
- 例外処理の整理
- エラー分類の整理
- subprocess / ffmpeg / ffprobe 実行まわりの安全性確認と必要最小限の改善
- temp / cache / 出力ファイル処理の安全化
- パス処理の整理
- 配布前に問題になりやすい同梱物処理の確認
- テストしやすさを高めるための小規模な責務分離
- コメントやドキュメントの実装状態同期

### 5.3 MS18で避けるリファクタリング

MS18では、次を避ける。

- pipeline の意味論変更
- VMD writer の再設計
- GUI 状態遷移の大幅変更
- Preview / waveform の仕様変更
- 音声解析アルゴリズムの品質変更
- Whisper / pyopenjtalk 周辺の機能追加
- 設定ファイル schema の大幅変更
- 任意モーフ編集に向けた先行実装
- 音声のみ入力対応の先行実装
- 英語対応の先行実装
- 大規模ディレクトリ再編

### 5.4 MS18 Block 構成

MS18は、以下の Block に分割する。

```text
MS18-B1: Repo / Release Readiness / Risk Inventory
MS18-B2: Security Preflight Review
MS18-B3: Refactor Scope Definition
MS18-B4: Safe Refactor Implementation
MS18-B5: SmokeLaunch / Process Residual Investigation
MS18-B6: Release / Packaging / License Preflight
MS18-B7: Actual MMD Manual Verification Closeout
```

### 5.5 MS18-B1: Repo / Release Readiness / Risk Inventory

#### ステータス

完了。

2026-06-28 に `feature/MS18` 上で repo 状態確認、`main / origin/main` 同期確認、MS17 closeout反映確認、`cache/` 追跡対象外化確認、配布関連文書確認、release readiness risk inventory を実施した。

P1は検出していない。B1時点のP2として、Security Preflight未実施、SmokeLaunch残留原因未確定、FFmpeg license notice最終確認未完了、実MMD確認未完了を後続Blockへ引き継いだ。Security Preflight未実施はMS18-B2で解消済み。

#### 目的

MS18開始時点の `main / origin/main` を正本として、リリース前に確認・修正・保留すべき項目を棚卸しする。

#### In Scope

* `main / origin/main` の同期確認
* `feature/MS17` など古いブランチを見ていないことの確認
* MS17 closeout 反映確認
* `cache/` の Git 追跡対象外化確認
* README / NOTICE / THIRD_PARTY_LICENSES.md / Release_Package_Manifest の同期状態確認
* MS18で扱うリスクの分類
* MS18内で修正するもの / MS19以降へ回すもの / リリース前手動確認へ回すものの分類

#### Out of Scope

* コード変更
* ドキュメント変更
* packaging 実作業
* 新機能実装
* リファクタリング実装

#### 完了条件

* MS18開始時点の正本状態が確認されている
* リリース前リスク一覧が作成されている
* MS18-B2以降の作業対象が明確になっている

### 5.6 MS18-B2: Security Preflight Review

#### ステータス

完了。

2026-06-28 に `feature/MS18` 上で、外部ファイル入力、ffprobe / ffmpeg 実行経路、subprocess引数、shell injection相当リスク、FFmpeg / ffprobe探索順、自動ダウンロード禁止、temp / cache / 出力ファイル処理、GUI worker / Busy状態、PyInstaller onefile、エラーメッセージ / 情報露出、FFmpeg license / release readinessを確認した。

Security PreflightとしてP1は検出していない。対象テスト42件は通過した。P2として、FFmpeg / ffprobe同梱配布時のlicense texts / notice最終確定、`build.ps1 -SmokeLaunch` のPyInstallerプロセス残留原因未確定、実MMD確認未完了を後続Blockへ引き継いだ。P3として、PATH fallback時の説明改善、`error.log` / 開発コンソールのローカル診断情報、cacheファイル名のstem、`build.ps1 -Clean` の旧onefile成果物明示削除なしを記録した。

#### 目的

リリース / package 化前に、ローカルWindowsアプリとして最低限確認すべきセキュリティ観点を洗い出す。

#### In Scope

* 外部ファイル読み込みの安全性確認
* wav / mp3 / m4a 入力時の制限値確認
* ffprobe / ffmpeg 実行時の引数組み立て確認
* shell injection 相当の危険がないことの確認
* subprocess 実行経路の確認
* temp / cache / 出力ファイルの扱い確認
* 上書き確認・失敗時 cleanup の確認
* PyInstaller onefile 展開先・同梱物の扱い確認
* ログやエラーメッセージに不要な個人情報・ローカルパスを出しすぎていないかの確認
* 自動ダウンロードを行っていないことの確認
* FFmpeg / ffprobe が想定外のパスから実行されないかの確認

#### Out of Scope

* 暗号化機能の追加
* ネットワーク通信機能の追加
* サンドボックス化
* 外部セキュリティ監査
* 大規模な依存関係入れ替え

#### 完了条件

* セキュリティ観点の確認結果が P1 / P2 / P3 で分類されている
* MS18内で修正すべき項目が明確になっている
* 修正不要または将来課題に回す項目が明確になっている

### 5.7 MS18-B3: Refactor Scope Definition

#### ステータス

完了。

2026-06-29 に `feature/MS18` 上で、MS18-B2のP2/P3をMS18-B4で扱う項目・扱わない項目へ分類した。B2でP1は検出されておらず、B4へ必須投入すべきP2もない。

B4で扱ってよい候補は、PATH fallback時の探索元説明性改善、および `error.log` / 開発コンソールの診断情報扱いの小規模整理に限定した。`build.ps1 -SmokeLaunch` と `build.ps1 -Clean` はMS18-B5、FFmpeg license / package確認とcache配布除外確認はMS18-B6、実MMD確認はMS18-B7へ送る。

#### 目的

MS18で実施するリファクタリング範囲を、挙動非変更・処理効率化・安全性向上に限定して定義する。

#### In Scope

* 重複コードの確認
* ffmpeg / ffprobe runner 周辺の責務確認
* 音声処理 worker 周辺の責務確認
* GUI controller 内の肥大化箇所確認
* 例外処理・エラー分類の重複確認
* temp / cache / 出力ファイル処理の重複確認
* テスト対象の確認
* 変更対象ファイルの限定

#### Out of Scope

* 実装変更
* 大規模再設計
* 新機能追加
* GUI レイアウト刷新
* VMD writer 再設計
* pipeline の契約変更

#### 完了条件

* MS18-B4で実装するリファクタリング対象が確定している
* 変更禁止範囲が明記されている
* テスト方針が定義されている

### 5.8 MS18-B4: Safe Refactor Implementation

#### ステータス

完了。

2026-06-30 に `feature/MS18` 上で、FFmpeg / ffprobe探索結果の説明補助、未検出時メッセージへの探索元説明反映、解析用WAV再生時のMCI向け短い一時ファイル名経由再生を実施した。

探索順、PATH fallback可否、自動ダウンロード禁止方針、GUI状態遷移、worker起動順は変更していない。
対象テストは通過し、ユーザーテスト通過が報告された。

#### 目的

MS18-B3で確定した範囲に限定して、挙動非変更の安全なリファクタリングを実施する。

#### In Scope

* MS18-B3で許可された範囲のみ
* PATH fallback時の探索元説明性改善
* `error.log` / 開発コンソールの診断情報扱いの小規模整理
* 上記に直接必要な限定テスト追加・更新
* B4実施内容に直接関係する履歴文書同期

#### Out of Scope

* MS18-B3で定義していない変更
* `build.ps1` / SmokeLaunch / Clean手順変更
* FFmpeg license / package manifest / release package同梱物確定
* cache命名規則変更
* pipeline の意味論変更
* VMD 出力仕様変更
* GUI 操作仕様変更
* 新機能追加
* 音声のみ入力対応
* モーフ編集機能

#### 完了条件

* 既存主要テストが通過している
* MS17の既存機能が維持されている
* 差分が MS18-B3 の定義範囲内に収まっている
* リファクタリングによる挙動変更がないことを説明できる

### 5.9 MS18-B5: SmokeLaunch / Process Residual Investigation

#### ステータス

完了。

2026-07-01 に `feature/MS18` 上で、`build.ps1 -SmokeLaunch` の停止待機・残留確認と `build.ps1 -Clean` 時の旧onefile成果物削除を実施した。

SmokeLaunchでは起動前の同一exeパス既存PIDを記録し、B5で起動した対象のみ停止・確認するようにした。
停止後は最大30秒まで対象PIDの終了を待機する。
`build.ps1 -Clean -SmokeLaunch` と通常 `build.ps1` は通過し、ユーザーテスト通過が報告された。

#### 目的

`build.ps1 -SmokeLaunch` における PyInstaller プロセス残留・タイムアウト原因を調査し、リリース前に許容できる状態へ整理する。

#### In Scope

* `build.ps1 -SmokeLaunch` の現行処理確認
* PyInstaller 実行後のプロセス状態確認
* 生成済み exe の起動スモーク確認
* `Stop-Process` 後の残留確認
* タイムアウト原因の切り分け
* build script 側での必要最小限の修正検討
* リリース前確認手順への反映

#### Out of Scope

* build system の全面置き換え
* installer 導入
* CI/CD workflow の大規模追加
* PyInstaller 以外の配布方式への移行

#### 完了条件

* SmokeLaunch の残留原因が説明されている
* 修正する場合は最小差分で修正されている
* 修正しない場合は、リリース前手順上の扱いが明記されている
* package 化前に実施すべき起動確認手順が整理されている

### 5.10 MS18-B6: Release / Packaging / License Preflight

#### ステータス

完了。

2026-07-02 に `feature/MS18` 上で、実行用ZIP / GitHub generated Source code archive / FFmpeg license notice / PyInstaller依存関係 / sample同梱方針を確認した。

`FFmpeg\bin\` 配下の実体ファイルがGit追跡対象であり、GitHub自動生成 Source code ZIP / tar.gzにもFFmpegバイナリが含まれる前提でlicense notice確認が必要である。
FFmpeg buildは `--enable-gpl --enable-version3` を含むが、個別のFFmpeg license text / COPYING相当ファイルはリポジトリ内で確認できていない。
PyInstaller xref上の `PySide6` 参照は、Qt / PySide GUI復活ではなく、配布内容・依存関係・license notice確認項目として扱う。
`sample/` は出典・ライセンス・用途説明が確定できるまで実行用ZIPから除外する。

2026-07-03 のMS18 CloseOut時点で、上記のpackage化前P2はユーザー判断によりクリア扱いとした。`sample/` は実行用ZIPから除外する方針を維持する。

#### 目的

実行用ZIPまたはGitHub Release向け配布物を作成する前に、同梱物・除外物・ライセンス通知・FFmpeg配布条件を確認する。

#### In Scope

* `README.md` の配布前同期確認
* `readme_mmdautolip.txt` の配布前同期確認
* `LICENSE` の存在確認
* `NOTICE` の内容確認
* `THIRD_PARTY_LICENSES.md` の内容確認
* `docs/Release_Package_Manifest.md` の内容確認
* FFmpeg / ffprobe の version / build configuration 確認
* `--enable-gpl --enable-version3` を含む build への第三者ライセンス通知確認
* 実行用ZIPに含めるもの / 含めないものの確認
* `cache/`、`build/`、`src/`、`tests/`、`.venv/` などが配布ZIPへ混入しないことの確認
* GitHub Release 本文の最低限の記載方針整理

#### Out of Scope

* 実際の公開
* GitHub Release 作成
* installer 作成
* FFmpeg build の変更
* ライセンス解釈の法的断定

#### 完了条件

* 配布前チェックリストが更新されている
* 同梱必須ファイルが明確になっている
* 除外対象が明確になっている
* FFmpeg ライセンス通知の未確定点が解消または明示されている
* package 化に進めるかどうかの判定が可能になっている

### 5.11 MS18-B7: Actual MMD Manual Verification Closeout

#### ステータス

完了。

`docs/Implementation_Plan/MS18-B7_Implementation_Plan.md` に、実MMDでのVMD / MMD用WAV読み込み・再生・リップ同期目視確認、ユーザー手動確認結果の記録、MS18 closeout判定、B6 package化前P2との分離方針を整理した。
2026-07-03 に、実MMDでのユーザー確認通過・問題なしが報告された。B7内でREADME / readme追加修正が必要な問題は報告されていない。

#### 目的

リリース前確認として、実際の MikuMikuDance 上で MMD用WAV と VMD の読み込み・再生確認を行い、MS18を closeout する。

#### In Scope

* 実MMDでの VMD 読み込み確認
* 実MMDでの MMD用WAV 読み込み確認
* 音声再生確認
* リップモーション同期の目視確認
* 生成ファイルの配置手順確認
* ユーザー向け説明への反映要否確認
* MS18 closeout 記録

#### Out of Scope

* MMD本体の不具合調査
* モデル固有のモーフ差異対応
* VMD writer の品質改善
* 音声のみ入力対応
* モーフ編集機能

#### 完了条件

* 実MMD確認結果が記録されている
* リリース前に残す課題が明確になっている
* MS18 closeout 判定が記録されている
* MS19へ進める状態か判断できる

## 6. MS19: Voice-only Input

### 6.1 目的

MS19の目的は、TEXT 必須前提を外し、音声ファイルのみから最低限の VMD 生成を成立させることである。

MS17時点では、TEXT 1件と音声ファイル 1件を入力する前提である。MS19では、音声のみ入力時に書き起こし・日本語読み生成・母音列変換を行い、既存 pipeline へ接続する。

### 6.2 In Scope

* 音声のみ入力モードの仕様定義
* TEXT あり / TEXT なしの状態分岐
* 音声からの書き起こし導線
* 書き起こし結果の確認・編集方針検討
* 日本語読み生成
* 母音列変換
* 既存 timing pipeline への接続
* Preview / waveform / VMD保存との整合
* エラー処理
* GUI導線
* テスト追加
* README / docs 同期

### 6.3 Out of Scope

* 英語対応
* 多言語対応
* 任意モーフ対応
* モーフ編集機能
* Whisper model 管理の大規模UI
* クラウドAPI依存
* 自動ダウンロード
* VMD writer の全面再設計

### 6.4 想定Block構成

MS19は、以下のような Block に分割する想定とする。

```text
MS19-B1: Voice-only Input Requirements / State Contract
MS19-B2: Transcription Pipeline Pre-check
MS19-B3: Textless Pipeline Integration Foundation
MS19-B4: GUI Entry Point and State Handling
MS19-B5: Review / Edit Transcription Result Flow
MS19-B6: VMD / Preview / Save Integration
MS19-B7: Error Handling / Tests / Docs
MS19-B8: Workspace Reset / New Session Flow
MS19-B9: MS19 Closeout
```

### 6.5 MS19の受け入れ条件

MS19の完了条件は以下とする。

* TEXTなしで音声ファイルのみを読み込める
* 書き起こし結果から日本語読み・母音列を生成できる
* 既存 pipeline へ接続できる
* Preview / waveform 上で確認できる
* VMD 保存できる
* TEXTあり入力の既存導線が壊れていない
* 音声のみ入力時のエラーがユーザーに分かる形で通知される
* README / docs に TEXTあり / TEXTなしの違いが説明されている
* 現在の作業を初期化し、設定・履歴を保持したまま次のTEXTあり / 音声のみ作業へ移れる

## 7. MS20: Per-Event Lip Morph Editing

### 7.1 目的

MS20の目的は、既存の `あ / い / う / え / お` リップモーフ範囲内で、発音イベント単位の調整機能を追加することである。

MS20で扱う「モーフ編集機能」は、任意モーフ編集ではない。対象は、既存リップ生成結果に含まれる発音イベントの開口量・閉口・スロープ・保持などの調整に限定する。

### 7.2 In Scope

* 発音イベント単位の編集対象定義
* 開口量調整
* 閉口・スムーズ調整
* slope / softness / hold の扱い整理
* Preview への反映
* VMD writer への反映
* 編集状態の保持方針
* GUI編集導線
* 既存自動生成結果との関係整理
* テスト追加
* docs 同期

### 7.3 Out of Scope

* 任意モーフ編集
* 表情モーフ全般の編集
* MMDモデルからのモーフ一覧読み込み
* PMX / PMD 解析
* VMD writer の全面再設計
* タイムライン型の汎用モーション編集
* 英語対応
* 音声のみ入力対応の追加実装
* 既存 `あ / い / う / え / お` 以外のモーフ自動生成

### 7.4 想定Block構成

MS20は、以下のような Block に分割する想定とする。

```text
MS20-B1: Per-Event Morph Editing Requirements / Scope Lock
MS20-B2: Event Data Contract Extension
MS20-B3: Preview Reflection Foundation
MS20-B4: GUI Editing Controls
MS20-B5: Writer Integration
MS20-B6: Save / Restore Editing State Policy
MS20-B7: Tests / Docs / Regression
MS20-B8: MS20 Closeout
```

### 7.5 MS20の受け入れ条件

MS20の完了条件は以下とする。

* 既存リップモーフ `あ / い / う / え / お` の範囲内で編集できる
* 発音イベント単位で調整対象を識別できる
* 編集内容が Preview に反映される
* 編集内容が VMD 出力に反映される
* 自動生成結果と手動編集結果の関係が説明されている
* 既存の TEXTあり / 音声あり処理が壊れていない
* docs に MS20 の対象範囲と非対象範囲が明記されている

## 8. MS21以降の候補

MS21以降は、MS18〜MS20の完了状態を踏まえて再評価する。

現時点で候補に留めるものは以下とする。

### 8.1 同音母音連続時の谷スムージング

#### 目的

同じ母音が連続する箇所で、不自然な口形の谷を減らす。

#### 備考

MS20の発音イベント単位編集と関係が深いため、MS20完了後に再評価する。

### 8.2 英語対応

#### 目的

英語音声から最低限のリップモーション生成を成立させる。

#### 備考

英語対応は、音声認識だけでなく、英語音素から日本語5母音モーフへのマッピング設計が必要である。そのため、MS19の音声のみ入力対応が安定してから検討する。

### 8.3 配布方式改善

#### 目的

GitHub Release 配布、ZIP構成、将来的な installer 方針を改善する。

#### 備考

MS18では package 化前の確認までを主対象とし、installer 導入は原則として MS21以降の検討課題とする。

### 8.4 cache / temp 管理改善

#### 目的

解析用WAVや一時ファイルの保存・削除・ユーザー説明を改善する。

#### 備考

MS18でセキュリティ・配布前確認として必要最小限を扱う。ユーザー向け管理UIなどは MS21以降の検討課題とする。

## 9. ドキュメント運用方針

### 9.1 正本扱い

MS18以降のロードマップは、本書を正本候補として扱う。

旧文書 `docs/Ver0_4_Expansion_Roadmap_for_Antigravity.md` は、MS18以降の判断材料としては原則使用しない。参照する場合は、過去の構想確認に限定する。

### 9.2 更新対象

MS18開始時には、必要に応じて以下を更新する。

* `docs/MS18_and_Beyond_Roadmap.md`
* `docs/MS17_and_Beyond_Index.md`
* `docs/repo_milestone.md`
* `docs/Version_Control.md`
* `README.md`
* `readme_mmdautolip.txt`
* `NOTICE`
* `THIRD_PARTY_LICENSES.md`
* `docs/Release_Package_Manifest.md`

ただし、README はエンドユーザー向け文書であるため、開発者向けの細かい計画は docs 側に寄せる。

### 9.3 実装プラン文書

各 Block の実装前には、必要に応じて以下の形式で実装プランを作成する。

```text
docs/Implementation_Plan/MS18-B1_Implementation_Plan.md
docs/Implementation_Plan/MS18-B2_Implementation_Plan.md
...
```

実装プランでは、次を明確に分ける。

* In Scope
* Out of Scope
* 前提条件
* 対象ファイル
* 実装方針
* 詳細ステップ
* テスト方針
* 受け入れ条件
* リスクと対策
* AI agent 作業時の注意

## 10. AI agent 作業時の注意

### 10.1 共通注意

AI agent に作業を依頼する場合は、毎回以下を明記する。

* 対象ブランチ
* 作業段階
* 実装を行うか、確認のみか
* 変更してよいファイル
* 変更してはいけないファイル
* 実行する確認コマンド
* 完了報告形式

### 10.2 MS18で特に重要な注意

MS18では、リファクタリングとセキュリティチェックを扱うが、作業範囲を広げすぎてはならない。

AI agent には、次を明示する。

* 新機能を追加しない
* pipeline の意味論を変えない
* VMD writer を再設計しない
* GUI レイアウトを刷新しない
* 音声のみ入力対応を先行実装しない
* モーフ編集機能を先行実装しない
* リファクタリングは挙動非変更に限定する
* セキュリティ修正は必要最小限に限定する
* 実行したテストと未実行のテストを分けて報告する

### 10.3 推奨確認コマンド

MS18開始時には、最低限以下を確認する。

```powershell
git status
git branch
git log --oneline -n 10
git remote -v
git fetch origin
git status
git log --oneline -n 10 origin/main
git diff --stat
git diff --name-only
git diff --cached --stat
git diff --cached --name-only
git ls-files cache
```

必要に応じて、テストは以下を使用する。

```powershell
.\.venv\Scripts\python.exe -m pytest tests
```

ただし、既知の wx teardown 由来の終了コード不安定性がある場合は、限定テストを分割して実行し、表示上の pass 数と終了コードを分けて記録する。

## 11. リスクと対策

### 11.1 MS18のリスク

#### リスク

リファクタリング範囲が広がり、リリース前安定化ではなく再実装に近づく。

#### 対策

* MS18-B3で変更範囲を固定する
* MS18-B4では B3で定義した範囲以外を変更しない
* 差分レビューで In Scope / Out of Scope を照合する

### 11.2 セキュリティチェックのリスク

#### リスク

一般的な抽象チェックに終始し、MMD_AutoLipTool 固有の危険箇所を見落とす。

#### 対策

* ffmpeg / ffprobe
* subprocess
* temp / cache
* PyInstaller onefile
* 外部ファイル読み込み
* 配布ZIP
* エラーメッセージ
* FFmpeg ライセンス通知

以上に対象を絞って確認する。

### 11.3 MS19のリスク

#### リスク

音声のみ入力対応が、書き起こし、読み生成、母音変換、GUI状態、Preview、VMD保存にまたがり、範囲が広がりやすい。

#### 対策

* MS19-B1で TEXTあり / TEXTなしの状態契約を先に固定する
* 既存 TEXTあり導線を壊さない
* 最初は日本語音声のみを対象とする
* 英語対応は MS19 から除外する

### 11.4 MS20のリスク

#### リスク

モーフ編集機能が任意モーフ編集や汎用VMD編集へ拡大する。

#### 対策

* 対象を `あ / い / う / え / お` に限定する
* 発音イベント単位のリップ編集に限定する
* PMX / PMD 読み込みは扱わない
* 任意モーフ編集は扱わない

## 12. 到達イメージ

MS18完了時点では、次の状態を目指す。

* MS17実装がリリース前確認済みである
* セキュリティ上の主要確認が完了している
* 処理効率化・重複整理が必要最小限実施されている
* `build.ps1 -SmokeLaunch` の残課題が整理されている
* FFmpeg同梱配布時のライセンス通知方針が確定している
* 実MMD確認が完了している
* package 化へ進めるか判断できる

MS19完了時点では、次の状態を目指す。

* TEXTなしで音声のみから最低限の VMD を生成できる
* TEXTあり導線が維持されている
* 音声のみ入力の制約とエラーがユーザーに説明されている
* 作業状態を初期化し、複数素材を連続して処理できる

MS20完了時点では、次の状態を目指す。

* 既存の `あ / い / う / え / お` リップモーフ範囲内で、発音イベント単位の調整が可能になる
* Preview と VMD 出力が編集内容に追従する
* 汎用モーフ編集ではなく、リップモーション補正機能として成立している

## 13. 次に行う作業

次に行う作業は、MS19 Closeout A判定後のpackage / release作業、またはMS20計画策定である。

MS18-B7では、実際の MikuMikuDance 上で VMD と MMD用WAV の読み込み・再生を確認し、ユーザー確認通過・問題なしとして記録した。

MS18-B6で検出したpackage化前追加確認事項は、2026-07-03のユーザー判断によりクリア扱いとした。

MS18-B7完了後の推奨作業段階は以下とする。

```text
MS18 closeout判定は A: OK。package 化へ進める。
main / origin/main を正本として扱う。
feature/MS17 は古い状態として扱い、参照対象にしない。
MS18全体の方針は本書に従う。
MMD本体でのVMD読み込み、MMD用WAV読み込み、音声再生、リップモーション同期の目視確認はB7で通過済み。
MS19-B1 Voice-only Input Requirements / State Contract は完了済みである。
MS19-B2 Transcription Pipeline Pre-check は完了済みである。
MS19-B3 Textless Pipeline Integration Foundation は完了済みである。
MS19-B4 GUI Entry Point and State Handling は完了済みである。
MS19-B5 Review / Edit Transcription Result Flow は完了済みである。ユーザー側B5確認も通過・問題なしである。
MS19-B6 VMD / Preview / Save Integration は完了済みである。対象自動スモーク36件とユーザー側B6確認は通過・問題なしである。
MS19-B7 Error Handling / Tests / Docs は完了済みである。通常の `pytest tests` は360件すべてpass表示まで完走し、既存wx終了処理由来のprocess exit code 1のみ継続記録している。ユーザー確認は通過・問題なしである。
MS19-B8 Workspace Reset / New Session Flow は完了している。`新規作業... Ctrl+N` による作業データ限定reset、確認キャンセル、Busy制御、late callback破棄、設定・履歴保持を実装し、ユーザースモークテストも通過・問題なしである。MS19 CloseoutはB9で完了した。
MS19-B9 Closeoutは2026-07-13に実施した。MS19固有テスト33件、計画指定回帰62件、全体テスト368件がpass表示となった。`test_wx_ms14_b6_closeout.py` の終了処理を補修し、access violationの再発がないことを確認した。ユーザーチェックも通過・問題なしであり、MS19 CloseoutはA判定とした。
次工程はpackage / release作業、またはMS20計画策定である。
```
