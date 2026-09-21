# MS16 Block Breakdown for Antigravity

## 1. 文書情報

- 文書名: `MS16 Block Breakdown for Antigravity`
- 推奨ファイル名: `docs/MS16_Block_Breakdown_for_Antigravity.md`
- 対象プロジェクト: `MMD_AutoLipTool`
- 対象リポジトリ: `https://github.com/kanna3939/MMD_AutoLipTool`
- 対象マイルストーン: `MS16`
- 対象系列: `Ver0.4.x`
- 主対象GUI: `wxPython`
- 旧GUI系: `Qt / PySide6` は再導入しない
- 主対象読者: `Google Antigravity / Gemini 3.1 Pro`
- 主開発環境: `Windows 11`
- Shell: `Windows PowerShell`
- Python: repo の現在要件に従う
- 仮想環境: `.venv`
- 作成日: 2026-05-01
- 文書種別: Block Breakdown / 実装前分解計画

---

## 2. 文書目的

本書は、`MMD_AutoLipTool` の MS16 を安全に実装するために、MS16全体を Block 単位へ分解し、各Blockの目的・範囲・非対象・依存関係・検証観点を整理するための文書である。

MS16では、いきなり大きな実装を行わず、以下の作業を段階的に進める。

- wxPython主系への一本化
- Qt / PySide6 系依存の排除
- Preview変形台形表示の復元
- 将来拡張に備えた右ペイン型GUI基盤
- Preview shape data contract の整理
- 母音イベント選択の下地
- MS16 closeout とドキュメント補正

本書は、個別Blockの詳細実装計画書ではない。

各Blockの実装に入る前には、必要に応じて別途 `MS16-Bx_Implementation_Plan.md` を作成する。

---

## 3. 現在の開発現在地

MS15 までで、wxPython 主系における以下の機能は closeout 済みである。

```text
MS13: wxPython 主系の起動骨格・UI基盤
MS14: 既存機能 parity 回復
MS15: 波形表示 / Preview / 再生 / Viewport / Theme / State 統合
MS15: closeout 済み
次: MS16
````

MS15までに成立している主な範囲は以下である。

```text
- TEXT読込
- WAV読込
- 解析実行
- VMD保存
- recent files
- settings save / load
- busy / cancel / timeout warning / late callback discard
- 波形表示
- Preview表示
- WAV再生
- 再生位置同期
- Zoom
- Viewport
- Auto-follow
- Theme / UiState 統合
```

MS16では、これらを壊さず、wxPython主系の安定化と将来拡張の土台整備を行う。

---

## 4. MS16の採用方針

### 4.1 MS16で扱うもの

MS16では以下を扱う。

```text
- wxPython主系への一本化
- Qt / PySide6 依存の完全排除
- 旧Qt/PySide版に近い Preview 変形台形表示の復元
- 右ペイン型GUI基盤
- Info / Warning / 選択イベント / プリセット / モデルプロファイル用の表示枠
- Preview shape data contract
- 将来の母音イベント選択・軽微編集に向けた metadata 整備
- MS16実装内容と docs の整合確認
```

### 4.2 MS16では扱わないもの

音声拡張と `.m4a` 対応は MS17 に回す。

したがって、MS16では以下を実装しない。

```text
- mp3入力対応
- m4a入力対応
- wav / mp3 / m4a 入力導線の拡張
- FFmpeg / ffprobe 接続
- 解析用WAV生成基盤
- MMD用WAV同時出力
- MMD互換WAV検証
- 音声変換系エラー処理本体
- MMD用WAV保存ダイアログ
- FFmpeg同梱有無の決定
- FFmpegライセンス同梱設計
```

これらは MS17 の対象とする。

### 4.3 MS16とMS17の境界

MS16とMS17の境界は以下とする。

| 区分 | MS16 | MS17 |
| ---------------- | ----------- | ------------------- |
| GUI主系 | wxPython一本化 | wxPython維持 |
| Qt / PySide6 | 排除 | 再導入しない |
| Preview | 変形台形表示復元 | 音声拡張後も維持 |
| 右ペイン | 枠・表示基盤 | 音声変換情報やWarning表示に活用 |
| shape metadata | 整備 | 音声変換後も整合維持 |
| mp3 / m4a | 非対象 | 対象 |
| FFmpeg / ffprobe | 非対象 | 対象 |
| 解析用WAV生成 | 非対象 | 対象 |
| MMD用WAV出力 | 非対象 | 対象 |
| 音声系エラー分類 | 文書参照のみ | 実装対象 |

---

## 5. MS16前提仕様書

MS16では、以下の仕様書を主に参照する。

```text
docs/MS16_and_Beyond_Milestone_Map_for_Antigravity.md
docs/Specification_Prompt_v4.md
docs/GUI_State_Theme_Specification.md
docs/Pipeline_Data_Contract_Specification.md
docs/VMD_Output_Specification.md
docs/Error_Handling_Specification.md
docs/Security_Safety_Specification.md
docs/Release_Package_Manifest.md
docs/repo_milestone.md
docs/Version_Control.md
README.md
```

音声拡張関連の仕様書は、MS16では実装対象ではなく、MS17以降の正本仕様として参照する。

```text
docs/MMD_Audio_WAV_Compatibility_Specification.md
```

MS16 closeout 時には、この音声仕様書内の「MS16初期対応」等の表現が、MS17送り方針と矛盾していないか確認し、必要に応じて補正する。

---

## 6. MS16全体のBlock構成

MS16は以下の7Blockに分ける。

| Block | 名称 | 実装有無 | 主目的 |
| ------ | ----------------------------------------------- | ---- | --------------------------- |
| MS16-B1 | Repo / Dependency / Preview Shape Contract 現状調査 | なし | 実装前調査 |
| MS16-B2 | Qt / PySide6 Removal | あり | wxPython主系への一本化 |
| MS16-B3 | GUI Layout Foundation / Right Pane 基盤 | あり | 将来拡張GUIの枠作り |
| MS16-B4 | Preview 変形台形表示復元 | あり | Preview表示をwriter shapeに近づける |
| MS16-B5 | Preview Shape Data Contract 固定 | あり | shape metadata整備 |
| MS16-B6 | 母音イベント選択の下地 | あり | 将来編集に向けた選択基盤 |
| MS16-B7 | 統合確認 / Docs補正 / MS16 Closeout | あり | MS16完了整理 |

---

## 7. MS16全体の実装順序

推奨順序は以下である。

```text
MS16-B1
  ↓
MS16-B2
  ↓
MS16-B3
  ↓
MS16-B4
  ↓
MS16-B5
  ↓
MS16-B6
  ↓
MS16-B7
```

理由:

1. まず現状調査で repo / docs / 依存 / Preview / writer の状態を把握する。
2. Qt / PySide6 排除を先に行い、後続実装が旧GUIを参照しない状態にする。
3. GUI右ペイン基盤を先に整え、後続Blockで情報表示先を確保する。
4. Preview表示を変形台形へ戻す。
5. Preview shape metadata を固定する。
6. 母音イベント選択の下地を整える。
7. 最後に統合確認と docs 補正を行う。

---

## 8. 共通禁止事項

MS16全体で以下を禁止する。

```text
- Qt / PySide6 を再導入しない
- 旧 src/gui/ を現行主系として拡張しない
- wxPython主系を壊さない
- MS17対象の mp3 / m4a / FFmpeg / MMD用WAV 出力を実装しない
- VMD出力対象をモーフキーフレーム以外へ広げない
- ボーン / カメラ / 照明 / IK / 表示制御をVMDへ出力しない
- Preview表示をpipeline正本として扱わない
- VMD writer出力をpipeline正本として扱わない
- 古いworker結果を現在結果としてUIへ反映しない
- 古いtiming plan由来のPreviewや選択状態を残さない
- GUI変更時にテーマ追従・再描画・Busy復帰確認を省略しない
- 実装済みでない機能をREADMEやdocsで完了扱いしない
```

---

## 9. 共通確認コマンド

Antigravity 側では、各Blockの開始時に必要に応じて以下を確認する。

```powershell
git status
git branch
git log --oneline -n 10
git diff --stat
git diff --name-only
```

テスト実行は、原則として以下を基本とする。

```powershell
.venv\Scripts\python.exe -m pytest
```

特定Block用のテストが追加された場合は、対象テストを先に実行し、その後に全体テストを実行する。

---

# MS16-B1: Repo / Dependency / Preview Shape Contract 現状調査

## 1. 目的

MS16実装前に、現在の repo 状態、Qt / PySide6 残存箇所、Preview表示、VMD writer の shape 契約、GUI構成、docs間のMS16/MS17境界を把握する。

このBlockでは実装を行わない。

## 2. 背景

MS15 closeout 後、wxPython主系は成立している。

一方で、MS16着手前の課題として以下が残っている。

```text
- Qt / PySide6 系依存が残っている可能性
- 旧 src/gui/ が残っている可能性
- Preview が旧Qt/PySide版の変形台形表示ではなくリボン型表示になっている
- Preview と VMD writer の shape 解釈が十分に近くない可能性
- 将来の選択イベント / Info / Warning / プリセット / モデルプロファイル用GUI枠が未固定
- docs上で、MS16とMS17の境界に揺れがある
```

## 3. In Scope

```text
- repo状態確認
- default branch / current branch 確認
- 最新コミット確認
- 未コミット差分確認
- requirements.txt の PySide6 系依存確認
- pyproject.toml の PySide6 系依存確認
- MMD_AutoLipTool.spec / build.ps1 の Qt 系混入確認
- src/gui/ 旧Qt系コード確認
- import PySide6 / QtWidgets / QtCore / QtGui の残存確認
- matplotlib backend がQt前提でないか確認
- src/gui_wx/preview_panel.py の現状確認
- src/core/preview_transform.py の現状確認
- src/vmd_writer/ の shape 生成契約確認
- Preview ribbon 表示の生成箇所確認
- writer shape と Preview shape の不一致点確認
- 右ペイン追加に必要なGUI対象ファイル確認
- MS16 / MS17 境界のdocs矛盾確認
```

## 4. Out of Scope

```text
- コード変更
- 依存変更
- ファイル削除
- ファイル移動
- Preview描画変更
- GUIレイアウト変更
- docs修正
- テスト修正
```

## 5. 前提仕様書

```text
docs/MS16_and_Beyond_Milestone_Map_for_Antigravity.md
docs/GUI_State_Theme_Specification.md
docs/Pipeline_Data_Contract_Specification.md
docs/VMD_Output_Specification.md
docs/Error_Handling_Specification.md
docs/repo_milestone.md
docs/Version_Control.md
```

## 6. 対象ファイル候補

```text
requirements.txt
pyproject.toml
MMD_AutoLipTool.spec
build.ps1
README.md
src/gui/
src/gui_wx/main_frame.py
src/gui_wx/preview_panel.py
src/gui_wx/waveform_panel.py
src/gui_wx/app_controller.py
src/gui_wx/ui_state.py
src/gui_wx/theme.py
src/core/preview_transform.py
src/core/pipeline.py
src/vmd_writer/
tests/
docs/
```

## 7. 依存関係

MS16-B1 は MS16 全Blockの前提である。

MS16-B2 以降は、B1の調査結果を踏まえて実装範囲を確定する。

## 8. 実装方針

このBlockでは実装しない。

Antigravity は確認結果を以下の形式で報告する。

```text
1. 確認したコマンド
2. 確認したファイル
3. Qt / PySide6 残存箇所
4. 旧 src/gui/ の状態
5. Preview ribbon 表示の生成箇所
6. writer shape 生成箇所
7. Preview と writer の主な不一致点
8. GUI右ペイン追加に必要な対象ファイル
9. MS16 / MS17 境界に関するdocs矛盾
10. MS16-B2以降で変更すべきファイル候補
11. 実装前にユーザー判断が必要な点
```

## 9. テスト方針

このBlockでは実装を行わないため、テスト追加は不要。

ただし、現状確認として可能であれば以下を実行する。

```powershell
.venv\Scripts\python.exe -m pytest
```

実行できない場合は、理由を報告する。

## 10. 受け入れ条件

```text
- 実装変更を行っていない
- git diff --name-only で意図しない変更がない
- Qt / PySide6 残存箇所が列挙されている
- Preview / writer / shape contract の現状が説明されている
- MS16-B2以降の変更対象が明確になっている
- MS16とMS17の境界に関するdocs矛盾が記録されている
```

## 11. リスクと対策

### リスク

```text
- 調査のつもりでコード変更してしまう
- 旧Qtコードを必要以上に参照して、wxPython主系の方針がぶれる
- 音声拡張をMS16対象として扱ってしまう
```

### 対策

```text
- 実装禁止を明記する
- git diff を確認する
- MS17対象項目を明示的に非対象へ置く
```

## 12. GUI / Theme / Error Handling 確認事項

このBlockではGUI変更を行わない。

ただし、後続Blockで必要になりそうな確認事項を以下の観点で洗い出す。

```text
- Layout()
- Refresh()
- Update()
- ThemeManager
- UiState
- Busy解除
- 古いPreviewのクリア
- 古いworker結果破棄
```

## 13. Antigravity 実装時の注意

```text
今回は MS16-B1 の実装前調査のみです。
コード変更・依存変更・ファイル削除・ファイル移動・docs修正は行わないでください。
調査結果と、MS16-B2以降の変更対象候補のみを報告してください。
```

---

# MS16-B2: Qt / PySide6 Removal

## 1. 目的

Qt / PySide6 系依存を排除し、現行GUI主系を wxPython に一本化する。

## 2. 背景

MS16では、wxPython主系を今後の開発基盤とする。

Qt / PySide6 系が残っていると、以下の問題がある。

```text
- Antigravity が旧GUIを誤参照する
- PyInstaller配布物にQt系DLLやresourceが混入する
- 配布サイズが増える
- ライセンス説明が複雑になる
- 現行主系が不明瞭になる
```

そのため、MS16の早い段階で Qt / PySide6 を排除する。

## 3. In Scope

```text
- requirements.txt から PySide6 系依存を削除
- pyproject.toml から PySide6 系依存を削除
- package include から旧 gui パッケージを除外
- MMD_AutoLipTool.spec の Qt / PySide6 混入確認
- build.ps1 の Qt / PySide6 混入確認
- src/gui/ 旧Qt系コードの扱い整理
- import PySide6 / QtWidgets / QtCore / QtGui の残存確認
- Qt backend 前提の matplotlib 設定確認
- Qt前提テストの残存確認
- README / docs のQt主系誤認表現の確認
```

## 4. Out of Scope

```text
- Preview変形台形表示の実装
- 右ペインGUI追加
- 母音イベント選択基盤
- mp3 / m4a 入力対応
- FFmpeg / ffprobe 接続
- 解析用WAV生成
- MMD用WAV出力
- 配布ビルドcloseout
```

## 5. 前提仕様書

```text
docs/MS16_and_Beyond_Milestone_Map_for_Antigravity.md
docs/GUI_State_Theme_Specification.md
docs/Release_Package_Manifest.md
docs/repo_milestone.md
docs/Version_Control.md
```

## 6. 対象ファイル候補

```text
requirements.txt
pyproject.toml
MMD_AutoLipTool.spec
build.ps1
src/gui/
src/gui_wx/
tests/
README.md
docs/Version_Control.md
docs/repo_milestone.md
```

## 7. 依存関係

```text
MS16-B1 完了後に実施する。
```

B1で旧Qt版Previewロジックに参考価値があると判明した場合、必要な知見を確認してから削除または退避する。

## 8. 実装方針

推奨方針は以下である。

```text
旧Qt/PySide版コードは、実行対象・配布対象・import対象から外す。
必要な表示仕様やロジックだけを確認し、wx側へ移植する。
旧コードを残す場合でも、package include と import 対象からは必ず外す。
```

旧 `src/gui/` の扱いは、B1調査結果を踏まえて以下から選ぶ。

| 方針 | 内容 | 推奨度 |
| -- | -------------------------------------- | --- |
| A | `src/gui/` を削除し、必要な知見は docs または wx側へ移す | 高 |
| B | `docs/_old/` 等へ参考資料として退避 | 中 |
| C | repo内に残すが package include から外す | 低 |
| D | そのまま残す | 非推奨 |

基本推奨は A または B である。

## 9. テスト方針

まず、依存・import残存を確認する。

```powershell
Select-String -Path .\requirements.txt, .\pyproject.toml -Pattern "PySide6|shiboken6|Qt"
Get-ChildItem -Recurse -File | Select-String -Pattern "from PySide6|import PySide6|QtWidgets|QtCore|QtGui"
```

その後、テストを実行する。

```powershell
.venv\Scripts\python.exe -m pytest
```

可能であれば、アプリ起動確認も行う。

```powershell
.venv\Scripts\python.exe -m src.gui_wx.main
```

実際の起動コマンドは repo の現行構成に従う。

## 10. 受け入れ条件

```text
- requirements.txt に PySide6 / PySide6_Addons / PySide6_Essentials / shiboken6 がない
- pyproject.toml に PySide6 系依存がない
- 旧Qt系コードが実行対象・配布対象・import対象から外れている
- PySide6 import が残っていない
- Qt backend 前提の matplotlib 設定が残っていない
- wxPython主系テストが通る
- アプリがwxPython主系として起動できる
- README / docs にQt主系と誤認される表現が残っていない
```

## 11. リスクと対策

### リスク

```text
- 旧Previewの参考ロジックまで失う
- package include 変更でwxPython主系まで壊す
- PyInstaller spec 変更で配布設定を壊す
```

### 対策

```text
- 削除前に必要な表示仕様だけ確認する
- 変更ファイルを最小化する
- tests と起動確認を行う
- spec / build.ps1 は不要な変更を避ける
```

## 12. GUI / Theme / Error Handling 確認事項

このBlockではGUI挙動変更を最小にする。

ただし、以下を確認する。

```text
- アプリ起動
- テーマ切替
- Waveform表示
- Preview表示
- ボタンEnable/Disable
- Status表示
```

## 13. Antigravity 実装時の注意

```text
Qt / PySide6 を再導入しないでください。
wxPython主系を維持してください。
旧Qtコードの削除または退避を行う場合は、事前に必要な参考ロジックを確認し、変更理由を報告してください。
MS17対象のmp3 / m4a / FFmpeg / MMD用WAV出力は実装しないでください。
```

---

# MS16-B3: GUI Layout Foundation / Right Pane 基盤

## 1. 目的

MS16以降の Info / Warning / 選択イベント / プリセット / モデルプロファイルを受け止める右ペイン型GUI基盤を作る。

## 2. 背景

MS15までで、波形表示、Preview、再生、Viewport、Theme / State は統合済みである。

次に、将来の診断情報、警告、選択母音イベント情報、プリセット、モデルプロファイルを表示するための安定したGUI領域が必要になる。

MS16では、本格機能ではなく表示枠とview helperを整備する。

## 3. In Scope

```text
- 右ペイン領域の追加
- Info タブ
- Warning タブ
- 選択イベント タブ
- プリセット タブ
- モデルプロファイル タブ
- 各タブの placeholder または最小表示
- view helper / setter / clear API の整備
- 既存の波形 / Preview / Toolbar / Status の維持
- Light / Dark / System テーマ追従
- Layout / Refresh / Update の要否確認
```

## 4. Out of Scope

```text
- Warning判定本体
- 出力診断レポート本体
- 母音イベント編集
- プリセット保存
- モデルプロファイル保存
- mp3変換UI
- m4a変換UI
- MMD用WAV保存UI
- FFmpeg / ffprobe 実行UI
```

## 5. 前提仕様書

```text
docs/GUI_State_Theme_Specification.md
docs/Pipeline_Data_Contract_Specification.md
docs/MS16_and_Beyond_Milestone_Map_for_Antigravity.md
docs/Error_Handling_Specification.md
```

## 6. 対象ファイル候補

```text
src/gui_wx/main_frame.py
src/gui_wx/app_controller.py
src/gui_wx/ui_state.py
src/gui_wx/theme.py
src/gui_wx/placeholder_panels.py
src/gui_wx/info_panel.py
tests/test_wx_ms16_b3_gui_layout.py
```

実際の対象ファイル名は、B1調査結果と現行repo構成に従う。

## 7. 依存関係

```text
MS16-B2 完了後に実施する。
```

理由:

```text
- 旧Qt系コードを排除してからwxPython主系GUIを拡張するため
- Antigravityが旧GUIを参照するリスクを下げるため
```

## 8. 実装方針

基本レイアウトは以下を目標とする。

```text
上部:
  ファイル読込 / 解析 / 保存 / 再生 / Zoom / パラメータ操作

左:
  入力情報
  TEXT / ひらがな / 母音列の概要

中央:
  波形表示
  Preview表示

右:
  情報系タブペイン
    - Info
    - Warning
    - 選択イベント
    - プリセット
    - モデルプロファイル

下部:
  Status / 処理状況
```

右ペインは、将来拡張用の枠である。

MS16時点では、各タブに placeholder または読み取り専用の最小表示を置く。

### 各タブのMS16時点の扱い

#### Info

```text
- 入力ファイル情報
- 解析結果概要
- 現在位置
- 将来の変換情報表示先
```

MS16では最小表示でよい。

#### Warning

```text
- Warning表示枠
- MS16では placeholder または最小警告表示
```

本格的なWarning判定はMS19以降または別マイルストーンで扱う。

#### 選択イベント

```text
- 選択中母音イベント情報の表示枠
- MS16では下地のみ
```

本格的な編集はMS21以降。

#### プリセット

```text
- プリセット情報表示枠
- MS16では placeholder または現在値表示
```

プリセット編集本体はMS20以降。

#### モデルプロファイル

```text
- モデル別プロファイル表示枠
- MS16では placeholder
```

モデル別プロファイル本体はMS22以降。

## 9. テスト方針

Block専用テストを追加する場合は、以下を想定する。

```powershell
.venv\Scripts\python.exe -m pytest tests\test_wx_ms16_b3_gui_layout.py
.venv\Scripts\python.exe -m pytest
```

確認観点:

```text
- MainFrame が起動する
- 右ペインが存在する
- Info / Warning / 選択イベント / プリセット / モデルプロファイル タブが存在する
- 各タブの placeholder 表示が可能
- Light / Dark / System テーマ切替で例外が出ない
- 既存ボタンの有効/無効制御が壊れない
- 既存の波形 / Preview 領域が存在する
```

## 10. 受け入れ条件

```text
- 右ペインが追加されている
- Info / Warning / 選択イベント / プリセット / モデルプロファイルの枠がある
- 既存のTEXT読込 / WAV読込 / 解析 / VMD保存 / 再生導線を壊していない
- Light / Dark / System テーマで破綻しない
- Layout / Refresh の必要処理が行われている
- MS17対象の音声変換UIは実装されていない
```

## 11. リスクと対策

### リスク

```text
- 右ペイン追加により中央の波形 / Preview 領域が狭くなる
- タブを作り込みすぎてMS20以降の機能まで先取りする
- テーマ追従漏れが発生する
```

### 対策

```text
- splitter / sash / 最小サイズを検討する
- MS16ではplaceholderとview helperに限定する
- ThemeManager経由で色を適用する
- GUI変更報告にLayout / Refresh / Theme確認結果を含める
```

## 12. GUI / Theme / Error Handling 確認事項

```text
- 新規タブがテーマ追従する
- 文字色 / 背景色 / disabled色が破綻しない
- 右ペイン追加後もStatus表示が残る
- Busy中の操作制御が壊れない
- 入力再読込時にInfo表示が古いまま残らない
```

## 13. Antigravity 実装時の注意

```text
右ペイン追加に留めてください。
Warning判定、イベント編集、プリセット保存、モデルプロファイル保存は実装しないでください。
既存の波形・Preview・再生・Zoom導線を壊さないでください。
MS17対象の mp3 / m4a / FFmpeg / MMD用WAV 関連UIは実装しないでください。
```

---

# MS16-B4: Preview 変形台形表示復元

## 1. 目的

現行wx版Previewのリボン型表示を、VMD writer の shape に近い変形台形 / 三角形 / multi-point envelope 表示へ戻す。

## 2. 背景

Previewは、VMD出力の見え方を事前確認するための補助表示である。

Previewはpipelineの正本ではないが、VMD writerと意味的に整合している必要がある。

MS16では、旧Qt/PySide版の見え方を参考にしつつ、wxPython主系でPreview表示を改善する。

## 3. In Scope

```text
- Preview表示形状の変更
- 変形台形表示
- 三角形表示
- multi-point envelope 相当表示
- peak_value に応じた高さ表現
- start / top / hold / slope / end / valley 相当の可視化
- Waveform と Preview の時間軸一致
- 再生カーソル同期
- Viewport / Zoom 対応維持
- Theme追従維持
```

## 4. Out of Scope

```text
- VMD writer の大規模変更
- VMD出力仕様の変更
- 母音イベント編集
- hit-test 本実装
- drag編集
- shape保存
- Undo / Redo
- mp3 / m4a 対応
- MMD用WAV出力
```

## 5. 前提仕様書

```text
docs/VMD_Output_Specification.md
docs/Pipeline_Data_Contract_Specification.md
docs/GUI_State_Theme_Specification.md
docs/MS16_and_Beyond_Milestone_Map_for_Antigravity.md
```

## 6. 対象ファイル候補

```text
src/gui_wx/preview_panel.py
src/core/preview_transform.py
src/vmd_writer/
tests/test_wx_ms16_b4_preview_shape.py
```

実際の対象はB1調査結果に従う。

## 7. 依存関係

```text
MS16-B3 完了後に実施する。
```

ただし、B4は右ペインそのものには強く依存しない。
B3完了後に進める理由は、GUI全体の配置を先に安定させるためである。

## 8. 実装方針

基本方針:

```text
- 正本は timing plan
- Preview data は timing plan からの派生物
- Preview表示を元に writer 出力を再構成しない
- writer出力を元に timing plan を逆生成しない
- Previewとwriterのshape意味を近づける
- 表示用データは表示用に留める
```

Previewに表示すべき概念:

```text
- morph_name / vowel
- start_sec
- end_sec
- peak_value
- shape_kind
- control_points 相当
- frame_range 相当
- value_range 相当
```

MS16-B4時点では、完全な編集用metadata固定までは求めない。
metadata固定はMS16-B5で扱う。

## 9. テスト方針

Block専用テストを追加する場合は、以下を想定する。

```powershell
.venv\Scripts\python.exe -m pytest tests\test_wx_ms16_b4_preview_shape.py
.venv\Scripts\python.exe -m pytest
```

確認観点:

```text
- 台形shapeが描画データとして生成される
- 短区間は三角形またはfallback表示になる
- peak_value が高さに反映される
- shape が 0.0〜1.0 の範囲に収まる
- Viewport変更で表示範囲がWaveformと一致する
- 再生カーソル位置がPreviewとWaveformで一致する
- 解析失敗時に古いPreviewが残らない
- テーマ切替後に再描画される
```

## 10. 受け入れ条件

```text
- Previewがリボン型一辺倒ではなく、shapeとして表示される
- 変形台形 / 三角形 / envelope 相当の表示が可能
- writerとPreviewのshape意味が大きく乖離していない
- Zoom / Viewport / playback cursor が壊れていない
- 解析失敗・入力変更時に古いPreviewが残らない
- テーマ切替後もPreviewが再描画される
- VMD出力仕様を勝手に変更していない
```

## 11. リスクと対策

### リスク

```text
- Previewをwriterの正本と誤解する実装になる
- writer側の出力仕様まで不用意に変更する
- 旧Qt版の実装をそのまま移植してwxPython主系と衝突する
- 描画負荷が増えてGUI応答性が落ちる
```

### 対策

```text
- Pipeline_Data_Contract に従い、正本は timing plan とする
- writer変更が必要な場合は理由を明記し、最小変更に留める
- wxPython主系のTheme / Viewport / Refresh規則に合わせる
- 表示点数や描画範囲をViewportで制限する
```

## 12. GUI / Theme / Error Handling 確認事項

```text
- Preview data更新時に Refresh される
- Preview clear時に Refresh される
- テーマ切替時に再描画される
- Viewport変更時にWaveformと範囲が一致する
- 解析失敗時に古い表示が残らない
- 古いworker結果がPreviewへ反映されない
```

## 13. Antigravity 実装時の注意

```text
Preview表示を変形台形系へ戻してください。
ただし、VMD writer の出力仕様を勝手に変更しないでください。
writer変更が必要な場合は、理由と影響範囲を報告し、最小変更に留めてください。
MS17対象の音声入力拡張・FFmpeg・MMD用WAV出力は実装しないでください。
```

---

# MS16-B5: Preview Shape Data Contract 固定

## 1. 目的

Preview / writer / 将来の選択イベント表示が共有できる shape metadata を固定する。

## 2. 背景

MS16-B4でPreview表示を変形台形系へ戻した後、将来の母音イベント選択・軽微編集へ進むには、描画shapeとtiming eventの対応関係が必要になる。

MS16-B5では、編集機能そのものではなく、shape data contract を整理する。

## 3. In Scope

```text
- shape_kind
- control_points
- source_event_index
- source_event_id 相当
- morph_name
- vowel
- start_sec
- end_sec
- peak_value
- frame_range
- value_range
- fallback / warning summary
- hit-test 用metadataの下地
- Preview shape と timing event の対応
```

## 4. Out of Scope

```text
- GUI上のクリック選択
- ドラッグ編集
- 編集値保存
- VMD再生成UI
- hit-test本実装
- Undo / Redo
- セッション保存
- プリセット保存
```

## 5. 前提仕様書

```text
docs/Pipeline_Data_Contract_Specification.md
docs/VMD_Output_Specification.md
docs/GUI_State_Theme_Specification.md
docs/MS16_and_Beyond_Milestone_Map_for_Antigravity.md
```

## 6. 対象ファイル候補

```text
src/core/preview_transform.py
src/gui_wx/preview_panel.py
src/gui_wx/ui_state.py
src/vmd_writer/
tests/test_wx_ms16_b5_preview_contract.py
```

実際の対象はB1およびB4の結果に従う。

## 7. 依存関係

```text
MS16-B4 完了後に実施する。
```

## 8. 実装方針

基本方針:

```text
- timing plan を正本とする
- Preview data は派生物とする
- Preview data から timing plan を復元しない
- VMD keyframes から timing plan を復元しない
- Preview shape と timing event を対応づける
- 将来の選択イベント表示に必要な最小metadataを付与する
```

shape metadata は、MS16時点では以下の目的に限定する。

```text
- 表示
- テスト
- 選択イベント表示の下地
- 将来hit-testの準備
```

編集値の保存や再生成はMS16では扱わない。

## 9. テスト方針

Block専用テストを追加する場合は、以下を想定する。

```powershell
.venv\Scripts\python.exe -m pytest tests\test_wx_ms16_b5_preview_contract.py
.venv\Scripts\python.exe -m pytest
```

確認観点:

```text
- 各Preview shapeが元eventへ対応できる
- shape_kind が存在する
- control_points が時系列として解釈できる
- value_range が 0.0〜1.0 に収まる
- frame_range が負にならない
- source_event_index が不正範囲を指さない
- fallback / warning summary が必要に応じて保持される
```

## 10. 受け入れ条件

```text
- Preview shape と timing event の対応が取れる
- 将来の選択イベント表示に必要な最小metadataがある
- writer と Preview の解釈差が記録・縮小されている
- 古いtiming plan由来のPreviewが現在状態に混入しない
- 編集機能は実装されていない
```

## 11. リスクと対策

### リスク

```text
- metadataを増やしすぎて構造が重くなる
- shape contract を固定しすぎて後続の改善が難しくなる
- observationを正本扱いしてしまう
```

### 対策

```text
- MS16では選択・表示に必要な最小項目に限定する
- 実装上の型名より意味契約を優先する
- 正本は timing plan であることを維持する
- observation は補助情報として扱う
```

## 12. GUI / Theme / Error Handling 確認事項

このBlockは主にデータ契約である。

GUI表示変更がある場合は以下を確認する。

```text
- Preview再描画
- Previewクリア
- 古い表示の破棄
- Theme追従
- 入力変更時のshape metadata無効化
```

## 13. Antigravity 実装時の注意

```text
shape metadataは将来編集の下地です。
MS16では編集機能を実装しないでください。
Preview data を pipeline の正本にしないでください。
正本は timing plan です。
```

---

# MS16-B6: 母音イベント選択の下地

## 1. 目的

Preview上の描画shapeと母音イベントを対応づけ、将来の選択・軽微編集に備える。

MS16では、編集本体ではなく、選択状態と読み取り専用情報表示の土台だけを作る。

## 2. 背景

MS21以降で、母音イベント単位の軽微編集を行う予定がある。

その前段として、MS16では以下が必要になる。

```text
- Preview shape と timing event の対応
- selected event の内部保持
- 選択中イベント情報の表示先
- 入力変更や解析失敗時の選択状態クリア
```

## 3. In Scope

```text
- Preview shape と source_event_index の対応
- selected_event_id / selected_shape_id 相当の内部保持
- 選択中イベント情報の view helper
- 右ペイン「選択イベント」タブへの最小表示
- テスト用 accessor
- 入力変更 / 解析失敗 / timing plan無効化時の選択状態クリア
```

## 4. Out of Scope

```text
- マウスクリックによる本格選択
- ドラッグ編集
- モーフ値変更
- timing変更
- 編集値保存
- VMD再生成
- Undo / Redo
- セッション保存
```

クリック選択を実装するかどうかは、B6実装前の詳細計画で判断する。
ただし、MS16では「編集」は実装しない。

## 5. 前提仕様書

```text
docs/MS16_and_Beyond_Milestone_Map_for_Antigravity.md
docs/Pipeline_Data_Contract_Specification.md
docs/GUI_State_Theme_Specification.md
docs/VMD_Output_Specification.md
```

## 6. 対象ファイル候補

```text
src/gui_wx/preview_panel.py
src/gui_wx/main_frame.py
src/gui_wx/ui_state.py
src/gui_wx/info_panel.py
tests/test_wx_ms16_b6_event_selection_foundation.py
```

実際の対象はB3〜B5の実装結果に従う。

## 7. 依存関係

```text
MS16-B3 完了後
MS16-B5 完了後
```

B6は右ペインとshape metadataの両方に依存する。

## 8. 実装方針

基本方針:

```text
- 最初は内部APIまたはテスト用APIで選択状態を扱う
- GUI上の編集操作は入れない
- 選択イベントタブには読み取り専用の概要だけ表示
- current timing plan と対応しない選択状態は破棄する
- 古いworker結果由来の選択状態をUIへ反映しない
```

選択中イベント表示の候補:

```text
- vowel / morph_name
- start_sec
- end_sec
- duration_sec
- peak_value
- shape_kind
- source_event_index
- fallback / warning summary
```

## 9. テスト方針

Block専用テストを追加する場合は、以下を想定する。

```powershell
.venv\Scripts\python.exe -m pytest tests\test_wx_ms16_b6_event_selection_foundation.py
.venv\Scripts\python.exe -m pytest
```

確認観点:

```text
- shapeからevent参照が可能
- selected_event が current timing plan と一致する
- 入力変更時に選択状態がクリアされる
- 解析失敗時に選択状態がクリアされる
- 古いworker結果破棄時に選択状態が更新されない
- 右ペイン表示が古い選択情報を残さない
```

## 10. 受け入れ条件

```text
- 将来のイベント選択・編集に進めるmetadataがある
- 選択中イベント情報を表示または取得できる
- 編集機能は入っていない
- 古いtiming plan由来の選択が残らない
- 右ペインの選択イベントタブが読み取り専用情報を表示できる
```

## 11. リスクと対策

### リスク

```text
- 選択UIを作り込みすぎてMS21相当まで進んでしまう
- 選択状態が古いtiming planにぶら下がったまま残る
- Preview shape と event の対応が不安定になる
```

### 対策

```text
- MS16では読み取り専用・下地のみ
- 入力変更 / 解析失敗 / plan無効化時に必ず選択状態をクリアする
- source_event_index / event_id の整合をテストする
```

## 12. GUI / Theme / Error Handling 確認事項

```text
- 右ペイン選択イベント表示のテーマ追従
- 入力変更時の表示クリア
- 解析失敗時の表示クリア
- Layout / Refresh
- 古いworker結果の破棄
```

## 13. Antigravity 実装時の注意

```text
母音イベント編集は実装しないでください。
MS16では、選択状態の下地と読み取り専用表示に限定してください。
クリック選択を入れる場合も、値変更・保存・VMD再生成は行わないでください。
```

---

# MS16-B7: 統合確認 / Docs補正 / MS16 Closeout

## 1. 目的

MS16-B1〜B6 の実装結果を統合確認し、MS16をcloseoutする。

あわせて、MS16とMS17の境界をdocsへ反映し、MS17へ安全に進める状態を作る。

## 2. 背景

MS16では以下の複数領域に変更が入る。

```text
- 依存関係
- 旧GUIコード
- wxPython GUI
- Preview描画
- shape metadata
- 選択イベント表示の下地
- docs
```

そのため、最後に統合確認を行い、実装済み / 未実装 / MS17送り / 将来課題を明確に分ける必要がある。

## 3. In Scope

```text
- MS16-B1〜B6 の統合確認
- 全テスト実行
- GUI手動確認
- Qt / PySide6 残存確認
- Preview / Waveform / Playback / Viewport / Theme の回帰確認
- README 更新
- docs/Version_Control.md 更新
- docs/repo_milestone.md 更新
- MS16 closeout 記録
- MS16 / MS17 境界補正
- docs/MMD_Audio_WAV_Compatibility_Specification.md の「MS16初期対応」表記確認・補正
- .agent/skills/build-packaging-verification/SKILL.md の文字化け修正を、まとまった整備コミットに含めるか判断
```

## 4. Out of Scope

```text
- mp3 / m4a 入力本実装
- FFmpeg / ffprobe 実装
- 解析用WAV生成
- MMD用WAV同時出力
- 配布ビルドcloseout
- MS17実装開始
- 母音イベント編集本体
- プリセット保存
- モデルプロファイル保存
```

## 5. 前提仕様書

```text
docs/MS16_and_Beyond_Milestone_Map_for_Antigravity.md
docs/GUI_State_Theme_Specification.md
docs/Pipeline_Data_Contract_Specification.md
docs/VMD_Output_Specification.md
docs/MMD_Audio_WAV_Compatibility_Specification.md
docs/Error_Handling_Specification.md
docs/Version_Control.md
docs/repo_milestone.md
README.md
```

## 6. 対象ファイル候補

```text
README.md
docs/Version_Control.md
docs/repo_milestone.md
docs/MS16_and_Beyond_Milestone_Map_for_Antigravity.md
docs/MMD_Audio_WAV_Compatibility_Specification.md
docs/MS16_Block_Breakdown_for_Antigravity.md
.agent/skills/build-packaging-verification/SKILL.md
tests/
```

実際の対象はB1〜B6の変更結果に従う。

## 7. 依存関係

```text
MS16-B1〜B6 完了後に実施する。
```

## 8. 実装方針

基本方針:

```text
- 実装済み内容を確認する
- docsと実装の差分を確認する
- MS16で実装した内容だけを完了扱いする
- MS17送りの音声拡張を実装済み扱いしない
- READMEはエンドユーザー向けに過剰な内部説明を避ける
- docsは開発者 / Antigravity 向けに詳細を記録する
```

MS16 closeout で記録すべき内容:

```text
- Qt / PySide6 排除状態
- wxPython主系の維持
- Preview変形台形表示復元
- 右ペイン基盤
- shape metadata
- 選択イベント下地
- テスト結果
- 手動確認結果
- MS17へ送る項目
- 残課題
```

## 9. テスト方針

全体テストを実行する。

```powershell
.venv\Scripts\python.exe -m pytest
```

可能であればGUI手動確認を行う。

```text
- アプリ起動
- TEXT読込
- WAV読込
- 解析
- Preview表示
- 再生
- Zoom In
- Zoom Out
- Reset Zoom
- Auto-follow
- テーマ切替
- VMD保存
- 入力再読込時のPreviewクリア
- 解析失敗時のPreviewクリア
- 右ペイン表示
```

Qt / PySide6 残存確認も行う。

```powershell
Select-String -Path .\requirements.txt, .\pyproject.toml -Pattern "PySide6|shiboken6|Qt"
Get-ChildItem -Recurse -File | Select-String -Pattern "from PySide6|import PySide6|QtWidgets|QtCore|QtGui"
```

## 10. 受け入れ条件

```text
- Qt / PySide6 が依存・import・配布対象から外れている
- wxPython主系が起動する
- Previewが変形台形系表示になっている
- Waveform / Preview / playback cursor / Viewport が同期する
- 右ペイン基盤が存在する
- Info / Warning / 選択イベント / プリセット / モデルプロファイルの枠がある
- shape metadata が将来選択に使える
- 選択イベント下地が存在する
- 編集機能は未実装として明確に残っている
- mp3 / m4a / FFmpeg / MMD用WAV はMS17送りとしてdocs上で整理されている
- MS16 closeout記録が追加されている
- 全テストまたは実行可能な範囲のテスト結果が記録されている
```

## 11. リスクと対策

### リスク

```text
- MS16 closeout時にMS17機能を実装済み扱いする
- docsの古い記述が残る
- 音声仕様書のMS16表記が後続作業を混乱させる
- Skill文字化け修正が漏れる
```

### 対策

```text
- 音声拡張は「仕様あり / 未実装 / MS17予定」と明記する
- READMEとdocsの対象読者を分ける
- docs/MMD_Audio_WAV_Compatibility_Specification.md のマイルストーン表記を確認する
- .agent/skills/build-packaging-verification/SKILL.md はまとまった整備コミット対象として扱う
```

## 12. GUI / Theme / Error Handling 確認事項

```text
- GUI追加部品のテーマ追従
- Preview / Waveform の古い表示残りなし
- Busy解除漏れなし
- エラー後に操作可能状態へ戻る
- 右ペイン表示が古い結果を保持しない
- 入力変更時に選択イベント表示がクリアされる
- 解析失敗時に選択イベント表示がクリアされる
```

## 13. Antigravity 実装時の注意

```text
MS16のcloseout作業です。
MS17相当の音声入力拡張・FFmpeg実装・MMD用WAV出力は開始しないでください。
実装済み / 未実装 / MS17送り / 将来課題を明確に分けてください。
```

---

## 10. MS17送りとして明示する項目

MS16では以下を実装しない。

これらは MS17 の対象として扱う。

```text
- wav / mp3 / m4a 入力対応
- m4a対応
- FFmpeg / ffprobe 接続
- 入力音声のffprobe検査
- 解析用WAV生成
- 解析用WAVを波形表示の正本にする処理
- MMD用WAV同時出力
- MMD互換WAV検証
- 音声変換系エラー分類の実装
- FFmpeg timeout / terminate / kill 制御
- 不完全なMMD用WAV削除
- FFmpeg同梱有無の判断
- FFmpegライセンス同梱整理
```

MS16のdocs補正では、これらを実装済み扱いしない。

---

## 11. MS16でユーザー判断が必要になり得る点

MS16-B1調査後に、以下についてユーザー判断が必要になる可能性がある。

### 11.1 旧 `src/gui/` の扱い

選択肢:

| 選択肢 | 内容 | 推奨 |
| --- | ------------------------ | ----- |
| A | 削除する | 推奨 |
| B | `docs/_old/` 等へ退避する | 次点 |
| C | repo内に残すが package 対象から外す | 非推奨寄り |
| D | そのまま残す | 非推奨 |

推奨は A または B。

理由:

```text
- Antigravityの誤参照を避けるため
- Qt / PySide6 再導入リスクを下げるため
- 配布対象を明確にするため
```

### 11.2 Preview復元時にwriter変更を許可するか

選択肢:

| 選択肢 | 内容 | 推奨 |
| --- | --------------------- | ---- |
| A | writerは原則変更しない | 推奨 |
| B | Preview整合に必要な最小変更のみ許可 | 条件付き |
| C | writer shape 全体を再設計する | 非推奨 |

推奨は A。
ただし、明確な不整合がある場合のみ B を検討する。

### 11.3 クリック選択をMS16-B6に含めるか

選択肢:

| 選択肢 | 内容 | 推奨 |
| --- | ---------------------- | ---- |
| A | 内部API / テスト用accessorのみ | 推奨 |
| B | クリック選択まで入れるが編集はしない | 条件付き |
| C | 編集まで入れる | 非対象 |

推奨は A。
MS16では下地整備に留める方が安全である。

---

## 12. MS16完了後に進むべきMS17の概要

MS16完了後、MS17では以下へ進む。

```text
MS17: wav / mp3 / m4a 入力対応 + MMD用WAV同時出力

主対象:
- FFmpeg / ffprobe 接続
- 入力拡張子 .wav / .mp3 / .m4a
- 入力ファイルサイズ上限 500MB
- 音声長上限 15分
- 解析用WAV生成
- 解析用WAVを波形表示の正本にする
- MMD用WAV同時出力
- MMD互換WAV検証
- 音声変換エラー処理
- 不完全ファイル削除
- GUI状態・Busy・Warning表示との統合
```

MS17では以下の仕様書を正本として扱う。

```text
docs/MMD_Audio_WAV_Compatibility_Specification.md
docs/Error_Handling_Specification.md
docs/Pipeline_Data_Contract_Specification.md
docs/GUI_State_Theme_Specification.md
docs/Security_Safety_Specification.md
docs/Release_Package_Manifest.md
```

---

## 13. Antigravity共通報告形式

各Block完了時、Antigravity は以下の形式で報告する。

```text
1. 実施したBlock
2. 確認したファイル
3. 変更したファイル
4. 実行したコマンド
5. 実行したテスト
6. テスト結果
7. GUI確認結果
8. Theme確認結果
9. Error / Busy / late callback 関連確認結果
10. 仕様書との差分
11. 残課題
12. 次Blockへ進めるか
```

B1のように実装しないBlockでは、`変更したファイル` は `なし` とする。

---

## 14. 変更履歴

### 2026-05-01 / 初版

* MS16を安全な7Blockへ分解した。
* 音声拡張、mp3対応、m4a対応、FFmpeg / ffprobe、解析用WAV生成、MMD用WAV同時出力は MS17 へ送る方針を明記した。
* MS16の主対象を、wxPython一本化、Qt / PySide6 排除、Preview変形台形表示復元、右ペインGUI基盤、Preview shape data contract、母音イベント選択下地、closeout に限定した。
* 各Blockに目的、背景、In Scope、Out of Scope、前提仕様書、対象ファイル候補、依存関係、実装方針、テスト方針、受け入れ条件、リスクと対策、GUI / Theme / Error Handling 確認事項、Antigravity実装時の注意を定義した。

### 2026-05-11 / MS16-B7 完了反映

* MS16-B7 の「統合確認 / Docs補正 / MS16 Closeout」を実施し、MS16 全Blockを完了状態としてクローズした。
