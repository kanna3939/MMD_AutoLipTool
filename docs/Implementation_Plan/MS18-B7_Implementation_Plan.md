# MS18-B7 Implementation Plan

## 1. 文書情報

- 文書名: MS18-B7 Implementation Plan
- 対象ブロック: MS18-B7 Actual MMD Manual Verification Closeout
- 想定配置先: `docs/Implementation_Plan/MS18-B7_Implementation_Plan.md`
- 作成日: 2026-07-02
- 作成ブランチ: `feature/MS18`
- 文書ステータス: Completed
- 完了日: 2026-07-03
- 前提:
  - MS18-B1 Repo / Release Readiness / Risk Inventory 完了
  - MS18-B2 Security Preflight Review 完了
  - MS18-B3 Refactor Scope Definition 完了
  - MS18-B4 Safe Refactor Implementation 完了
  - MS18-B5 SmokeLaunch / Process Residual Investigation 完了
  - MS18-B6 Release / Packaging / License Preflight 完了。package化前P2はユーザー判断によりクリア
- 注意:
  - B7は実MMD確認とMS18 closeout記録を扱う。
  - B6で残ったFFmpeg license texts / `FFmpeg\bin\` Git追跡 / PySide6 xref確認は、package化前P2として扱い、実MMD確認そのものと混同しない。

## 2. 背景

MS17では、wav / mp3 / m4a 入力、解析用WAV生成、MMD用WAV出力、worker化、Busy制御、README / 配布関連文書同期まで完了した。

MS18-B1からB3では、リリース前のリスク棚卸し、Security Preflight、MS18-B4以降の作業分離を行った。
MS18-B4では、FFmpeg / ffprobe探索元説明性改善と、Windows MCI向けの解析用WAV再生パス補正を行い、ユーザーテスト通過が報告された。
MS18-B5では、`build.ps1 -SmokeLaunch` の停止待機・残留確認と `-Clean` 時の旧onefile成果物削除を整理し、ユーザーテスト通過が報告された。
MS18-B6では、配布物・ライセンス・PyInstaller依存関係・`sample/` 同梱方針を確認し、package化前に追加確認が必要なP2を記録した。

残っているMS18本体の確認は、実際の MikuMikuDance 上で、生成済み VMD と MMD用WAV が読み込めるか、再生できるか、リップモーションとして大きな破綻がないかを確認することである。

## 3. 目的

MS18-B7の目的は、実MMD上で VMD / MMD用WAV の読み込み・再生・目視確認を行い、MS18 closeout可否を判定できる状態にすることである。

このBlockでは、実MMD確認結果を記録し、README / 配布用readmeへの手順追記が必要かを判断し、MS19へ進めるかどうかを整理する。

## 4. In Scope

- 実MMDでの VMD 読み込み確認
- 実MMDでの MMD用WAV 読み込み確認
- MMD上での音声再生確認
- リップモーション再生の目視確認
- 音声とリップモーションの大きなズレ・利用不能レベルの破綻確認
- 生成ファイルの配置手順確認
- 確認に使った入力条件・出力条件の記録
- README / `readme_mmdautolip.txt` への反映要否判断
- `docs/repo_milestone.md` / `docs/Version_Control.md` / `docs/MS17_and_Beyond_Index.md` / `docs/Implementation_Plan/MS18_Block_Breakdown.md` へのB7結果反映
- MS18 closeout判定
- MS19へ進む前提条件整理

## 5. Out of Scope

- MMD本体の不具合調査
- MMDモデル固有のモーフ差異対応
- VMD writer の品質改善
- 音声解析品質改善
- pipeline の意味論変更
- Preview / waveform の仕様変更
- GUIレイアウト変更
- 音声のみ入力対応
- モーフ編集機能
- 任意モーフ対応
- package作成
- GitHub Release公開
- installer作成
- FFmpeg build変更
- B6で残ったlicense / PySide6 / `FFmpeg\bin\` Git追跡方針の解消作業

## 6. 前提条件

B7実施前に、以下を確認する。

- 作業ブランチが `feature/MS18` である。
- MS18-B6実施結果の未コミット差分が存在する場合、その差分を上書きしない。
- B7開始時点の `docs/MS17_and_Beyond_Index.md` がB7を次作業として示している。
- `docs/Implementation_Plan/MS18_Block_Breakdown.md` がB7のIn Scope / Out of Scopeを定義している。
- 実MMD確認に使うVMDとMMD用WAVを用意できる。
- MMD本体とテスト用モデルをユーザー環境で利用できる。
- 実MMD確認はCodex側だけで完結しない可能性があるため、ユーザー手動確認結果を受け取って記録できる。

## 7. 対象ファイル

### 7.1 主対象

```text
docs/Implementation_Plan/MS18-B7_Implementation_Plan.md
docs/Implementation_Plan/MS18_Block_Breakdown.md
docs/MS17_and_Beyond_Index.md
docs/MS18_and_Beyond_Roadmap.md
docs/repo_milestone.md
docs/Version_Control.md
```

### 7.2 条件付き変更候補

```text
README.md
readme_mmdautolip.txt
docs/Release_Package_Manifest.md
```

条件付き変更候補は、実MMD確認でユーザー向け手順不足や明確な注意書き不足が見つかった場合のみ更新する。

### 7.3 参照対象

```text
docs/Implementation_Plan/MS18-B6_Implementation_Plan.md
docs/Release_Package_Manifest.md
docs/MMD_Audio_WAV_Compatibility_Specification.md
build.ps1
MMD_AutoLipTool.spec
dist/MMD_AutoLipTool.exe
FFmpeg/bin/
```

## 8. 実装方針

### 8.1 基本方針

- B7は確認と記録を中心にする。
- アプリの生成仕様やMMD用WAV仕様は変更しない。
- 実MMD確認で問題が出た場合は、原因を分類し、B7で修正するか、MS18 closeout保留にするかを判断する。
- B6のpackage化前P2はB7の実MMD確認とは別の残課題として扱う。
- 実MMD確認は、Codexが直接MMDを操作できない場合、ユーザー手動確認結果を正として記録する。

### 8.2 ユーザー判断が必要になり得る項目

現時点では、計画作成のために追加質問は不要。
ただしB7実施時には、以下の判断が必要になる可能性がある。

| 項目 | 推奨選択肢 | 理由 | 代替選択肢 |
| :--- | :--- | :--- | :--- |
| 実MMD確認の実施者 | ユーザー手動確認を正とする | MMD本体・モデル・表示確認はユーザー環境依存であり、Codex環境から正確に保証しにくい | Codexが可能な範囲でGUI操作補助する |
| 確認素材 | ユーザーが配布可否に関係しないローカル素材を指定する | `sample/` はB6で配布同梱未確定としたため、release判定用の証跡としてはユーザー指定素材の方が安全 | 既存 `sample/` をローカル検証専用として使う |
| 判定の厳しさ | 読み込み・再生・明らかな同期破綻なしを最低条件にする | B7は品質改善ではなくrelease readiness確認であり、細かなリップ品質調整はMS18範囲外 | 細かな品質不満もP2/P3として記録する |
| B6残課題の扱い | B7結果とは分離し、MS18 closeout判定でP2残として扱う | 実MMD確認とlicense/package課題は性質が異なる | B7前にB6残課題を別作業で解消する |

## 9. 詳細ステップ

### Step 1: repo状態確認

```powershell
git status
git branch
git log --oneline -n 10
```

確認観点:

- `feature/MS18` 上で作業しているか
- B6関連の未コミット差分が存在する場合、B7差分と混同しないか
- B7計画書作成後、差分が文書範囲に収まっているか

### Step 2: B6残課題の確認

以下を確認する。

```text
docs/Implementation_Plan/MS18-B6_Implementation_Plan.md
docs/Release_Package_Manifest.md
THIRD_PARTY_LICENSES.md
NOTICE
```

確認観点:

- `FFmpeg\bin\` Git追跡とSource code archive同梱の問題
- FFmpeg license texts / COPYING類未確認
- PyInstaller xref上の `PySide6` 参照
- `sample/` 実行用ZIP除外方針

B7ではこれらを解消しない。
MS18 closeout判定時に、P2残として扱うか、B7前に別作業で解消するかを明記する。

### Step 3: 実MMD確認用ファイルの用意

確認対象は以下。

```text
生成済み VMD
生成済み MMD用WAV
確認に使うMMDモデル
MMD本体
```

推奨:

- ユーザーが実際に使うローカル音声・テキストから生成したVMD / MMD用WAVを使用する。
- 配布可否が未確定の `sample/` は、release証跡ではなくローカル検証専用として扱う。

### Step 4: VMD読み込み確認

確認観点:

- MMDで対象モデルを開ける
- 生成済みVMDを読み込める
- 読み込み時にMMD側でエラーが出ない
- 口モーフキーがフレーム上で反映される

記録する内容:

- MMDの利用バージョンまたは識別可能な情報
- 使用モデル名またはモデル種別
- VMDファイル名
- 読み込み結果
- エラー有無

### Step 5: MMD用WAV読み込み・再生確認

確認観点:

- 生成済みMMD用WAVをMMDへ読み込める
- MMD上で音声再生できる
- 再生開始・停止に支障がない
- 音声ファイル名・配置場所がMMD利用上問題にならない

記録する内容:

- WAVファイル名
- WAV仕様が `pcm_s16le / 44100 Hz / stereo` 前提か
- 読み込み結果
- 再生結果
- エラー有無

### Step 6: リップモーション同期の目視確認

確認観点:

- 音声と口パクに大きなズレがない
- VMDが無音または極端な無動作になっていない
- リップモーションが全体的に再生される
- MMD上で利用不能と判断する重大破綻がない

注意:

- B7はリップ品質改善Blockではない。
- 細かな発音品質、表情の好み、モデル固有のモーフ見え方は、MS18の修正対象にしない。
- 利用不能レベルの破綻のみP1/P2として扱う。

### Step 7: 問題の分類

問題が出た場合は、以下に分類する。

```text
P1: 実MMDでVMDまたはMMD用WAVを読み込めず、MS18 closeout不可
P2: 読み込み・再生はできるが、release前に修正または手順明記が必要
P3: 記録・説明・手順上の軽微な補足
```

分類例:

- P1:
  - MMDでVMDが読み込めない
  - MMD用WAVがMMDで再生できない
  - 生成物が空または利用不能
- P2:
  - 手順不足によりユーザーが配置場所を誤りやすい
  - ファイル名や出力形式に注意書きが必要
  - B6由来のlicense/package P2が未解決
- P3:
  - README / readmeの説明補足
  - 実MMD確認環境の記録追記
  - MS19引き継ぎメモ

### Step 8: 文書反映

B7実施後に、以下を更新する。

```text
docs/Implementation_Plan/MS18-B7_Implementation_Plan.md
docs/Implementation_Plan/MS18_Block_Breakdown.md
docs/MS17_and_Beyond_Index.md
docs/MS18_and_Beyond_Roadmap.md
docs/repo_milestone.md
docs/Version_Control.md
```

必要な場合のみ、以下を更新する。

```text
README.md
readme_mmdautolip.txt
docs/Release_Package_Manifest.md
```

### Step 9: MS18 closeout判定

Block Breakdownの判定基準に従う。

```text
A. MS18 closeout OK。package 化へ進める。
B. MS18 closeout OK。ただし package 化前に軽微な確認事項あり。
C. MS18 closeout 保留。P1 / P2 の未解決課題あり。
D. MS18 closeout 不可。MS17実装または配布前提に重大な問題あり。
```

B6由来のpackage化前P2が残る場合、実MMD確認が通過しても、MS18全体closeoutはAにならない。
その場合は、BまたはCのどちらが妥当かを、残課題の重大度で判断する。

## 10. 状態遷移 / データ契約

B7では、アプリ内部の状態遷移やデータ契約を変更しない。

維持する契約:

- 入力音声、解析用WAV、MMD用WAVを混同しない。
- MMD用WAVは専用出力導線から保存する。
- VMD出力はリップモーフキーフレームのみを対象とする。
- `あ / い / う / え / お` の固定モーフ対象を維持する。
- 実MMD確認は、既存出力仕様の利用確認であり、生成仕様変更ではない。

## 11. テスト方針

### 11.1 自動テスト

B7は原則として実MMD手動確認Blockであり、コード変更を伴わない。
そのため、計画作成時点で自動テストは必須にしない。

文書更新後は以下を実行する。

```powershell
git diff --check
```

コードやREADME手順に影響する変更を行った場合は、変更範囲に応じて関連テストを実行する。

候補:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_ms17_b7_mmd_wav_export.py
.\.venv\Scripts\python.exe -m pytest tests\test_ms17_b7_mmd_wav_failure_cleanup.py
.\.venv\Scripts\python.exe -m pytest tests\test_ms17_b7_mmd_wav_overwrite_confirm.py
```

### 11.2 手動テスト

B7の中心は手動テストである。

最低限の確認:

- MMDでモデルを開く
- VMDを読み込む
- MMD用WAVを読み込む
- MMDで再生する
- 音声と口パクに利用不能レベルのズレがないことを目視する

### 11.3 ユーザー手動確認の扱い

Codex環境からMMD本体を直接確認できない場合は、ユーザー手動確認結果を根拠として記録する。

記録形式:

```text
- MMD確認実施者:
- 確認日:
- 使用MMD:
- 使用モデル:
- VMD:
- MMD用WAV:
- VMD読み込み:
- WAV読み込み:
- 再生:
- リップ同期:
- 問題:
- 判定:
```

## 12. 受け入れ条件

MS18-B7の受け入れ条件は以下。

- 実MMD確認結果が記録されている。
- VMD読み込み可否が明確である。
- MMD用WAV読み込み可否が明確である。
- MMD上で音声再生できるかが明確である。
- リップモーション同期の目視確認結果が記録されている。
- 問題がある場合、P1 / P2 / P3に分類されている。
- README / readme更新の要否が判断されている。
- MS18 closeout判定が記録されている。
- MS19へ進めるかどうかが判断できる。
- B6由来のpackage化前追加確認事項が、B7結果と分離して記録されている。

## 13. リスクと対策

### 13.1 MMD本体をCodex環境から直接確認できない

リスク:
Codex側でMMD本体を操作できず、実MMD確認を完結できない。

対策:
ユーザー手動確認結果を受け取り、確認条件・結果・判定を文書化する。

### 13.2 素材の出典・配布可否と実MMD確認が混ざる

リスク:
`sample/` やユーザー素材の配布可否問題と、MMD上の読み込み可否確認が混同される。

対策:
B7ではローカル確認素材として扱い、配布同梱可否はB6残課題または別作業で扱う。

### 13.3 品質改善へ範囲が広がる

リスク:
目視確認中にリップ品質改善要求が入り、MS18のrelease readiness範囲を超える。

対策:
B7では利用不能レベルの問題だけをP1/P2にし、細かな品質改善はMS19以降または別マイルストーンへ送る。

### 13.4 B6 package化前P2が残ったままA判定してしまう

リスク:
実MMD確認が通過しただけで、FFmpeg license texts / source archive / PySide6確認未完了を無視してMS18 closeout A判定にしてしまう。

対策:
B6残課題はcloseout判定で必ず別項目として確認する。P2が残る場合、A判定にしない。

### 13.5 MMDモデル固有差異をツール不具合と誤認する

リスク:
モデル側のモーフ名や見え方の差異を、VMD生成不具合として扱ってしまう。

対策:
固定モーフ対象は `あ / い / う / え / お` とし、モデル固有の見え方はB7の修正対象にしない。

## 14. Codex 実装時の注意

- 作業開始時に `docs/MS17_and_Beyond_Index.md` を読む。
- コマンドは1つずつ実行し、並列実行しない。
- shell pipelineやコマンド連結を避ける。
- `docs/repo_milestone.md` や `docs/Version_Control.md` は必要箇所だけ読む。
- B7は原則として確認・記録・文書同期であり、コード変更は行わない。
- MMD本体の不具合調査やモデル固有調整に踏み込まない。
- package作成・GitHub Release公開・installer作成は行わない。
- B6のlicense / package P2をB7で勝手に解消しようとしない。
- 実MMD確認をユーザー手動結果に依存する場合は、そのことを明記する。
- テスト未実行の場合は理由を明記する。

## 15. 実施結果 / Closeout

### 15.1 Codex側準備

2026-07-03 に `feature/MS18` 上でB7を開始し、実MMD確認用の一時生成物を用意した。

```text
VMD: C:\tmp\autolip_ms18_b7\ms18_b7_sample_input2.vmd
MMD用WAV: C:\tmp\autolip_ms18_b7\ms18_b7_sample_input2_mmd.wav
```

生成時の確認結果:

- VMD出力: 成功
- VMDサイズ: `23281` bytes
- vowel / timeline: `272`
- MMD用WAV出力: 成功
- MMD用WAV仕様: `pcm_s16le / 44100Hz / 2ch`
- MMD用WAV長: `40.459` 秒
- 確認素材: 既存 `sample/` 由来のローカル検証用素材

`sample/` はB6で出典・ライセンス・配布用途説明が未確定としたため、この生成物はローカル確認用であり、release証跡や同梱可否判断の根拠にはしない。

### 15.2 自動テスト

以下を実行し、MMD用WAV出力関連の既存回帰が通ることを確認した。

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_ms17_b7_mmd_wav_export.py tests\test_ms17_b7_mmd_wav_failure_cleanup.py tests\test_ms17_b7_mmd_wav_overwrite_confirm.py
```

結果:

- `10 passed`

### 15.3 ユーザー手動確認結果

ユーザーから、実MMD確認について以下の報告を受けた。

```text
ユーザー確認通過。問題無し。
```

記録:

- MMD確認実施者: ユーザー
- 確認日: 2026-07-03
- 使用MMD: ユーザー環境。バージョン未申告。
- 使用モデル: ユーザー環境。モデル名未申告。
- VMD: Codex側で用意したB7確認用VMD、またはユーザー環境で生成した同等の確認用VMD。
- MMD用WAV: Codex側で用意したB7確認用MMD用WAV、またはユーザー環境で生成した同等の確認用WAV。
- VMD読み込み: 通過報告あり。
- WAV読み込み: 通過報告あり。
- 再生: 通過報告あり。
- リップ同期: 問題なし報告あり。
- 問題: なし。
- 判定: B7の実MMD確認は通過。

使用MMDバージョンとモデル名は未申告のため、本書では確認できた事実としてはユーザー手動確認通過のみを記録する。

### 15.4 README / readme反映要否

ユーザー確認で手順不足、ファイル名問題、読み込みエラー、再生エラーは報告されていない。
そのため、B7では `README.md` / `readme_mmdautolip.txt` の追加修正は不要と判断する。

### 15.5 MS18 closeout判定

MS18-B7の受け入れ条件は満たした。

MS18全体のcloseout判定は、以下とする。

```text
A. MS18 closeout OK。package 化へ進める。
```

理由:

- 実MMDでのVMD / MMD用WAV読み込み・再生・リップ同期目視確認は、ユーザー確認通過として記録された。
- B7内でP1 / P2の実MMD問題は報告されていない。
- B6由来のpackage化前P2は、2026-07-03のユーザー判断によりクリア扱いとした。
- package化を止める未解決P1 / P2は残っていない。

B6由来のpackage化前P2としてクリア扱いにした項目:

- `FFmpeg\bin\` がGit追跡対象であり、GitHub generated Source code ZIP / tar.gzにもFFmpeg実体が含まれる。
- FFmpeg個別のlicense texts / COPYING相当ファイルが未確定。
- PyInstaller xref上の `PySide6` 参照について、最終成果物への混入有無・license影響確認が未完了。

`sample/` は出典・ライセンス・用途説明が確定するまで、実行用ZIPから除外する方針を維持する。

### 15.6 MS18 CloseOut

2026-07-03 にMS18をCloseOutした。

- CloseOut判定: A
- B1〜B7: 完了
- 実MMD確認: ユーザー確認通過・問題なし
- B6由来P2: ユーザー判断によりクリア扱い
- 次作業: MS19-B4 GUI Entry Point and State Handling の実装前チェック / 実装、またはMS18成果を前提にしたpackage / release作業
