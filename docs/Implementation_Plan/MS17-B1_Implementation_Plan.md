# MS17-B1 Implementation Plan

## 1. 文書情報

- Project: MMD_AutoLipTool
- Milestone: MS17
- Block: MS17-B1
- Block name: Repo / MS16 closeout 後状態確認 + MS17開始条件整理
- Target branch: `feature/MS17`
- Output path: `docs/Implementation_Plan/MS17-B1_Implementation_Plan.md`
- Target GUI: wxPython
- Target environment: Windows 11
- IDE: Google Antigravity
- Coding AI: Gemini 3.1 Pro
- Shell: Windows PowerShell
- 作業種別: 状態確認のみ
- 実装変更: 禁止
- テスト実行: なし

## 2. 背景

MS16では、wxPython主系への一本化、Qt / PySide6系排除、Preview変形台形表示復元、Preview shape data contract固定、RightPane基盤、母音イベント選択下地、MS16 closeout docs整備までを扱った。

MS17では、wav / mp3 / m4a 入力対応、FFmpeg / ffprobe 接続、解析用WAV生成、MMD用WAV同時出力、音声変換系エラー処理へ進む。

ただし、MS17の実装に入る前に、MS16 closeout後のrepo状態が本当に整っているかを確認する必要がある。特に、以下はMS17開始前に確認が必要である。

- MS16-B1〜B7がrepo上に反映・コミットされているか
- README / docs / repo_milestone / Version_Control がMS16完了状態と矛盾していないか
- Qt / PySide6 / shiboken6 / 旧 `src/gui` 参照が戻っていないか
- `preview_transform.py` が `src/core/preview_transform.py` にあるか
- RightPane / Preview shape / 選択下地関連のテストが存在するか
- MS17対象である音声拡張がMS16実装済み扱いされていないか
- FFmpeg同梱有無が未確定なのにREADMEやdocsで断定されていないか
- `.agent/skills/build-packaging-verification/SKILL.md` の文字化け修正が反映済みか

MS17-B1では、これらを確認するだけに留める。ファイル修正、実装、docs補正、テスト実行は行わない。

## 3. 目的

MS17-B1の目的は、MS17実装に入る前のrepo状態を確認し、MS17-B2以降に進めるかどうかを判断することである。

具体的には、以下を明らかにする。

1. `feature/MS17` branch の現在状態
2. MS16 closeout成果の反映状況
3. README / docs の整合状態
4. Qt / PySide6 再混入の有無
5. MS17対象項目が誤ってMS16実装済み扱いされていないか
6. FFmpeg / ffprobe / MMD用WAV関連記述の先走り有無
7. MS17-B2へ進める状態か
8. 進めない場合、先に補正すべき項目

## 4. In Scope

MS17-B1で行う作業は以下に限定する。

- `feature/MS17` branch の確認
- 作業ツリー状態の確認
- 最新commit履歴の確認
- staged / unstaged diff の確認
- MS16-B1〜B7関連文書の存在確認
- MS16 closeout記録の確認
- READMEの現在地確認
- `docs/Version_Control.md` の確認
- `docs/repo_milestone.md` の確認
- MS16 / MS17関連docsの整合確認
- Qt / PySide6 / shiboken6 / 旧 `src/gui` 参照の検索
- `src/core/preview_transform.py` の存在確認
- RightPane / Preview shape / 選択下地関連testの存在確認
- MS17対象項目がMS16実装済み扱いされていないか確認
- FFmpeg / ffprobe / mp3 / m4a / MMD用WAV関連記述の現在地確認
- `.agent/skills/build-packaging-verification/SKILL.md` の文字化け確認
- MS17-B2へ進めるかどうかの判定
- 確認結果の報告

## 5. Out of Scope

MS17-B1では以下を行わない。

- コード実装
- ファイル修正
- docs修正
- README修正
- 依存関係変更
- build / spec変更
- テスト追加
- テスト修正
- テスト実行
- FFmpeg / ffprobe接続実装
- mp3 / m4a入力実装
- 解析用WAV生成実装
- MMD用WAV出力実装
- 音声変換系エラー処理実装
- MS17-B2以降の先行実装
- Qt / PySide6系の再導入
- 旧 `src/gui` 系の復活

## 6. 前提条件

- MS17用branchとして `feature/MS17` が発行済みである。
- MS17-B1は `feature/MS17` 上で実施する。
- MS17-B1は状態確認のみであり、ファイル変更は禁止する。
- MS17-B1ではテストを実行しない。
- 全体pytestにはハング可能性が残っている可能性があるため、MS17-B1では実行対象にしない。
- 音声拡張、m4a対応、FFmpeg接続、解析用WAV、MMD用WAVはMS17対象であり、MS16実装済みとして扱わない。
- FFmpeg同梱有無はMS17-B2で整理する。MS17-B1では現状記述の確認に留める。

## 7. 対象ファイル

MS17-B1では、以下のファイル・ディレクトリを確認対象にする。

```text
README.md
requirements.txt
pyproject.toml
build.ps1
MMD_AutoLipTool.spec
NOTICE
THIRD_PARTY_LICENSES.md

docs/Version_Control.md
docs/repo_milestone.md
docs/MS16_Block_Breakdown_for_Antigravity.md
docs/MS16_and_Beyond_Milestone_Map_for_Antigravity.md
docs/MS17_Block_Breakdown_for_Antigravity.md
docs/MMD_Audio_WAV_Compatibility_Specification.md
docs/Error_Handling_Specification.md
docs/Pipeline_Data_Contract_Specification.md
docs/GUI_State_Theme_Specification.md
docs/Security_Safety_Specification.md
docs/Release_Package_Manifest.md
docs/VMD_Output_Specification.md

docs/Implementation_Plan/MS16-B1_Implementation_Plan.md
docs/Implementation_Plan/MS16-B2_Implementation_Plan.md
docs/Implementation_Plan/MS16-B3_Implementation_Plan.md
docs/Implementation_Plan/MS16-B4_Implementation_Plan.md
docs/Implementation_Plan/MS16-B5_Implementation_Plan.md
docs/Implementation_Plan/MS16-B6_Implementation_Plan.md
docs/Implementation_Plan/MS16-B7_Implementation_Plan.md
docs/Implementation_Plan/MS17-B1_Implementation_Plan.md

src/core/preview_transform.py
src/gui_wx/
tests/

.agent/skills/build-packaging-verification/SKILL.md
```

存在しないファイルがある場合は、作成せず、報告に含める。

## 8. 実装方針

MS17-B1は実装Blockではなく、確認Blockである。

Antigravityは、repo状態、docs状態、旧依存混入、MS16完了記録、MS17対象項目の記述状態を確認し、結果を報告する。

ファイル変更は禁止する。明らかな誤字、文字化け、docs矛盾を見つけても、その場では修正しない。修正対象として分類し、MS17-B1報告に記録する。

## 9. 詳細ステップ

### Step 1: branch / 作業ツリー確認

PowerShellで以下を実行する。

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
* 作業ツリーがcleanか
* staged変更がないか
* unstaged変更がないか
* MS16 closeout関連commitが履歴にあるか
* MS17-B1実施前の意図しない差分がないか

現在branchが `feature/MS17` ではない場合は、checkoutしない。まず報告する。

### Step 2: MS16 closeout文書の存在確認

以下の存在を確認する。

```text
docs/MS16_Block_Breakdown_for_Antigravity.md
docs/Implementation_Plan/MS16-B1_Implementation_Plan.md
docs/Implementation_Plan/MS16-B2_Implementation_Plan.md
docs/Implementation_Plan/MS16-B3_Implementation_Plan.md
docs/Implementation_Plan/MS16-B4_Implementation_Plan.md
docs/Implementation_Plan/MS16-B5_Implementation_Plan.md
docs/Implementation_Plan/MS16-B6_Implementation_Plan.md
docs/Implementation_Plan/MS16-B7_Implementation_Plan.md
```

確認すること。

* 各文書が存在するか
* MS16-B1〜B7の目的・完了条件が記録されているか
* B7がcloseout Blockとして記録されているか
* 音声拡張がMS17送りとして明記されているか

存在しない文書がある場合は、作成せず、報告に含める。

### Step 3: README現在地確認

`README.md` を確認する。

確認観点。

* 現在バージョン表記
* MS15 / MS16 / MS17 の表記整合
* GUIがwxPython主系として説明されているか
* 旧PySide6系が現行GUIのように説明されていないか
* 入力がWAV限定なのか、音声ファイル拡張済みなのか
* mp3 / m4a が実装済み扱いされていないか
* FFmpeg / ffprobe 同梱有無が断定されていないか
* MMD用WAV同時出力が実装済み扱いされていないか
* エンドユーザー向け説明として過不足がないか

MS17-B1では修正しない。矛盾があれば報告する。

### Step 4: docs整合確認

以下を確認する。

```text
docs/Version_Control.md
docs/repo_milestone.md
docs/MS16_and_Beyond_Milestone_Map_for_Antigravity.md
docs/MS17_Block_Breakdown_for_Antigravity.md
```

確認観点。

* MS16がcloseout済みとして記録されているか
* MS17が次マイルストーンとして記録されているか
* MS17の範囲が音声拡張として整理されているか
* MS16範囲とMS17範囲が混同されていないか
* MS17-B1〜B9などのBlock構成が記録されているか
* `Version_Control.md` の変更履歴と実際のdocs状態が矛盾していないか

### Step 5: 音声・FFmpeg関連仕様書の確認

以下を確認する。

```text
docs/MMD_Audio_WAV_Compatibility_Specification.md
docs/Error_Handling_Specification.md
docs/Pipeline_Data_Contract_Specification.md
docs/GUI_State_Theme_Specification.md
docs/Security_Safety_Specification.md
docs/Release_Package_Manifest.md
docs/VMD_Output_Specification.md
```

確認観点。

* wav / mp3 / m4a がMS17対象として整理されているか
* FFmpeg / ffprobe がMS17対象として整理されているか
* 解析用WAVとMMD用WAVが区別されているか
* MMD用WAVがMMD互換用途として説明されているか
* 音量正規化、無音トリム、自動フェード、自動ノイズ除去がMS17対象として混入していないか
* 300秒が強制停止ではなく長時間処理確認閾値として扱われているか
* FFmpeg / ffprobe の terminate / kill 方針が記録されているか
* Whisperなど即時停止できない処理のlate callback破棄方針が記録されているか
* MIT License本体とFFmpeg等の第三者ライセンスが混同されていないか
* Release Package Manifest にFFmpeg配置や配布物の扱いが記録されているか

存在しない仕様書がある場合は、作成せず、報告する。

### Step 6: Qt / PySide6 再混入確認

検索で以下を確認する。

```powershell
Select-String -Path .\requirements.txt, .\pyproject.toml, .\README.md -Pattern "PySide6|shiboken6|Qt" -CaseSensitive:$false

Get-ChildItem -Recurse -File .\src, .\tests, .\docs |
  Select-String -Pattern "PySide6|shiboken6|Qt|src/gui" -CaseSensitive:$false
```

確認観点。

* `requirements.txt` に PySide6 / shiboken6 が戻っていないか
* `pyproject.toml` に PySide6 / shiboken6 が戻っていないか
* `src/gui` 旧Qt系コードが復活していないか
* `src/test_gui.py` が復活していないか
* wxPython主系以外のGUI主系が現行扱いされていないか
* docsに過去経緯としてのQt記述がある場合、現行実装と混同されていないか

過去経緯としてのQt記述は即問題扱いしない。現行実装・現行依存として扱われている場合のみ問題として分類する。

### Step 7: preview_transform / Preview shape / RightPane確認

以下を確認する。

```text
src/core/preview_transform.py
src/gui_wx/
tests/
```

確認観点。

* `src/core/preview_transform.py` が存在するか
* wx版Previewが `core.preview_transform` を参照しているか
* 旧 `src/gui/preview_transform.py` を参照していないか
* Preview shape data contract関連テストが存在するか
* RightPane関連テストが存在するか
* 母音イベント選択下地関連テストが存在するか
* 古いPreview / 古い選択状態を残さない設計がテストまたはdocsに記録されているか

MS17-B1ではテスト実行は行わない。存在確認と内容確認に留める。

### Step 8: build / packaging / license関連確認

以下を確認する。

```text
build.ps1
MMD_AutoLipTool.spec
NOTICE
THIRD_PARTY_LICENSES.md
docs/Release_Package_Manifest.md
.agent/skills/build-packaging-verification/SKILL.md
```

確認観点。

* onefile / onedir の記述が矛盾していないか
* FFmpeg同梱前提の記述があるか
* FFmpeg外部導入前提の記述があるか
* READMEとpackaging docsの説明が矛盾していないか
* `NOTICE` にFFmpeg等の第三者配布物への注意があるか
* `THIRD_PARTY_LICENSES.md` にFFmpeg関連の記録があるか
* `.agent/skills/build-packaging-verification/SKILL.md` に文字化けが残っていないか

MS17-B1では修正しない。

### Step 9: MS17-B2へ進めるか判定

確認結果から、以下のどれかで判定する。

```text
A. MS17-B2へ進める
B. MS17-B2へ進めるが、B2内で先にdocs補正が必要
C. MS17-B2へ進む前に、MS16 closeout補修Blockが必要
D. MS17-B2へ進む前に、branch / commit / 作業ツリー整理が必要
```

判定理由を明記する。

## 10. 状態遷移 / データ契約

MS17-B1では、アプリ内部の状態遷移やデータ契約は変更しない。

ただし、確認時には以下の既存契約がdocsまたは実装と矛盾していないか確認する。

### 10.1 MS16までの既存契約

* timing plan が正本である
* Preview shape は timing plan から派生する表示・選択準備用データである
* Preview shape から timing plan を復元しない
* Preview shape を writer input の正本にしない
* RightPane表示は正本ではない
* TEXT / 音声 / パラメータ変更時は timing plan / Preview / VMD保存可能状態 / 選択状態を無効化する
* 古いworker結果は現在結果として扱わない

### 10.2 MS17で追加予定の契約

MS17-B1では未実装だが、次の契約がMS17対象として整理されているか確認する。

* 入力音声はユーザーが選んだ元ファイルである
* 解析用WAVは波形表示・解析・timing plan生成の正本である
* MMD用WAVはMMDに読み込ませるための出力物である
* 解析用WAVとMMD用WAVを混同しない
* VMD出力は引き続きリップモーフキーフレームのみである

## 11. テスト方針

MS17-B1ではテストを実行しない。

理由:

* MS17-B1は状態確認Blockであり、実装変更を伴わない
* 全体pytestにはハング可能性が残っている可能性がある
* テスト実行はB2以降または補修Blockで、目的別に範囲を絞って行う方が安全である

MS17-B1で行うのは、テストファイルの存在確認と、必要に応じた内容確認のみである。

確認対象例:

```text
tests/
tests/test_wx_ms16_b3_right_pane.py
tests/test_wx_ms16_b4_preview_shape.py
tests/test_wx_ms16_b5_preview_contract.py
tests/test_wx_ms16_b6_event_selection_foundation.py
```

実際のファイル名はrepo状態に従う。存在しない場合は、作成せず報告する。

## 12. 受け入れ条件

MS17-B1は、以下を満たしたら完了とする。

* `feature/MS17` branch上で状態確認が行われている
* `git status` / `git branch` / `git log` / diff状態が報告されている
* MS16-B1〜B7の反映状況が確認されている
* README / docs / repo_milestone / Version_Control の整合状態が確認されている
* Qt / PySide6 / shiboken6 / 旧 `src/gui` 再混入有無が確認されている
* `src/core/preview_transform.py` の存在が確認されている
* RightPane / Preview shape / 選択下地関連テストの存在が確認されている
* MS17対象項目がMS16実装済み扱いされていないか確認されている
* FFmpeg / ffprobe / MMD用WAV関連記述の先走り有無が確認されている
* `.agent/skills/build-packaging-verification/SKILL.md` の文字化け状態が確認されている
* MS17-B2へ進めるかどうかが判定されている
* ファイル変更が行われていない
* テスト実行が行われていない

## 13. リスクと対策

### Risk 1: MS16 closeoutが未反映のままMS17実装へ進む

対策:

* B1でMS16-B1〜B7のdocsとcommit履歴を確認する
* 不足があればMS17-B2へ進めず、補修対象として報告する

### Risk 2: READMEがMS15 / MS16 / MS17状態と矛盾している

対策:

* READMEのバージョン・入力形式・FFmpeg・出力説明を確認する
* 修正はB1では行わず、B1報告で分類する

### Risk 3: PySide6 / Qt系が再混入している

対策:

* requirements / pyproject / src / tests / docs を検索する
* 過去経緯としての記述と現行依存を区別して報告する

### Risk 4: FFmpeg同梱有無が未確定なのにdocsで断定されている

対策:

* README / NOTICE / THIRD_PARTY_LICENSES / Release Package Manifest / build docsを確認する
* B2で整理すべき未確定事項として報告する

### Risk 5: 解析用WAVとMMD用WAVの責務が混同される

対策:

* Pipeline / WAV互換仕様 / VMD出力仕様を確認する
* B1では修正せず、B2以降の設計課題として報告する

### Risk 6: 全体pytestがハングする

対策:

* B1ではテストを実行しない
* 必要なテスト方針はB1報告に「B2以降で要確認」として記録する

### Risk 7: MS17用branch名の大小文字差異による作業ミス

対策:

* 本計画では対象branchを `feature/MS17` とする
* Antigravityは必ず `git branch` で現在branchを確認する
* 現在branchが異なる場合は、checkoutせず報告する

## 14. Antigravity 実施時の注意

以下のプロンプトを Antigravity に渡して実施する。

```text
今回は MS17-B1 です。

目的:
MS16 closeout後のrepo状態を確認し、MS17-B2へ進めるかどうかを判定してください。

重要:
- 対象branchは feature/MS17 です。
- 状態確認のみを行ってください。
- 実装・修正・ファイル変更は行わないでください。
- docs補正も行わないでください。
- テストは実行しないでください。
- 何か問題を見つけても、その場で直さず報告してください。

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
requirements.txt
pyproject.toml
build.ps1
MMD_AutoLipTool.spec
NOTICE
THIRD_PARTY_LICENSES.md

docs/Version_Control.md
docs/repo_milestone.md
docs/MS16_Block_Breakdown_for_Antigravity.md
docs/MS16_and_Beyond_Milestone_Map_for_Antigravity.md
docs/MS17_Block_Breakdown_for_Antigravity.md
docs/MMD_Audio_WAV_Compatibility_Specification.md
docs/Error_Handling_Specification.md
docs/Pipeline_Data_Contract_Specification.md
docs/GUI_State_Theme_Specification.md
docs/Security_Safety_Specification.md
docs/Release_Package_Manifest.md
docs/VMD_Output_Specification.md

docs/Implementation_Plan/MS16-B1_Implementation_Plan.md
docs/Implementation_Plan/MS16-B2_Implementation_Plan.md
docs/Implementation_Plan/MS16-B3_Implementation_Plan.md
docs/Implementation_Plan/MS16-B4_Implementation_Plan.md
docs/Implementation_Plan/MS16-B5_Implementation_Plan.md
docs/Implementation_Plan/MS16-B6_Implementation_Plan.md
docs/Implementation_Plan/MS16-B7_Implementation_Plan.md
docs/Implementation_Plan/MS17-B1_Implementation_Plan.md

src/core/preview_transform.py
src/gui_wx/
tests/

.agent/skills/build-packaging-verification/SKILL.md

確認観点:

1. feature/MS17 branch上にいるか
2. 作業ツリーがcleanか
3. staged / unstaged差分がないか
4. MS16-B1〜B7がrepo上に反映・コミットされているか
5. MS16 closeout docsが存在するか
6. READMEがMS16 closeout後の状態と矛盾していないか
7. docs/repo_milestone.md と docs/Version_Control.md がMS16 closeout状態と矛盾していないか
8. 音声拡張 / mp3 / m4a / FFmpeg / MMD用WAV がMS16実装済み扱いされていないか
9. PySide6 / shiboken6 / Qt / 旧 src/gui 参照が現行実装として戻っていないか
10. src/core/preview_transform.py が存在するか
11. RightPane / Preview shape / 選択下地関連のテストが存在するか
12. FFmpeg同梱有無が未確定なのに断定されていないか
13. NOTICE / THIRD_PARTY_LICENSES.md / Release Package Manifest にFFmpeg関連の記述があるか
14. .agent/skills/build-packaging-verification/SKILL.md に文字化けが残っていないか
15. MS17-B2へ進めるかどうか

検索例:

Select-String -Path .\requirements.txt, .\pyproject.toml, .\README.md -Pattern "PySide6|shiboken6|Qt" -CaseSensitive:$false

Get-ChildItem -Recurse -File .\src, .\tests, .\docs |
  Select-String -Pattern "PySide6|shiboken6|Qt|src/gui" -CaseSensitive:$false

注意:
- 過去経緯としてのQt記述は即問題扱いしないでください。
- 現行依存、現行実装、現行GUIとして扱われている場合のみ問題として分類してください。
- 存在しない文書があっても作成しないでください。
- 明らかな誤字や文字化けがあっても修正しないでください。
- テストは実行しないでください。

完了報告では、以下を必ず分けてください。

1. 確認したbranch / commit
2. 作業ツリー状態
3. staged / unstaged差分の有無
4. MS16-B1〜B7の反映状況
5. README / docs の整合状態
6. PySide6 / Qt / shiboken6 / 旧 src/gui 再混入有無
7. preview_transform.py の配置確認
8. RightPane / Preview shape / 選択下地関連テストの存在確認
9. MS17送り項目が実装済み扱いされていないか
10. FFmpeg / ffprobe / MMD用WAV関連記述の状態
11. .agent/skills/build-packaging-verification/SKILL.md の文字化け確認
12. MS17-B2へ進めるかどうか
13. MS17-B2前に補正すべき項目
14. 今回変更したファイルがないこと
15. 今回テストを実行していないこと
```

## 15. 完了報告テンプレート

Antigravityは、完了時に以下の形式で報告する。

```text
MS17-B1 完了報告

1. 確認したbranch / commit
- branch:
- latest commit:

2. 作業ツリー状態
- git status:
- staged diff:
- unstaged diff:

3. MS16-B1〜B7の反映状況
- B1:
- B2:
- B3:
- B4:
- B5:
- B6:
- B7:

4. README / docs の整合状態
- README:
- Version_Control:
- repo_milestone:
- MS16 / MS17関連docs:

5. PySide6 / Qt / shiboken6 / 旧 src/gui 再混入有無
- requirements.txt:
- pyproject.toml:
- src:
- tests:
- docs:

6. preview_transform.py の配置確認
- src/core/preview_transform.py:
- 旧 src/gui/preview_transform.py 参照:

7. RightPane / Preview shape / 選択下地関連テストの存在確認
- RightPane:
- Preview shape:
- Preview contract:
- Event selection foundation:

8. MS17送り項目の扱い
- mp3:
- m4a:
- FFmpeg / ffprobe:
- 解析用WAV:
- MMD用WAV:

9. FFmpeg / ライセンス / 配布関連記述
- README:
- NOTICE:
- THIRD_PARTY_LICENSES.md:
- Release Package Manifest:
- build.ps1 / spec:

10. .agent skill文字化け確認
- .agent/skills/build-packaging-verification/SKILL.md:

11. MS17-B2へ進めるか
- 判定:
- 理由:

12. MS17-B2前に補正すべき項目
- P1:
- P2:
- P3:

13. 今回の変更
- 変更ファイル: なし
- テスト実行: なし
```

## 16. 判定基準

MS17-B1の最終判定は以下から選ぶ。

### A. MS17-B2へ進める

条件:

* `feature/MS17` 上で作業ツリーがclean
* MS16 closeout記録が概ね整合
* PySide6 / Qt 再混入なし
* MS17対象項目がMS16実装済み扱いされていない
* B2で扱うべきFFmpeg方針整理に進める

### B. MS17-B2へ進めるが、B2冒頭でdocs補正が必要

条件:

* 実装状態に重大な問題はない
* ただしREADMEやdocsにFFmpeg / MS17範囲の表現ゆれがある
* B2で方針整理と同時に補正すればよい

### C. MS17-B2へ進む前に、MS16 closeout補修Blockが必要

条件:

* MS16-B7 closeoutが未反映
* MS16完了扱いと実装・docsが矛盾
* MS17対象項目がMS16実装済み扱いされている
* PySide6 / Qt再混入など、MS16完了条件に関わる問題がある

### D. MS17-B2へ進む前に、branch / commit / 作業ツリー整理が必要

条件:

* 現在branchが `feature/MS17` ではない
* 未コミット差分がある
* staged差分がある
* MS17-B1開始前に意図不明の変更がある

## 17. MS17-B2への引き継ぎ条件

MS17-B2へ進む場合、B1報告から以下を引き継ぐ。

* FFmpeg / ffprobe の現状記述
* 同梱方式に見える記述
* 外部導入方式に見える記述
* READMEとdocsの矛盾
* NOTICE / THIRD_PARTY_LICENSES / Release Package Manifest の不足
* build.ps1 / spec のFFmpeg配置記述
* MS17-B2で決めるべき未確定事項

MS17-B2では、これらをもとに FFmpeg / ffprobe 接続方式・ライセンス・配布方針を整理する。

## 18. 変更履歴

### 2026-05-13 / MS17-B1 完了反映

* `MS17-B1: Repo / MS16 closeout 後状態確認 + MS17開始条件整理` を完了。
* 各種確認項目（PySide6排除の維持、MS16完了状態の確認など）をパス。
* `src/main.py` のコメントのみ実態に合わせて修正し、本 Block をクローズした。
