# MS17-B2 Implementation Plan

## 1. 文書情報

- Project: MMD_AutoLipTool
- Milestone: MS17
- Block: MS17-B2
- Block name: FFmpeg / ffprobe 接続方式・ライセンス・配布方針整理
- Target branch: `feature/MS17`
- Output path: `docs/Implementation_Plan/MS17-B2_Implementation_Plan.md`
- Target GUI: wxPython
- Target environment: Windows 11
- IDE: Google Antigravity
- Coding AI: Gemini 3.1 Pro
- Shell: Windows PowerShell
- 作業種別: 方針整理 + 実装プラン文書作成
- 実装変更: 禁止
- FFmpeg実行確認: 禁止
- テスト実行: 原則なし

## 2. 背景

MS17では、wav / mp3 / m4a 入力対応、FFmpeg / ffprobe 接続、解析用WAV生成、MMD用WAV同時出力を扱う。

その前提として、MS17-B2では FFmpeg / ffprobe の接続方式、探索優先順、配布方針、ライセンス記録方針を整理する必要がある。

MMD_AutoLipToolの主利用者は、Windows上でMMDを利用する個人ユーザーであり、必ずしもPython、GitHub、PATH設定、外部CLI導入に詳しいとは限らない。そのため、MS17ではFFmpeg / ffprobeを配布物に同梱する方向を推奨する。

ただし、FFmpeg / ffprobeは第三者配布物であり、MIT Licenseの本体ソースコードと同じ扱いにはできない。同梱する場合は、`NOTICE`、`THIRD_PARTY_LICENSES.md`、`docs/Release_Package_Manifest.md`、README、ビルド手順の整備が必須である。

MS17-B2では、実装には入らず、方針整理と実装プラン文書作成に限定する。`ffmpeg.exe -version` や `ffprobe.exe -version` の実行確認も行わない。

## 3. 目的

MS17-B2の目的は、MS17-B3以降で迷わず実装できるように、FFmpeg / ffprobe に関する以下の方針を明確化することである。

1. FFmpeg / ffprobe の利用目的
2. 同梱方式と外部導入方式の比較
3. MS17で採用する推奨方針
4. 開発時・配布時の配置基準
5. 探索優先順
6. PATH fallback の扱い
7. 自動ダウンロードをMS17対象外にすること
8. ライセンス・NOTICE・第三者ライセンス記録の扱い
9. B3以降で実装する対象
10. B3以降で実装しない対象

## 4. In Scope

MS17-B2で行う作業は以下。

- FFmpeg / ffprobe の利用目的整理
- 同梱方式と外部導入方式の比較
- MS17での推奨方針決定
- `FFmpeg\bin\ffmpeg.exe` / `FFmpeg\bin\ffprobe.exe` を基準配置とする方針整理
- 探索優先順の整理
- PATH fallback の扱い整理
- 自動ダウンロード禁止方針の明記
- LICENSE / NOTICE / THIRD_PARTY_LICENSES の役割整理
- Release Package Manifest への記録方針整理
- build.ps1 / PyInstaller spec との関係整理
- README更新方針の整理
- B3以降で実装すべき対象の整理
- `docs/Implementation_Plan/MS17-B2_Implementation_Plan.md` の作成

## 5. Out of Scope

MS17-B2では以下を行わない。

- FFmpeg / ffprobe 探索コードの実装
- FFmpeg / ffprobe 実行ラッパーの実装
- `ffmpeg.exe -version` の実行確認
- `ffprobe.exe -version` の実行確認
- mp3 / m4a 入力実装
- 解析用WAV生成実装
- MMD用WAV出力実装
- 音声変換エラー処理実装
- GUI変更
- README本文更新
- NOTICE本文更新
- THIRD_PARTY_LICENSES本文更新
- Release Package Manifest本文更新
- build.ps1変更
- PyInstaller spec変更
- FFmpegバイナリのrepo追加
- FFmpegバイナリの自動ダウンロード
- FFmpeg配布条件未確認のままの配布確定
- テスト追加
- テスト修正
- テスト実行

## 6. 前提条件

- MS17用branchは `feature/MS17` とする。
- MS17-B2は `feature/MS17` 上で行う。
- MS17-B1でrepo状態確認が完了している前提とする。
- MS17-B1で発見されたREADME / docs矛盾がある場合、B2ではそれを方針整理の材料として扱う。
- B2では実装しない。
- B2ではFFmpeg / ffprobeを実行しない。
- MS17ではFFmpeg / ffprobe自動ダウンロードを行わない。
- MS17の推奨方針はFFmpeg / ffprobe同梱方向とする。
- 同梱する場合でも、ライセンス・NOTICE・第三者ライセンス文書整備が完了条件である。
- PATH上のFFmpeg / ffprobeはfallbackとして扱う。
- PATH上のFFmpeg / ffprobeはバージョンやビルド条件が不定であるため、使用時には実体パスとversion情報を後続Blockで取得・表示・記録できる設計にする。

## 7. 対象ファイル

MS17-B2では、主に以下を確認対象とする。

```text
README.md
NOTICE
THIRD_PARTY_LICENSES.md
LICENSE

docs/Release_Package_Manifest.md
docs/MMD_Audio_WAV_Compatibility_Specification.md
docs/Error_Handling_Specification.md
docs/Pipeline_Data_Contract_Specification.md
docs/GUI_State_Theme_Specification.md
docs/Security_Safety_Specification.md
docs/Version_Control.md
docs/repo_milestone.md
docs/MS17_Block_Breakdown_for_Antigravity.md

build.ps1
MMD_AutoLipTool.spec
requirements.txt
pyproject.toml

docs/Implementation_Plan/MS17-B2_Implementation_Plan.md
````

存在しないファイルがある場合は、作成対象が `docs/Implementation_Plan/MS17-B2_Implementation_Plan.md` のみであることに注意する。その他のファイルは、存在しない場合もB2では作成しない。必要性を報告に含める。

## 8. 実装方針

MS17-B2は、実装Blockではなく設計・方針整理Blockである。

Antigravityは、既存README / docs / build / packaging関連記述を確認し、以下を整理する。

* 現状、FFmpeg / ffprobe を同梱前提としている記述があるか
* 現状、外部導入前提としている記述があるか
* READMEとdocsで矛盾があるか
* onefile / onedir / 配布フォルダ構成に矛盾があるか
* NOTICE / THIRD_PARTY_LICENSES / Release Package Manifest に不足があるか
* MS17で採用すべき推奨方針
* B3以降で実装・補正すべき項目

MS17-B2で作成・変更してよいファイルは、原則として以下のみ。

```text
docs/Implementation_Plan/MS17-B2_Implementation_Plan.md
```

それ以外のファイルは、問題を見つけても修正せず、報告に記録する。

## 9. MS17-B2で採用する推奨方針

### 9.1 配布方針

MS17では、FFmpeg / ffprobe を配布物に同梱する方向を推奨する。

理由:

* Windows / MMDユーザー向けに導入しやすい
* PATH設定を不要にできる
* ユーザー環境差によるトラブルを減らせる
* GUIアプリとしての自己完結性が高まる

ただし、同梱は無条件に確定ではない。以下を完了条件とする。

* 同梱するFFmpeg配布物のライセンス条件確認
* `NOTICE` 更新
* `THIRD_PARTY_LICENSES.md` 更新
* `docs/Release_Package_Manifest.md` 更新
* READMEへの配布時注意の明記
* build.ps1 / spec の配置ルール整合
* 配布物に含めるファイル範囲の明確化

### 9.2 配置方針

基準配置は以下とする。

```text
FFmpeg\bin\ffmpeg.exe
FFmpeg\bin\ffprobe.exe
```

開発時はrepo直下の上記配置を優先する。

配布時は、アプリ配布フォルダ内に以下のような形で含める方向を想定する。

```text
dist\MMD_AutoLipTool\FFmpeg\bin\ffmpeg.exe
dist\MMD_AutoLipTool\FFmpeg\bin\ffprobe.exe
```

実際のPyInstaller onefile / onedir構成と整合する必要があるため、最終配置は後続Blockで `build.ps1` と `MMD_AutoLipTool.spec` を確認して確定する。

### 9.3 探索優先順

MS17での推奨探索順は以下。

```text
1. repo直下 FFmpeg\bin\ffmpeg.exe / ffprobe.exe
2. 配布アプリ基準の FFmpeg\bin\ffmpeg.exe / ffprobe.exe
3. PATH 上の ffmpeg.exe / ffprobe.exe
```

PATH上のFFmpeg / ffprobeはfallback扱いとする。

PATH fallbackを使う場合、B3以降で以下を実装・記録対象とする。

* 実際に使用した `ffmpeg.exe` / `ffprobe.exe` のパス
* version情報
* 見つからなかった場合のユーザー向けエラー
* PATH版は環境依存であることのInfo表示またはログ記録

### 9.4 自動ダウンロード方針

MS17では、FFmpeg / ffprobe の自動ダウンロードを行わない。

理由:

* 配布元検証が必要になる
* ネットワーク失敗時の復旧が必要になる
* セキュリティ説明が増える
* Windows Defender等で不審に見えやすくなる可能性がある
* ライセンス表示と取得元管理が複雑になる
* MS17の目的から範囲が広がりすぎる

自動ダウンロードはMS18以降の検討課題とする。

## 10. 詳細ステップ

### Step 1: branch / 作業ツリー確認

最初に以下を実行する。

```powershell
git status
git branch
git log --oneline -n 10
git diff --stat
git diff --name-only
git diff --cached --stat
git diff --cached --name-only
```

確認すること。

* 現在branchが `feature/MS17` であるか
* MS17-B1後の作業ツリー状態
* 既にMS17-B2実装プランが存在するか
* 意図しない差分がないか

現在branchが `feature/MS17` ではない場合、checkoutせず報告する。

### Step 2: MS17-B1結果の確認

MS17-B1完了報告または関連docsを確認する。

確認すること。

* MS17-B2へ進める判定だったか
* B2前に補正すべきP1問題が残っていないか
* README / docsの矛盾がB2方針整理で扱える範囲か
* branch / 作業ツリー整理が必要ではないか

B2へ進めない状態であれば、MS17-B2文書作成前に報告する。

### Step 3: FFmpeg関連の現状記述確認

以下を確認する。

```text
README.md
NOTICE
THIRD_PARTY_LICENSES.md
docs/Release_Package_Manifest.md
build.ps1
MMD_AutoLipTool.spec
```

確認観点。

* `FFmpeg\bin\ffmpeg.exe` の記述があるか
* `FFmpeg\bin\ffprobe.exe` の記述があるか
* 同梱前提の記述があるか
* 外部導入前提の記述があるか
* READMEとbuild/docsで配置先が一致しているか
* onefile / onedir の説明が矛盾していないか
* 配布物に含めるFFmpeg関連ファイル範囲が記録されているか
* FFmpegのversion記述がある場合、固定されているか、例示か
* FFmpeg配布時のライセンス注意があるか

### Step 4: ライセンス・NOTICE・第三者ライセンス確認

以下を確認する。

```text
LICENSE
NOTICE
THIRD_PARTY_LICENSES.md
docs/Release_Package_Manifest.md
```

確認観点。

* 本体ソースコードがMIT Licenseであること
* FFmpeg等の第三者配布物が本体MIT Licenseと混同されていないこと
* FFmpeg同梱時に必要なNOTICEがあるか
* THIRD_PARTY_LICENSESにFFmpeg関連項目があるか
* upstream license texts を含める必要性が記録されているか
* Release Package Manifest に同梱物としてFFmpegが記録されているか
* 不足がある場合、B3以降またはdocs補正Blockで対応すべき項目として分類する

MS17-B2では、これらの文書本文は修正しない。

### Step 5: 探索優先順の設計整理

MS17で採用する探索優先順を以下として整理する。

```text
1. repo直下 FFmpeg\bin\
2. 配布アプリ基準 FFmpeg\bin\
3. PATH
```

整理する観点。

* 開発時の基準パス
* PyInstaller配布時の基準パス
* PATH fallbackの位置づけ
* PATH版を使った場合の注意
* 実体パスとversion情報の記録方針
* 見つからない場合のエラー方針
* `ffmpeg.exe` と `ffprobe.exe` の片方だけ見つかった場合の扱い

### Step 6: 自動ダウンロード禁止方針の明記

MS17では自動ダウンロードを行わないことを、実装プランに明記する。

確認・整理する観点。

* 自動ダウンロード実装をB3以降に含めない
* GUIからダウンロード誘導しない
* build時に自動取得しない
* 初回起動時に自動取得しない
* 不足時はユーザー向けに不足を説明する
* MS18以降の検討課題として残す

### Step 7: B3以降への実装引き継ぎ整理

B3以降で実装すべき項目を整理する。

B3以降の候補。

```text
src/core/ffmpeg_locator.py
src/core/ffprobe_runner.py
src/core/ffmpeg_runner.py
src/core/audio_errors.py
src/core/audio_probe.py
src/core/audio_convert.py
```

B2ではこれらを作成・変更しない。

B3以降で実装すべきこと。

* FFmpeg / ffprobe探索
* 実体パス解決
* version確認
* ffprobe実行
* ffmpeg実行
* timeout
* terminate / kill
* エラー分類
* GUIへのエラー表示
* Info表示
* ログまたは内部状態への使用実体記録

### Step 8: `docs/Implementation_Plan/MS17-B2_Implementation_Plan.md` 作成

本計画に基づき、以下を作成する。

```text
docs/Implementation_Plan/MS17-B2_Implementation_Plan.md
```

作成後、以下を確認する。

```powershell
git diff -- docs/Implementation_Plan/MS17-B2_Implementation_Plan.md
```

他のファイルに差分が出ていないことを確認する。

### Step 9: 完了報告

完了報告では、以下を必ず分ける。

1. 確認したbranch / commit
2. 作業ツリー状態
3. MS17-B1結果の扱い
4. FFmpeg関連現状記述
5. 同梱方式 / 外部導入方式の比較
6. MS17での推奨方針
7. 探索優先順
8. 自動ダウンロード禁止方針
9. ライセンス・NOTICE・THIRD_PARTY_LICENSES・Release Package Manifestの不足
10. B3以降で実装すべき項目
11. 今回作成したファイル
12. 今回変更していないファイル
13. 実行していない確認・テスト

## 11. 状態遷移 / データ契約

MS17-B2では、アプリ内部の状態遷移やデータ契約は変更しない。

ただし、B3以降で以下の契約を追加する前提で方針を整理する。

### 11.1 FFmpeg / ffprobe 解決結果

B3以降では、以下のような情報を保持する設計を想定する。

```text
ffmpeg_path
ffprobe_path
ffmpeg_source
ffprobe_source
ffmpeg_version
ffprobe_version
```

`source` の候補。

```text
repo_local
bundled
path
not_found
```

### 11.2 エラー分類

B3以降では、少なくとも以下を区別できるようにする。

```text
ffmpeg_not_found
ffprobe_not_found
ffmpeg_permission_error
ffprobe_permission_error
ffmpeg_execution_failed
ffprobe_execution_failed
ffmpeg_timeout
ffprobe_timeout
ffmpeg_cancelled
ffprobe_cancelled
```

MS17-B2では、これらを実装しない。B3以降の設計候補として記録する。

### 11.3 配布物契約

配布時にFFmpeg / ffprobeを同梱する場合、以下を配布物契約に含める。

```text
FFmpeg\bin\ffmpeg.exe
FFmpeg\bin\ffprobe.exe
LICENSE
NOTICE
THIRD_PARTY_LICENSES.md
docs or bundled license texts
```

実際に同梱するlicense textsの範囲は、B2の方針整理後、配布関連docsで確定する。

## 12. テスト方針

MS17-B2ではテストを実行しない。

理由:

* B2は方針整理と実装プラン文書作成のみである
* FFmpeg / ffprobe探索・実行実装はB3以降で扱う
* B2では `ffmpeg.exe -version` / `ffprobe.exe -version` も実行しない
* ローカル環境のFFmpeg有無にB2の成否を依存させないため

B3以降で追加するテスト候補は以下。

```text
tests/test_ms17_b3_ffmpeg_locator.py
tests/test_ms17_b4_ffprobe_runner.py
tests/test_ms17_b5_ffmpeg_runner.py
tests/test_ms17_b5_audio_convert.py
tests/test_ms17_b7_mmd_wav_export.py
```

実際のファイル名はrepoの命名規則に合わせて調整する。

## 13. 受け入れ条件

MS17-B2は、以下を満たしたら完了とする。

* `feature/MS17` branch上で作業されている
* MS17-B1結果を確認している
* FFmpeg / ffprobe の現状記述を確認している
* 同梱方式と外部導入方式の比較が記録されている
* MS17では同梱方向を推奨することが記録されている
* `FFmpeg\bin\ffmpeg.exe` / `FFmpeg\bin\ffprobe.exe` を基準配置とすることが記録されている
* 探索優先順が `repo配置 → 配布配置 → PATH` として記録されている
* PATH fallback が環境依存であることが記録されている
* MS17では自動ダウンロード禁止であることが記録されている
* LICENSE / NOTICE / THIRD_PARTY_LICENSES / Release Package Manifest の確認観点が記録されている
* B3以降で実装すべき項目が整理されている
* `docs/Implementation_Plan/MS17-B2_Implementation_Plan.md` が作成されている
* B2ではFFmpeg / ffprobe実行確認をしていない
* B2ではコード実装をしていない
* B2では対象外ファイルを変更していない

## 14. リスクと対策

### Risk 1: FFmpeg同梱に伴うライセンス不備

対策:

* 同梱推奨とするが、配布確定条件として `NOTICE` / `THIRD_PARTY_LICENSES.md` / Release Package Manifest 更新を必須にする
* MIT License本体とFFmpeg等の第三者ライセンスを混同しない

### Risk 2: PATH fallbackによる環境差

対策:

* PATHはfallback扱いにする
* B3以降で使用実体パスとversion情報を取得・表示・記録できるようにする
* PATH版使用時はInfoまたはログに残す

### Risk 3: 自動ダウンロードで範囲が拡大する

対策:

* MS17では自動ダウンロード禁止と明記する
* MS18以降の検討課題に分離する

### Risk 4: onefile / onedir / 配布フォルダ構成の矛盾

対策:

* B2で現状記述を確認する
* B3以降またはpackaging補正Blockで build.ps1 / spec / Release Package Manifest を整合させる

### Risk 5: B2で実装まで進んでしまう

対策:

* B2の変更許可対象を `docs/Implementation_Plan/MS17-B2_Implementation_Plan.md` のみに限定する
* FFmpeg / ffprobe の実行確認も禁止する

### Risk 6: FFmpeg versionを固定しすぎる

対策:

* READMEやdocsで特定versionが記述されている場合、固定要件か例示かを区別する
* B2ではversion固定を決め打ちせず、配布候補として扱う
* B3以降で実体version取得を行う

## 15. Antigravity 実施時の注意

以下のプロンプトを Antigravity に渡して実施する。

```text
今回は MS17-B2 です。

目的:
FFmpeg / ffprobe の接続方式・ライセンス・配布方針を整理し、
docs/Implementation_Plan/MS17-B2_Implementation_Plan.md を作成してください。

重要:
- 対象branchは feature/MS17 です。
- 実装は行わないでください。
- コード変更は行わないでください。
- GUI変更は行わないでください。
- README / NOTICE / THIRD_PARTY_LICENSES.md / Release Package Manifest の本文修正は行わないでください。
- FFmpeg / ffprobe の実行確認は行わないでください。
- ffmpeg.exe -version / ffprobe.exe -version は実行しないでください。
- テストは実行しないでください。
- 作成・変更してよいファイルは docs/Implementation_Plan/MS17-B2_Implementation_Plan.md のみです。

最初に以下を実行してください。

git status
git branch
git log --oneline -n 10
git diff --stat
git diff --name-only
git diff --cached --stat
git diff --cached --name-only

現在branchが feature/MS17 ではない場合は、checkoutせず、その時点で報告してください。

確認対象:

README.md
NOTICE
THIRD_PARTY_LICENSES.md
LICENSE

docs/Release_Package_Manifest.md
docs/MMD_Audio_WAV_Compatibility_Specification.md
docs/Error_Handling_Specification.md
docs/Pipeline_Data_Contract_Specification.md
docs/GUI_State_Theme_Specification.md
docs/Security_Safety_Specification.md
docs/Version_Control.md
docs/repo_milestone.md
docs/MS17_Block_Breakdown_for_Antigravity.md

build.ps1
MMD_AutoLipTool.spec
requirements.txt
pyproject.toml

確認観点:

1. FFmpeg / ffprobe を同梱前提としている記述があるか
2. FFmpeg / ffprobe を外部導入前提としている記述があるか
3. READMEとdocsで配置先や配布方針が矛盾していないか
4. onefile / onedir / dist配置の記述が矛盾していないか
5. FFmpeg\bin\ffmpeg.exe / FFmpeg\bin\ffprobe.exe の記述があるか
6. PATH上のFFmpeg / ffprobeを使う記述があるか
7. FFmpeg自動ダウンロードに見える記述があるか
8. NOTICEにFFmpeg等の第三者配布物への注意があるか
9. THIRD_PARTY_LICENSES.mdにFFmpeg関連項目があるか
10. Release Package ManifestにFFmpeg配置が記録されているか
11. MIT License本体とFFmpeg等の第三者ライセンスが混同されていないか
12. B3以降で実装すべき項目は何か

MS17-B2で採用する方針:

- FFmpeg / ffprobe は配布物に同梱する方向を推奨する。
- 基準配置は repo直下 FFmpeg\bin\ffmpeg.exe / FFmpeg\bin\ffprobe.exe とする。
- 探索優先順は repo配置 → 配布配置 → PATH とする。
- PATH上のFFmpeg / ffprobeはfallback扱いにする。
- PATH fallbackを使う場合は、B3以降で実体パスとversion情報を取得・表示・記録できる設計にする。
- MS17ではFFmpeg / ffprobeの自動ダウンロードを行わない。
- 同梱する場合は NOTICE / THIRD_PARTY_LICENSES.md / Release Package Manifest の整備を必須とする。

作成する文書:

docs/Implementation_Plan/MS17-B2_Implementation_Plan.md

完了前に以下を確認してください。

git diff --stat
git diff --name-only
git diff -- docs/Implementation_Plan/MS17-B2_Implementation_Plan.md

完了報告では、以下を必ず分けてください。

1. 確認したbranch / commit
2. 作業ツリー状態
3. MS17-B1結果の扱い
4. FFmpeg関連の現状記述
5. 同梱方式 / 外部導入方式の比較
6. MS17での推奨方針
7. 探索優先順
8. PATH fallbackの扱い
9. 自動ダウンロード禁止方針
10. ライセンス・NOTICE・THIRD_PARTY_LICENSES・Release Package Manifestの不足
11. B3以降で実装すべき項目
12. 今回作成したファイル
13. 今回変更していないファイル
14. FFmpeg / ffprobe実行確認をしていないこと
15. テストを実行していないこと
```

## 16. 完了報告テンプレート

Antigravityは、完了時に以下の形式で報告する。

```text
MS17-B2 完了報告

1. 確認したbranch / commit
- branch:
- latest commit:

2. 作業ツリー状態
- git status:
- staged diff:
- unstaged diff:

3. MS17-B1結果の扱い
- B1判定:
- B2へ進める理由:
- B2前に残っていた注意点:

4. FFmpeg関連の現状記述
- README:
- build.ps1:
- MMD_AutoLipTool.spec:
- docs:
- NOTICE:
- THIRD_PARTY_LICENSES.md:
- Release Package Manifest:

5. 同梱方式 / 外部導入方式の比較
- 同梱方式の利点:
- 同梱方式のリスク:
- 外部導入方式の利点:
- 外部導入方式のリスク:

6. MS17での推奨方針
- 推奨:
- 理由:
- 未確定条件:

7. 探索優先順
- 1:
- 2:
- 3:

8. PATH fallbackの扱い
- fallbackとして許可するか:
- 記録すべき情報:
- ユーザーへの説明:

9. 自動ダウンロード禁止方針
- MS17で行わないこと:
- MS18以降送り:

10. ライセンス・配布文書の不足
- NOTICE:
- THIRD_PARTY_LICENSES.md:
- Release Package Manifest:
- README:
- upstream license texts:

11. B3以降で実装すべき項目
- ffmpeg / ffprobe探索:
- version取得:
- ffprobe実行:
- ffmpeg実行:
- エラー分類:
- GUI表示:
- packaging補正:

12. 今回作成したファイル
- docs/Implementation_Plan/MS17-B2_Implementation_Plan.md:

13. 今回変更していないファイル
- README:
- NOTICE:
- THIRD_PARTY_LICENSES.md:
- build.ps1:
- MMD_AutoLipTool.spec:
- src:
- tests:

14. 実行していない確認
- ffmpeg.exe -version:
- ffprobe.exe -version:
- pytest:
- unittest:

15. 次に進めるか
- MS17-B3へ進めるか:
- 先に補正すべき項目:
```

## 17. MS17-B3への引き継ぎ条件

MS17-B3へ進む前に、B2報告から以下を引き継ぐ。

* FFmpeg / ffprobe の推奨探索順
* 基準配置
* PATH fallbackの扱い
* 自動ダウンロード禁止
* 見つからない場合のエラー方針
* version情報の取得・記録方針
* NOTICE / THIRD_PARTY_LICENSES / Release Package Manifest の不足
* build.ps1 / spec の補正必要性
* READMEの補正必要性

MS17-B3では、これらをもとに音声入力拡張の前提基盤、またはFFmpeg locatorの最小実装に進む。
