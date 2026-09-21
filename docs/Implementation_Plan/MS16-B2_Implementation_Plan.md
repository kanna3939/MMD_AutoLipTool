# MS16-B2 Implementation Plan

## 1. 文書情報

- 文書名: `MS16-B2 Implementation Plan`
- 推奨ファイル名: `docs/Implementation_Plan/MS16-B2_Implementation_Plan.md`
- 対象プロジェクト: `MMD_AutoLipTool`
- 対象リポジトリ: `https://github.com/kanna3939/MMD_AutoLipTool`
- 対象マイルストーン: `MS16`
- 対象Block: `MS16-B2`
- Block名: `Qt / PySide6 Removal`
- 主対象GUI: `wxPython`
- 旧GUI系: `Qt / PySide6`
- 主対象読者: `Google Antigravity / Gemini 3.1 Pro`
- 主開発環境: `Windows 11`
- Shell: `Windows PowerShell`
- Python: repo の現在要件に従う
- 仮想環境: `.venv`
- 作成日: 2026-05-01
- 文書種別: Implementation Plan
- 実装区分: `scoped implementation`

---

## 2. 背景

MS16-B1 の現状調査により、以下が確認された。

```text
- 現在の作業branchは feature/MS16
- git状態はクリーン
- pyproject.toml / requirements.txt に PySide6 系依存が残存
- pyproject.toml の packages.find.include に旧 "gui" パッケージが残存
- MMD_AutoLipTool.spec / build.ps1 に Qt 系DLL混入リスクが残存
- src/gui/ 配下に旧Qt/PySide版コードが残存
- src/test_gui.py に PySide6 import が残存
- preview_transform.py は旧 src/gui/ 配下に存在するが、wx版からも参照されている
- wx版 Preview は control_points が無い場合にリボン型表示へフォールバックしやすい
````

MS16-B2では、Qt / PySide6 系依存と旧GUIコードを削除し、wxPython主系へ一本化する。

ただし、`preview_transform.py` は wx版Previewでも必要な共通変換ロジックであるため、旧 `src/gui/` を削除する前に `src/core/` などの共通領域へ救出する。

---

## 3. 目的

MS16-B2の目的は、以下を安全に実施することである。

```text
- Qt / PySide6 系依存を requirements.txt から削除する
- Qt / PySide6 系依存を pyproject.toml から削除する
- pyproject.toml の package include から旧 gui パッケージを外す
- preview_transform.py を旧 src/gui/ から共通領域へ移動する
- wxPython主系の import path を新しい preview_transform の場所へ修正する
- 旧 src/gui/ を削除する
- 旧 src/test_gui.py を削除する
- PySide6 / shiboken6 / QtWidgets / QtCore / QtGui の実行コード上の残存をなくす
- PyInstaller spec / build.ps1 のQt混入リスクを取り除く
```

このBlockの完了後、repo上の主GUIは `src/gui_wx/` に一本化される。

---

## 4. In Scope

MS16-B2では以下を対象とする。

```text
- requirements.txt の PySide6 / PySide6_Addons / PySide6_Essentials / shiboken6 削除
- pyproject.toml の PySide6 系依存削除
- pyproject.toml の packages.find.include から旧 gui を削除
- preview_transform.py の救出・移動
- preview_transform import path の修正
- 旧 src/gui/ の削除
- 旧 src/test_gui.py の削除
- MMD_AutoLipTool.spec の Qt / PySide6 明示収集設定の削除
- build.ps1 の Qt / PySide6 前提記述の削除
- PySide6 / shiboken6 / Qt import 残存確認
- wxPython主系の軽量import確認
- compileall または対象テストによる破損確認
```

---

## 5. Out of Scope

MS16-B2では以下を行わない。

```text
- Preview変形台形表示の本格復元
- Preview shape data contract の修正
- control_points 生成契約の修正
- writer shape ロジックの変更
- 右ペインGUI追加
- 母音イベント選択下地
- mp3入力対応
- m4a入力対応
- FFmpeg / ffprobe 接続
- 解析用WAV生成
- MMD用WAV同時出力
- MMD互換WAV検証
- 音声変換系エラー処理
- 配布ビルドcloseout
```

特に、B1で確認された「Previewがリボン型表示になりやすい問題」は、MS16-B4 / MS16-B5 の対象であり、MS16-B2では修正しない。

---

## 6. 前提条件

### 6.1 作業前提

```text
- 作業branch: feature/MS16
- 作業開始時点で git status がクリーンであること
- MS16-B1の調査結果を前提にすること
- 現行GUI主系は src/gui_wx/ であること
```

### 6.2 重要な前提

`src/gui/preview_transform.py` は旧GUI配下にあるが、wx版からも参照されている。

したがって、旧 `src/gui/` を削除する前に、必ず次を行う。

```text
1. preview_transform.py の内容を確認する
2. 移動先を確認する
3. src/core/preview_transform.py 等へ移動する
4. wx側 import を修正する
5. import確認を行う
6. その後に旧 src/gui/ を削除する
```

この順序を守らない場合、wxPython主系のPreviewが壊れる可能性がある。

---

## 7. 対象ファイル

MS16-B2で変更対象となる候補は以下である。

```text
requirements.txt
pyproject.toml
MMD_AutoLipTool.spec
build.ps1

src/gui/preview_transform.py
src/core/preview_transform.py
src/gui_wx/preview_panel.py
src/gui_wx/main_frame.py
src/gui_wx/placeholder_panels.py
src/gui_wx/app_controller.py

src/gui/
src/test_gui.py

README.md
docs/Version_Control.md
docs/repo_milestone.md
```

ただし、README / docs の更新は、B2の変更により現行記述が明確に不正確になる場合に限る。
MS16 / MS17 境界補正の本格整理は MS16-B7 で扱う。

---

## 8. 実装方針

### 8.1 基本方針

MS16-B2では、旧Qt/PySide6系を削除し、wxPython主系へ一本化する。

基本方針は以下。

```text
- Qt / PySide6 を再導入しない
- wxPython主系を維持する
- preview_transform.py は削除せず共通領域へ移動する
- 旧 src/gui/ は preview_transform.py 救出後に削除する
- src/test_gui.py は旧PySide6系テストとして削除する
- Preview表示仕様そのものは変更しない
- writer shape仕様は変更しない
```

### 8.2 preview_transform.py の移動方針

推奨移動先は以下。

```text
src/core/preview_transform.py
```

理由:

```text
- Preview data はGUI表示専用ではなく、timing plan から派生する共通変換データである
- wx版Previewと将来のテストから参照しやすい
- 旧Qt/PySide版 src/gui/ への依存を切れる
```

ただし、作業時点で `src/core/preview_transform.py` が既に存在する場合は、上書きしない。
既存ファイルがある場合は、内容を確認し、重複・差分・import先を整理したうえで最小変更に留める。

### 8.3 旧 src/gui/ の削除方針

B1報告では、旧Qt/PySide版コードが `src/gui/` 配下に完全な形で残存している。

MS16-B2では、原則として以下を行う。

```text
- preview_transform.py を救出する
- 参照先を修正する
- import確認後、旧 src/gui/ を削除する
```

旧 `src/gui/` を残すと、Antigravityが誤参照する可能性があるため、完全削除を推奨する。

### 8.4 docs更新方針

B2では、以下の最小更新のみ許可する。

```text
- Qt / PySide6 が現行依存であるかのような記述の削除
- 現行GUI主系が wxPython であることの明確化
- B2実施記録として Version_Control / repo_milestone へ短い記録追加
```

ただし、次の補正はB7へ送る。

```text
- docs/MMD_Audio_WAV_Compatibility_Specification.md の MS16/MS17 表記整理
- MS17音声拡張の詳細整理
- MS16 closeout記録
```

---

## 9. 詳細ステップ

### Step 1: 作業前git状態確認

```powershell
git status
git branch
git log --oneline -n 10
git diff --stat
git diff --name-only
```

確認すること。

```text
- branch が feature/MS16 であること
- 作業前に予期しない差分がないこと
- 既知差分がある場合は内容を報告すること
```

### Step 2: preview_transform.py の参照確認

移動前に、現行の参照箇所を確認する。

```powershell
Get-ChildItem -Recurse -File |
  Where-Object { $_.Extension -in ".py", ".toml", ".txt", ".md" } |
  Select-String -Pattern "preview_transform"
```

確認すること。

```text
- src/gui/preview_transform.py の存在
- src/gui_wx/ からの import
- tests/ からの import
- docs内の参照
```

### Step 3: preview_transform.py を共通領域へ移動

推奨コマンド。

```powershell
git mv .\src\gui\preview_transform.py .\src\core\preview_transform.py
```

ただし、移動先ファイルが既に存在する場合は、上記を実行しない。

既に存在する場合は、以下を確認する。

```powershell
Get-Item .\src\core\preview_transform.py
```

そのうえで、重複・差分を確認し、必要最小限の統合に留める。

### Step 4: import path 修正

旧import例。

```python
from gui.preview_transform import ...
```

または類似の旧参照を、新しい共通領域へ修正する。

推奨例。

```python
from core.preview_transform import ...
```

または現行package構成に従い、既存の `core` import 形式と揃える。

修正対象候補。

```text
src/gui_wx/preview_panel.py
src/gui_wx/main_frame.py
src/gui_wx/placeholder_panels.py
tests/
```

修正後、再度参照確認を行う。

```powershell
Get-ChildItem -Recurse -File |
  Where-Object { $_.Extension -in ".py", ".toml", ".txt", ".md" } |
  Select-String -Pattern "gui.preview_transform|src.gui.preview_transform|preview_transform"
```

docs内の単なる説明は残ってもよいが、実行コードの旧importは残さない。

### Step 5: 軽量import確認

pytest全体はB1でハングしたため、まず軽量確認を行う。

例。

```powershell
.\.venv\Scripts\python.exe -m compileall .\src
```

可能であれば、対象import確認を行う。

```powershell
.\.venv\Scripts\python.exe -c "import core.preview_transform"
```

現行repoのimport rootにより上記が失敗する場合は、既存テストや既存起動方法に合わせて確認する。
失敗した場合は、import rootの問題か実装破損かを区別して報告する。

### Step 6: 旧 src/gui/ の削除

preview_transform.py の救出とimport修正が完了した後、旧 `src/gui/` を削除する。

```powershell
git rm -r .\src\gui
```

削除前に `src/gui/` 内に救出すべきファイルが残っていないか確認する。

```powershell
Get-ChildItem .\src\gui -Recurse -File
```

B2では、旧Qt/PySide版のGUIコードは削除対象である。
ただし、削除後にwx主系が壊れないことを確認する。

### Step 7: 旧 src/test_gui.py の削除

B1報告では `src/test_gui.py` に PySide6 import が残存している。

旧PySide6 GUI用の手動テストまたは試験コードと判断できる場合、削除する。

```powershell
git rm .\src\test_gui.py
```

削除前に、wx主系や現行テストから参照されていないことを確認する。

```powershell
Get-ChildItem -Recurse -File |
  Where-Object { $_.Extension -in ".py", ".md", ".toml", ".txt" } |
  Select-String -Pattern "test_gui"
```

### Step 8: requirements.txt のPySide6系依存削除

以下を削除する。

```text
PySide6
PySide6_Addons
PySide6_Essentials
shiboken6
```

バージョン表記がある場合も削除する。

wxPython依存は残す。

削除後確認。

```powershell
Select-String -Path .\requirements.txt -Pattern "PySide6|shiboken6|Qt"
```

実行コードに必要な依存を誤って消していないか確認する。

### Step 9: pyproject.toml のPySide6系依存削除

以下を削除する。

```text
PySide6
PySide6_Addons
PySide6_Essentials
shiboken6
```

また、`packages.find.include` から旧 `gui` パッケージを外す。

維持するべきもの。

```text
gui_wx
core
vmd_writer
その他現行repoで必要なpackage
```

削除後確認。

```powershell
Select-String -Path .\pyproject.toml -Pattern "PySide6|shiboken6|Qt|gui"
```

`gui_wx` は残ってよい。
旧 `gui` だけを除外する。

### Step 10: spec / build.ps1 のQt混入リスク削除

以下を確認する。

```powershell
Select-String -Path .\MMD_AutoLipTool.spec, .\build.ps1 -Pattern "PySide6|shiboken6|Qt|gui"
```

存在する場合、以下を削除または修正する。

```text
- PySide6 collect_all
- Qt DLL 明示収集
- Qt resource 明示収集
- 旧 gui パッケージ収集
- PySide6 前提の hiddenimports
```

ただし、PyInstaller全体の再設計は行わない。
MS16-B2では Qt / PySide6 混入リスクの除去に限定する。

### Step 11: PySide6 / Qt 残存確認

実行コード上の残存を確認する。

```powershell
Get-ChildItem -Recurse -File |
  Where-Object { $_.Extension -in ".py", ".toml", ".txt", ".ps1", ".spec", ".md" } |
  Select-String -Pattern "from PySide6|import PySide6|QtWidgets|QtCore|QtGui|shiboken6"
```

分類して報告する。

```text
- 実行コード内: 残っていてはならない
- tests内: 原則残っていてはならない
- docs内: 履歴や旧GUI説明として残る場合は可。ただし現行依存と誤認される記述は修正候補
```

### Step 12: 軽量テスト

B1で全体pytestがハングしたため、B2では以下を優先する。

```powershell
.\.venv\Scripts\python.exe -m compileall .\src
```

可能であれば、GUI非依存または対象範囲のテストを実行する。

例。

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_wx_ms14_b2_state.py
.\.venv\Scripts\python.exe -m pytest tests\test_wx_ms15_b5_state_theme.py
```

実際のテストファイル名は現行repoに存在するものを使う。

全体pytestは、ハング回避策がある場合のみ実行する。

```powershell
.\.venv\Scripts\python.exe -m pytest
```

全体pytestが再びハングする場合は、強制終了し、以下を報告する。

```text
- どの段階でハングしたか
- GUI初期化 / ダイアログ / wx App 起因か
- B2変更による失敗か、既存のテスト実行環境問題か
```

### Step 13: 最終git差分確認

```powershell
git status
git diff --stat
git diff --name-only
```

確認すること。

```text
- 変更ファイルがB2対象に収まっているか
- preview_transform.py が移動扱いになっているか
- 旧 src/gui/ が削除されているか
- 旧 src/test_gui.py が削除されているか
- requirements / pyproject の変更が意図通りか
- MS17対象の音声拡張変更が混入していないか
```

---

## 10. 状態遷移 / データ契約

MS16-B2では、pipeline のデータ契約やGUI状態遷移は原則変更しない。

### 10.1 変更しない契約

```text
- timing plan を pipeline 正本とする契約
- Preview data は timing plan からの派生物とする契約
- VMD writer input は timing plan からの派生物とする契約
- input identity / job id による古いworker結果破棄
- TEXT / 音声 / パラメータ変更時の結果無効化
```

### 10.2 B2で変わる可能性があるもの

```text
- preview_transform.py の import path
- package include 対象
- 配布対象package
- 依存定義
```

### 10.3 B2で変えてはならないもの

```text
- Preview shape の意味契約
- writer shape の生成ロジック
- VMD出力対象
- GUI操作の状態遷移
- Busy / cancel / late callback discard
```

---

## 11. テスト方針

### 11.1 優先テスト

B2では、まず以下を優先する。

```text
1. PySide6 / Qt 文字列残存確認
2. compileall
3. preview_transform import確認
4. wx主系の対象テスト
5. 可能な範囲のpytest
```

### 11.2 推奨コマンド

```powershell
Get-ChildItem -Recurse -File |
  Where-Object { $_.Extension -in ".py", ".toml", ".txt", ".ps1", ".spec", ".md" } |
  Select-String -Pattern "from PySide6|import PySide6|QtWidgets|QtCore|QtGui|shiboken6"

.\.venv\Scripts\python.exe -m compileall .\src
```

対象テストは、存在するものを選ぶ。

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_wx_ms14_b2_state.py
.\.venv\Scripts\python.exe -m pytest tests\test_wx_ms15_b5_state_theme.py
```

### 11.3 全体pytestの扱い

B1で全体pytestがGUI初期化またはダイアログによりハングしたため、B2では全体pytestを絶対条件にしない。

ただし、実行可能な状態であれば行う。

```powershell
.\.venv\Scripts\python.exe -m pytest
```

ハングした場合は、B2失敗と即断せず、ハング箇所と原因候補を報告する。

---

## 12. 受け入れ条件

MS16-B2の受け入れ条件は以下である。

```text
- requirements.txt から PySide6 / PySide6_Addons / PySide6_Essentials / shiboken6 が削除されている
- pyproject.toml から PySide6 系依存が削除されている
- pyproject.toml の packages.find.include から旧 gui が外れている
- gui_wx は package 対象として維持されている
- preview_transform.py が src/core/ 等の共通領域へ移動されている
- wxPython主系の preview_transform import が新パスへ修正されている
- 旧 src/gui/ が削除されている
- src/test_gui.py が削除されている
- 実行コード内に PySide6 / shiboken6 / QtWidgets / QtCore / QtGui import が残っていない
- MMD_AutoLipTool.spec / build.ps1 に Qt / PySide6 明示収集が残っていない
- compileall または軽量import確認が通る
- MS17対象の音声拡張変更が混入していない
- Preview表示仕様やwriter shape仕様を変更していない
```

---

## 13. リスクと対策

### 13.1 リスク: preview_transform.py を削除してwx版Previewが壊れる

対策:

```text
- 旧 src/gui/ 削除前に必ず preview_transform.py を救出する
- 移動後に import path を修正する
- compileall / import確認を行う
```

### 13.2 リスク: 旧gui削除により参照切れが発生する

対策:

```text
- 削除前に preview_transform 以外の参照を検索する
- 削除後に旧 gui import が残っていないか確認する
- 参照切れはB2内で修正する
```

### 13.3 リスク: PySide6依存を削除してもspec/buildに残る

対策:

```text
- requirements / pyproject だけでなく spec / build.ps1 も確認する
- PySide6 collect / hiddenimports / Qt DLL収集を削除する
```

### 13.4 リスク: docs内のQt履歴記述まで過剰に消す

対策:

```text
- docs内の履歴記述は必要なら残してよい
- 現行依存・現行主系と誤認される記述だけ修正候補にする
- 本格的なdocs整合はB7で扱う
```

### 13.5 リスク: 全体pytestが再ハングする

対策:

```text
- まず compileall と対象テストを行う
- 全体pytestは可能な場合のみ実行する
- ハングした場合は原因候補を報告し、B2変更による破損か環境問題かを切り分ける
```

### 13.6 リスク: B2でPreview shape復元まで始めてしまう

対策:

```text
- B2は依存排除と旧GUI削除に限定する
- control_points生成契約や変形台形表示復元はB4/B5へ送る
```

---

## 14. Antigravity 実装時の注意

Antigravity は以下を厳守すること。

```text
今回は MS16-B2 の scoped implementation です。

目的は、Qt / PySide6 系依存と旧Qt GUIコードを削除し、wxPython主系へ一本化することです。

旧 src/gui/ を削除する前に、必ず src/gui/preview_transform.py を src/core/preview_transform.py 等の共通領域へ移動し、wxPython主系の import path を修正してください。

Preview変形台形表示の復元、Preview shape data contract の修正、writer shape の変更は行わないでください。

mp3 / m4a 入力、FFmpeg / ffprobe、解析用WAV生成、MMD用WAV同時出力は MS17 対象です。MS16-B2では実装しないでください。
```

---

## 15. Antigravity 作業開始用プロンプト

以下を Antigravity に渡す想定とする。

````text
MS16-B2: Qt / PySide6 Removal を実施してください。

今回は scoped implementation です。
MS16-B1の調査結果に基づき、Qt / PySide6 系依存と旧Qt GUIコードを削除し、wxPython主系へ一本化してください。

重要:
- Qt / PySide6 を再導入しないでください。
- wxPython主系を維持してください。
- 旧 src/gui/ を削除する前に、必ず src/gui/preview_transform.py を src/core/preview_transform.py 等の共通領域へ移動してください。
- 移動後、src/gui_wx 側の import path を修正してください。
- preview_transform.py の中身は、B2では原則として移動とimport修正に留め、shape契約の修正は行わないでください。
- Preview変形台形表示の復元はMS16-B4、shape data contractの固定はMS16-B5で扱います。
- mp3 / m4a 入力、FFmpeg / ffprobe、解析用WAV生成、MMD用WAV同時出力はMS17対象です。B2では実装しないでください。

作業開始時に以下を実行してください。

```powershell
git status
git branch
git log --oneline -n 10
git diff --stat
git diff --name-only
````

実施内容:

1. preview_transform.py の参照箇所を確認する
2. src/gui/preview_transform.py を src/core/preview_transform.py 等へ移動する
3. wxPython主系の import path を修正する
4. 旧 src/gui/ を削除する
5. 旧 src/test_gui.py を削除する
6. requirements.txt から PySide6 / PySide6_Addons / PySide6_Essentials / shiboken6 を削除する
7. pyproject.toml から PySide6 系依存を削除する
8. pyproject.toml の packages.find.include から旧 gui を削除する。ただし gui_wx は残す
9. MMD_AutoLipTool.spec / build.ps1 に Qt / PySide6 明示収集があれば削除する
10. PySide6 / shiboken6 / Qt import 残存を確認する
11. compileall または軽量import確認を行う
12. 可能であればGUI非依存または対象テストを実行する

確認コマンド例:

```powershell
Get-ChildItem -Recurse -File |
  Where-Object { $_.Extension -in ".py", ".toml", ".txt", ".ps1", ".spec", ".md" } |
  Select-String -Pattern "from PySide6|import PySide6|QtWidgets|QtCore|QtGui|shiboken6"

.\.venv\Scripts\python.exe -m compileall .\src
```

B1で全体pytestはGUI初期化またはダイアログによりハングしました。
そのため、B2では全体pytestに固執せず、まず compileall、import確認、対象テストを優先してください。
全体pytestを実行して再度ハングした場合は、強制終了し、ハング箇所と原因候補を報告してください。

作業完了時には以下を報告してください。

* 実行したコマンド
* 変更したファイル
* 削除したファイル
* preview_transform.py の移動先
* 修正した import path
* 削除した依存
* pyproject.toml の package include 変更内容
* spec / build.ps1 のQt関連修正有無
* PySide6 / Qt 残存確認結果
* 実行したテストまたは確認
* テスト結果
* 全体pytestを実行したか、実行しなかった場合の理由
* 最終 git diff --stat
* MS17対象の変更が混入していないこと

---

## 16. 完了報告形式

Antigravity は作業完了時に以下の形式で報告する。

```text
## MS16-B2 実装報告

### 1. 実行したコマンド

### 2. 作業前git状態
- branch:
- latest commit:
- working tree:

### 3. 変更したファイル

### 4. 削除したファイル

### 5. preview_transform.py の移動
- 移動前:
- 移動後:
- import修正箇所:

### 6. 依存削除
- requirements.txt:
- pyproject.toml:

### 7. package include変更
- 削除:
- 維持:

### 8. spec / build.ps1 確認
- Qt / PySide6 明示収集:
- 修正有無:

### 9. PySide6 / Qt 残存確認
#### 9.1 実行コード
#### 9.2 tests
#### 9.3 docs
#### 9.4 build/spec

### 10. 確認・テスト結果
- compileall:
- import確認:
- 対象pytest:
- 全体pytest:

### 11. GUI / Theme / Error Handling への影響
- GUI変更有無:
- Theme変更有無:
- Busy / late callback 影響有無:

### 12. 最終git状態
- git diff --stat:
- git diff --name-only:

### 13. MS17対象変更の混入確認
- mp3 / m4a:
- FFmpeg / ffprobe:
- 解析用WAV:
- MMD用WAV:

### 14. 残課題
- B4へ送る項目:
- B5へ送る項目:
- B7へ送るdocs補正:
````

---

## 17. 完了後の次アクション

MS16-B2完了後、通常は以下へ進む。

```text
MS16-B3: GUI Layout Foundation / Right Pane 基盤
```

ただし、以下の場合はB3へ進む前に補修を行う。

```text
- wxPython主系がimportできない
- preview_transform.py の参照切れが残っている
- PySide6 import が実行コードに残っている
- requirements / pyproject にPySide6系が残っている
- 旧 src/gui/ の削除後に参照切れが発生している
```

MS16-B2では、Previewがリボン型表示になりやすい問題は残ってよい。
その修正は MS16-B4 / MS16-B5 で扱う。

---

## 18. 変更履歴

### 2026-05-01 / 初版

* MS16-B1調査結果を踏まえ、MS16-B2の実装プランを作成。
* `preview_transform.py` を旧 `src/gui/` から共通領域へ救出してから旧GUIを削除する順序を明記。
* PySide6 / shiboken6 依存削除、旧 `src/gui/` 削除、旧 `src/test_gui.py` 削除、package include整理、spec / build.ps1確認をIn Scopeに定義。
* Preview変形台形表示復元、shape data contract修正、音声拡張、FFmpeg / MMD用WAV対応をOut of Scopeに明記。
* B1で全体pytestがハングしたため、B2ではcompileall、import確認、対象テストを優先する方針を定義。
