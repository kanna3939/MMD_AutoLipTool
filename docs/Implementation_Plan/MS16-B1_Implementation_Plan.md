# MS16-B1 Implementation Plan

## 1. 文書情報

- 文書名: `MS16-B1 Implementation Plan`
- 推奨ファイル名: `docs/Implementation_Plan/MS16-B1_Implementation_Plan.md`
- 対象プロジェクト: `MMD_AutoLipTool`
- 対象リポジトリ: `https://github.com/kanna3939/MMD_AutoLipTool`
- 対象マイルストーン: `MS16`
- 対象Block: `MS16-B1`
- Block名: `Repo / Dependency / Preview Shape Contract 現状調査`
- 主対象GUI: `wxPython`
- 旧GUI系: `Qt / PySide6` は再導入しない
- 主対象読者: `Google Antigravity / Gemini 3.1 Pro`
- 主開発環境: `Windows 11`
- Shell: `Windows PowerShell`
- Python: repo の現在要件に従う
- 仮想環境: `.venv`
- 作成日: 2026-05-01
- 文書種別: Implementation Plan
- 実装区分: `調査のみ / コード変更なし`

---

## 2. 背景

MS15 までで、wxPython 主系における以下の機能は closeout 済みである。

```text
MS13: wxPython 主系の起動骨格・UI基盤
MS14: 既存機能 parity 回復
MS15: 波形表示 / Preview / 再生 / Viewport / Theme / State 統合
MS15: closeout 済み
````

MS16では、次の段階として以下を扱う。

```text
- wxPython主系への一本化
- Qt / PySide6 系依存の排除
- Preview変形台形表示の復元
- 将来拡張に備えた右ペイン型GUI基盤
- Preview shape data contract の整理
- 母音イベント選択の下地
```

ただし、MS16-B1では実装を行わない。

MS16-B1の役割は、実装に入る前に repo の現在状態、依存関係、旧GUI残存、Preview表示、VMD writer の shape 契約、docs上のMS16/MS17境界を確認し、後続Blockの安全な実装範囲を明確にすることである。

---

## 3. 目的

MS16-B1の目的は、以下の現状を調査・整理することである。

```text
- 現在の git 状態
- 現在の branch / 最新コミット
- 未コミット差分・未追跡ファイル
- Qt / PySide6 系依存の残存箇所
- 旧 src/gui/ の状態
- wxPython主系の現行構成
- Preview ribbon 表示の生成箇所
- VMD writer の shape 生成契約
- Preview と writer の shape 解釈の不一致点
- 右ペインGUI基盤追加に必要な対象ファイル候補
- MS16 / MS17 境界に関する docs の矛盾点
- MS16-B2以降で変更すべきファイル候補
```

本Blockの成果物は、コード差分ではなく、**調査報告**である。

---

## 4. In Scope

MS16-B1では、以下を対象とする。

```text
- git status / branch / log / diff の確認
- default branch / current branch の確認
- 最新コミットの確認
- 未コミット差分の確認
- 未追跡ファイルの確認
- requirements.txt の確認
- pyproject.toml の確認
- MMD_AutoLipTool.spec の確認
- build.ps1 の確認
- src/gui/ 旧Qt/PySide系コードの確認
- src/gui_wx/ wxPython主系コードの確認
- PySide6 / shiboken6 / Qt import 残存確認
- Qt backend 前提の matplotlib 設定確認
- src/gui_wx/preview_panel.py の確認
- src/core/preview_transform.py の確認
- src/vmd_writer/ の確認
- tests/ のQt依存テスト確認
- docs/ のMS16/MS17境界確認
- README.md の現行記述確認
```

---

## 5. Out of Scope

MS16-B1では、以下を行わない。

```text
- コード変更
- docs修正
- 依存削除
- ファイル削除
- ファイル移動
- 旧 src/gui/ の削除または退避
- requirements.txt の編集
- pyproject.toml の編集
- MMD_AutoLipTool.spec の編集
- build.ps1 の編集
- Preview描画変更
- GUIレイアウト変更
- 右ペイン追加
- shape metadata 実装
- 母音イベント選択実装
- テスト修正
- 新規テスト追加
- mp3 / m4a 入力対応
- FFmpeg / ffprobe 接続
- 解析用WAV生成
- MMD用WAV同時出力
```

MS16-B1では、MS17対象の音声拡張を実装しない。

---

## 6. 前提条件

### 6.1 開発前提

```text
- Windows 11
- Google Antigravity
- Gemini 3.1 Pro
- Windows PowerShell
- 仮想環境 .venv
- GUI主系は wxPython
```

### 6.2 マイルストーン前提

MS16では以下を対象とする。

```text
- wxPython一本化
- Qt / PySide6 排除
- Preview変形台形表示復元
- 右ペインGUI基盤
- Preview shape data contract
- 母音イベント選択下地
```

MS17へ送るもの。

```text
- wav / mp3 / m4a 入力対応
- m4a対応
- FFmpeg / ffprobe 接続
- 解析用WAV生成
- MMD用WAV同時出力
- MMD互換WAV検証
- 音声変換系エラー処理
```

### 6.3 ローカル差分に関する前提

前セッションで、以下のSkillはローカル修正済みだが、単体ではコミットしない方針とされた。

```text
.agent/skills/build-packaging-verification/SKILL.md
```

MS16-B1では、この差分が存在していても、それだけで異常扱いしない。

ただし、以下は必ず報告する。

```text
- 変更済みファイルとして検出されたか
- 文字化け修正済みと思われるか
- MS16-B7またはまとまったdocs/skills整備で扱うべきか
```

---

## 7. 対象ファイル

MS16-B1で確認する主な対象ファイル候補は以下である。

```text
requirements.txt
pyproject.toml
MMD_AutoLipTool.spec
build.ps1
README.md

docs/MS16_Block_Breakdown_for_Antigravity.md
docs/MS16_and_Beyond_Milestone_Map_for_Antigravity.md
docs/Specification_Prompt_v4.md
docs/GUI_State_Theme_Specification.md
docs/Pipeline_Data_Contract_Specification.md
docs/VMD_Output_Specification.md
docs/Error_Handling_Specification.md
docs/Security_Safety_Specification.md
docs/MMD_Audio_WAV_Compatibility_Specification.md
docs/Release_Package_Manifest.md
docs/repo_milestone.md
docs/Version_Control.md

src/gui/
src/gui_wx/
src/gui_wx/main_frame.py
src/gui_wx/app_controller.py
src/gui_wx/ui_state.py
src/gui_wx/theme.py
src/gui_wx/preview_panel.py
src/gui_wx/waveform_panel.py
src/core/preview_transform.py
src/core/pipeline.py
src/vmd_writer/
tests/
.agent/skills/
```

対象ファイルは現行repo構成に従い、存在しない場合は「存在しない」と報告する。

---

## 8. 実装方針

MS16-B1では実装しない。

Antigravity は、repo状態と対象ファイルを読み、後続Blockの判断材料を整理する。

### 8.1 変更禁止

以下は禁止する。

```text
- ファイル編集
- 自動整形
- import整理
- 未使用ファイル削除
- 依存削除
- テスト修正
- docs修正
- 旧GUIファイル移動
```

### 8.2 調査観点

主な調査観点は以下である。

```text
1. git状態
2. Qt / PySide6依存
3. 旧GUIコード
4. wxPython主系構成
5. Preview表示構造
6. VMD writer shape契約
7. Preview / writer の不一致点
8. 右ペイン追加候補
9. MS16 / MS17 docs境界
10. 次Blockで必要な判断事項
```

### 8.3 判断しないこと

MS16-B1では、以下を勝手に決めない。

```text
- 旧 src/gui/ を削除するか
- 旧 src/gui/ を docs/_old/ へ退避するか
- writer変更を許可するか
- クリック選択をMS16-B6に含めるか
- Skill文字化け修正をいつコミットするか
```

これらは、調査結果として選択肢を提示し、ユーザー判断または次Block計画で扱う。

---

## 9. 詳細ステップ

### Step 1: git状態確認

以下を実行する。

```powershell
git status
git branch
git log --oneline -n 10
git diff --stat
git diff --name-only
```

確認すること。

```text
- 現在branch
- mainとの差分有無
- 未コミットファイル
- 未追跡ファイル
- 前セッション由来のSkill修正差分
- 予期しないコード差分
```

### Step 2: 依存定義確認

以下のファイルを確認する。

```text
requirements.txt
pyproject.toml
MMD_AutoLipTool.spec
build.ps1
```

確認すること。

```text
- PySide6
- PySide6_Addons
- PySide6_Essentials
- shiboken6
- Qt関連DLL収集
- Qt backend前提記述
- package include に旧 gui が含まれるか
- wxPython主系が含まれるか
```

PowerShell例。

```powershell
Select-String -Path .\requirements.txt, .\pyproject.toml -Pattern "PySide6|shiboken6|Qt|gui"
```

`MMD_AutoLipTool.spec` や `build.ps1` が存在する場合は確認する。

```powershell
Select-String -Path .\MMD_AutoLipTool.spec, .\build.ps1 -Pattern "PySide6|shiboken6|Qt|gui"
```

存在しないファイルがある場合は、その旨を報告する。

### Step 3: import残存確認

以下を確認する。

```powershell
Get-ChildItem -Recurse -File |
  Where-Object { $_.Extension -in ".py", ".toml", ".txt", ".ps1", ".spec", ".md" } |
  Select-String -Pattern "from PySide6|import PySide6|QtWidgets|QtCore|QtGui|shiboken6"
```

確認すること。

```text
- 旧Qt/PySide import が残っているか
- docs内の単なる説明か
- 実行コード内の依存か
- tests内の旧依存か
```

docs内の記述と実行コード内のimportは分けて報告する。

### Step 4: 旧 `src/gui/` 確認

以下を確認する。

```powershell
Get-ChildItem .\src -Directory
Get-ChildItem .\src\gui -Recurse -File
```

`src/gui/` が存在しない場合は「存在しない」と報告する。

存在する場合は以下を整理する。

```text
- 旧Qt/PySide版と思われるか
- 現行実行経路に含まれるか
- package include に含まれるか
- testsから参照されるか
- Preview変形台形表示の参考ロジックがあるか
- 削除 / 退避 / 除外のどれが妥当か
```

このStepでは削除・退避しない。

### Step 5: wxPython主系確認

以下を確認する。

```text
src/gui_wx/
src/gui_wx/main_frame.py
src/gui_wx/app_controller.py
src/gui_wx/ui_state.py
src/gui_wx/theme.py
src/gui_wx/preview_panel.py
src/gui_wx/waveform_panel.py
```

確認すること。

```text
- MainFrame の現行レイアウト
- WaveformPanel と PreviewPanel の配置
- ThemeManager の適用箇所
- UiState の保持項目
- AppController の責務
- 右ペイン追加に影響する箇所
- Layout / Refresh / Update の使用状況
```

### Step 6: Preview表示構造確認

以下を確認する。

```text
src/gui_wx/preview_panel.py
src/core/preview_transform.py
```

確認すること。

```text
- 現行Previewがリボン型か
- 描画単位
- lane構造
- peak_value の扱い
- start_sec / end_sec の扱い
- Viewport / Zoom との接続
- 再生カーソルとの接続
- ThemePalette との接続
- clear時の挙動
```

### Step 7: VMD writer shape契約確認

以下を確認する。

```text
src/vmd_writer/
src/core/pipeline.py
```

確認すること。

```text
- writer が受け取る timing event 情報
- start_sec / end_sec / time_sec / peak_value の扱い
- short fallback
- legacy triangle
- trapezoid
- closing hold
- closing softness
- bridge / smoothing
- zero key / zero-only shape
- duplicate frame normalize
```

実装名は現行コードに従って報告する。

### Step 8: Preview と writer の不一致点整理

以下を整理する。

```text
- writerにはあるがPreviewに出ていないshape概念
- Previewにはあるがwriterと意味が違う表示
- peak_valueの表示差
- closing hold / closing softness の表示差
- bridge / smoothing の表示差
- short fallback の表示差
- zero peak / zero-only shape の表示差
```

このStepでは修正しない。

### Step 9: 右ペイン追加対象確認

以下を確認する。

```text
- MainFrameの現在レイアウト
- 左 / 中央 / 下部の構造
- 右ペインを追加する場合に触るべきファイル
- 既存InfoPanelまたはplaceholder panelの有無
- ThemeManager適用単位
- UiStateに追加が必要そうな項目
```

出力形式。

```text
右ペイン追加に必要な候補:
- ファイル:
- 理由:
- 影響:
- テスト候補:
```

### Step 10: docs上のMS16/MS17境界確認

以下を確認する。

```text
docs/MS16_Block_Breakdown_for_Antigravity.md
docs/MS16_and_Beyond_Milestone_Map_for_Antigravity.md
docs/MMD_Audio_WAV_Compatibility_Specification.md
docs/repo_milestone.md
docs/Version_Control.md
README.md
```

確認すること。

```text
- MS16を wx一本化 / Preview / GUI基盤として扱っているか
- mp3 / m4a / FFmpeg / MMD用WAV がMS16扱いになっていないか
- 音声拡張がMS17送りとして整理されているか
- 古い記述が残っていないか
```

MS16-B1ではdocs修正しない。
修正候補として報告する。

### Step 11: テスト現状確認

可能であれば以下を実行する。

```powershell
.venv\Scripts\python.exe -m pytest
```

実行できない場合は、以下を報告する。

```text
- 実行しなかった理由
- 依存不足
- 環境不足
- 所要時間が長すぎる
- GUIテスト環境の制約
```

テスト実行で生成されたキャッシュや一時ファイルがある場合は、変更として扱わず、生成物として報告する。

### Step 12: 最終git差分確認

最後に以下を実行する。

```powershell
git status
git diff --stat
git diff --name-only
```

確認すること。

```text
- B1作業による変更が発生していないこと
- 既存差分と新規差分を区別すること
- 変更が発生した場合は理由を説明すること
```

---

## 10. 状態遷移 / データ契約

MS16-B1では、アプリケーションの状態遷移やデータ契約を変更しない。

ただし、後続Blockに向けて以下の契約を確認する。

### 10.1 Pipeline正本

```text
Pipelineの正本は timing plan である。
Preview data と VMD writer input は timing plan からの派生物である。
```

確認観点:

```text
- Preview data が正本扱いされていないか
- writer output が正本扱いされていないか
- observation が timeline event の代替正本になっていないか
```

### 10.2 古い結果の破棄

```text
TEXT / 音声 / パラメータ変更時は、既存 timing plan / Preview / VMD保存可能状態を無効化する。
```

確認観点:

```text
- UiStateに current_timing_plan があるか
- input identity / job id 相当の仕組みがあるか
- late callback discard が維持されているか
- 古いPreviewが残らない構造になっているか
```

### 10.3 Previewとwriterの関係

```text
Previewは確認用表示であり、VMD writerの正本ではない。
ただし、Previewとwriterは意味的に整合している必要がある。
```

確認観点:

```text
- writer shape の主要概念がPreviewで確認可能か
- Previewだけ古いshape仕様になっていないか
- writerだけ新仕様でPreviewが追従していない箇所があるか
```

---

## 11. テスト方針

MS16-B1では、新規テスト追加やテスト修正は行わない。

### 11.1 必須確認

必須確認は以下。

```powershell
git status
git branch
git log --oneline -n 10
git diff --stat
git diff --name-only
```

### 11.2 任意確認

可能であれば以下を実行する。

```powershell
.venv\Scripts\python.exe -m pytest
```

### 11.3 テスト結果の扱い

テストが通った場合:

```text
- 実行コマンド
- テスト件数
- 結果
```

を報告する。

テストが失敗した場合:

```text
- 失敗テスト名
- 失敗理由の概要
- MS16-B1の範囲で直さないこと
- 後続Blockまたは補修対象にするか
```

を報告する。

テストを実行しなかった場合:

```text
- 実行しなかった理由
```

を報告する。

---

## 12. 受け入れ条件

MS16-B1の受け入れ条件は以下である。

```text
- コード変更を行っていない
- docs変更を行っていない
- 依存変更を行っていない
- ファイル削除・移動を行っていない
- git状態を確認している
- Qt / PySide6 残存箇所を列挙している
- 旧 src/gui/ の状態を報告している
- Preview ribbon 表示の生成箇所を報告している
- VMD writer shape 生成箇所を報告している
- Preview と writer の不一致点を報告している
- 右ペイン追加に必要な対象ファイル候補を報告している
- MS16 / MS17 境界に関するdocs矛盾を報告している
- MS16-B2以降で変更すべきファイル候補を整理している
- ユーザー判断が必要な点を整理している
```

---

## 13. リスクと対策

### 13.1 リスク: 調査Blockで実装してしまう

内容:

```text
MS16-B1は調査のみだが、依存削除やファイル削除まで行ってしまう可能性がある。
```

対策:

```text
- 実装禁止を明記する
- 最後に git diff を確認する
- 変更が出た場合は、内容を戻すか報告する
```

### 13.2 リスク: 旧Qtコードを誤って正本扱いする

内容:

```text
旧 src/gui/ に参考実装が残っている場合、現行主系と混同する可能性がある。
```

対策:

```text
- 現行主系は src/gui_wx/ と明記する
- 旧 src/gui/ は参考または削除候補として扱う
- 旧実装をそのまま移植しない
```

### 13.3 リスク: MS17対象をMS16対象に戻してしまう

内容:

```text
docs/MMD_Audio_WAV_Compatibility_Specification.md にMS16初期対応表記が残っている場合、音声拡張をMS16で実装する誤解が生じる。
```

対策:

```text
- MS16では音声拡張を実装しない
- mp3 / m4a / FFmpeg / MMD用WAV はMS17送りと報告する
- docs修正はB7または別Blockで扱う
```

### 13.4 リスク: テスト実行で生成物が出る

内容:

```text
pytest実行により .pytest_cache 等が生成され、git status に出る可能性がある。
```

対策:

```text
- 実行前後のgit statusを比較する
- 生成物と手動変更を区別する
- 生成物が出た場合は報告する
```

### 13.5 リスク: Skill文字化け修正差分を異常扱いする

内容:

```text
.agent/skills/build-packaging-verification/SKILL.md は前セッションでローカル修正済みだが、単体コミットしない方針である。
```

対策:

```text
- 既知差分として扱う
- 内容を確認し、B7またはまとまった整備コミット対象として報告する
- B1では修正・コミットしない
```

---

## 14. Antigravity 実装時の注意

Antigravity には以下を厳守させる。

```text
今回は MS16-B1 の実装前調査のみです。

コード変更、docs修正、依存変更、ファイル削除、ファイル移動、テスト修正、新規テスト追加は行わないでください。

目的は、MS16-B2以降の安全な実装に向けて、repo状態、Qt / PySide6残存、旧GUIコード、Preview表示、VMD writer shape契約、docs上のMS16/MS17境界を確認することです。

音声拡張、m4a対応、mp3対応、FFmpeg / ffprobe、解析用WAV生成、MMD用WAV同時出力はMS17対象です。MS16-B1では実装しないでください。
```

---

## 15. Antigravity 作業開始用コマンド

まず以下を実行する。

```powershell
git status
git branch
git log --oneline -n 10
git diff --stat
git diff --name-only
```

次に、依存とimport残存を確認する。

```powershell
Select-String -Path .\requirements.txt, .\pyproject.toml -Pattern "PySide6|shiboken6|Qt|gui"
```

`MMD_AutoLipTool.spec` と `build.ps1` が存在する場合は確認する。

```powershell
Select-String -Path .\MMD_AutoLipTool.spec, .\build.ps1 -Pattern "PySide6|shiboken6|Qt|gui"
```

import残存を確認する。

```powershell
Get-ChildItem -Recurse -File |
  Where-Object { $_.Extension -in ".py", ".toml", ".txt", ".ps1", ".spec", ".md" } |
  Select-String -Pattern "from PySide6|import PySide6|QtWidgets|QtCore|QtGui|shiboken6"
```

必要に応じてテストを実行する。

```powershell
.venv\Scripts\python.exe -m pytest
```

最後に再度git状態を確認する。

```powershell
git status
git diff --stat
git diff --name-only
```

---

## 16. 完了報告形式

Antigravity は、作業完了時に以下の形式で報告する。

```text
## MS16-B1 調査結果

### 1. 実行したコマンド

### 2. git状態
- branch:
- latest commit:
- modified:
- untracked:
- known local diff:

### 3. 確認したファイル

### 4. Qt / PySide6 残存箇所
#### 4.1 依存定義
#### 4.2 import
#### 4.3 build / spec
#### 4.4 tests
#### 4.5 docs内の記述

### 5. 旧 src/gui/ の状態
- 存在:
- 現行実行経路:
- package対象:
- 参考価値:
- 推奨扱い:

### 6. wxPython主系の状態
- MainFrame:
- AppController:
- UiState:
- Theme:
- Waveform:
- Preview:

### 7. Preview表示の現状
- 現行表示方式:
- 生成箇所:
- Viewport連携:
- cursor連携:
- Theme連携:
- clear処理:

### 8. VMD writer shape契約
- 生成箇所:
- shape種別:
- peak_value:
- closing hold:
- closing softness:
- bridge / smoothing:
- zero key:

### 9. Preview と writer の不一致点

### 10. 右ペイン追加に必要な対象ファイル候補

### 11. docs上のMS16 / MS17境界
- 矛盾あり / なし:
- 修正候補:
- MS16で扱うべきでない記述:

### 12. テスト結果
- 実行した / しなかった:
- 結果:
- 失敗がある場合の概要:

### 13. 最終git状態
- B1作業による変更:
- 既存差分:
- 新規差分:

### 14. MS16-B2以降への提案
- B2で扱うべきこと:
- B3で扱うべきこと:
- B4で扱うべきこと:
- B5以降への注意:

### 15. ユーザー判断が必要な点
```

---

## 17. 完了後の次アクション

MS16-B1完了後、調査結果に基づき次のいずれかへ進む。

### 通常ケース

```text
MS16-B2: Qt / PySide6 Removal
```

### B1で重大な矛盾が見つかった場合

```text
- MS16-B2へ進む前に、docsまたはBlock Breakdownを補正する
- 旧 src/gui/ の扱いについてユーザー判断を取る
- Preview / writer 契約に重大な不一致がある場合、B4前に補足設計を作る
```

### テストが大きく壊れている場合

```text
- MS16-B2へ進む前に、破損原因が既存不具合か環境問題かを切り分ける
- ただしMS16-B1では修正しない
```

---

## 18. 変更履歴

### 2026-05-01 / 初版

* MS16 Block Breakdown に基づき、MS16-B1 の実装プランを作成。
* B1を「実装なしの現状調査Block」と定義。
* repo状態、Qt / PySide6残存、旧GUIコード、Preview表示、VMD writer shape契約、docs上のMS16/MS17境界を調査対象に設定。
* 音声拡張、m4a対応、mp3対応、FFmpeg / ffprobe、解析用WAV生成、MMD用WAV同時出力はMS17対象として、MS16-B1のOut of Scopeに明記。
