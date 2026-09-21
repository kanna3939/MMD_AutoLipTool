# MS16-B6 Implementation Plan

## 1. 文書情報

- 文書名: `MS16-B6 Implementation Plan`
- 推奨ファイル名: `docs/Implementation_Plan/MS16-B6_Implementation_Plan.md`
- 対象プロジェクト: `MMD_AutoLipTool`
- 対象リポジトリ: `https://github.com/kanna3939/MMD_AutoLipTool`
- 対象マイルストーン: `MS16`
- 対象Block: `MS16-B6`
- Block名: `母音イベント選択の下地`
- 主対象GUI: `wxPython`
- 旧GUI系: `Qt / PySide6` は再導入しない
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

MS16-B2 までで、Qt / PySide6 系依存と旧GUI実装は削除され、現行GUI主系は `src/gui_wx/` に一本化された。

MS16-B3 では、将来の情報表示・警告表示・選択イベント情報・プリセット・モデルプロファイルを受け止める右ペイン型GUI基盤を追加する。

MS16-B4 では、wxPython主系の Preview 表示を、リボン型中心から `control_points` ベースの変形台形 / 三角形 / 簡易エンベロープ表示へ戻す。

MS16-B5 では、Preview shape data contract を固定し、Preview shape が `source_event_index`, `shape_kind`, `control_points`, `frame_range`, `value_range` などの情報を持てる状態にする。

MS16-B6では、B5で固定した契約を使い、Preview shape と timing event の対応関係をもとに、**母音イベント選択の下地** を整える。

ただし、MS16-B6は編集機能のBlockではない。  
B6で扱うのは、選択状態の内部保持、読み取り専用の選択イベント概要表示、選択状態のクリア条件、将来の hit-test / 編集へ進むための最小基盤である。

---

## 3. 目的

MS16-B6の目的は、Preview上の shape と timing event の対応を使い、将来の母音イベント選択・軽微編集に進める下地を作ることである。

主目的は以下である。

```text
- Preview shape と timing event の対応を利用できるようにする
- selected shape / selected event 相当の内部状態を持てるようにする
- source_event_index から選択中イベント概要を取得できるようにする
- RightPane の「選択イベント」タブへ読み取り専用情報を表示できるようにする
- 入力変更 / 解析失敗 / timing plan 無効化時に選択状態をクリアする
- 古い timing plan 由来の選択状態を現在結果として扱わない
- B6時点では編集機能を実装しない
```

MS16-B6完了後、後続の MS21 以降で、母音イベント単位の軽微編集や発音単位調整へ進むための最低限の接続点ができている状態を目標とする。

---

## 4. In Scope

MS16-B6では以下を対象とする。

```text
- Preview shape と timing event の対応確認
- source_event_index を利用した選択対象解決
- PreviewPanel 側の選択状態保持
- UiState または MainFrame 側の最小選択状態保持
- selected_event_index / selected_shape_index 相当の内部状態
- 選択状態を設定する public helper
- 選択状態をクリアする public helper
- 選択中イベントの読み取り専用summary生成
- RightPane の「選択イベント」タブへの最小表示連携
- 入力変更時の選択状態クリア
- 解析失敗時の選択状態クリア
- timing plan 無効化時の選択状態クリア
- Preview clear 時の選択状態クリア
- 古いworker結果破棄時に選択状態を更新しないことの確認
- B6用テスト追加
- 既存Preview / RightPane関連テストの必要最小限の更新
```

---

## 5. Out of Scope

MS16-B6では以下を行わない。

```text
- 母音イベント編集
- モーフ値変更
- start_sec / end_sec の変更
- control_points のドラッグ編集
- Preview上の本格的なhit-test実装
- Preview上のマウスクリック選択本実装
- drag編集
- Undo / Redo
- 編集値保存
- VMD再生成UI
- VMD writer shape ロジックの変更
- Warning判定本体
- 出力診断レポート本体
- プリセット保存
- モデルプロファイル保存
- mp3入力対応
- m4a入力対応
- FFmpeg / ffprobe 接続
- 解析用WAV生成
- MMD用WAV同時出力
- MMD互換WAV検証
```

MS16-B6では、選択の「内部基盤」と「読み取り専用表示」までに限定する。  
ユーザーがPreviewをクリックして選択する本格UIは、必要に応じて後続BlockまたはMS21以降で扱う。

---

## 6. 前提条件

### 6.1 作業前提

```text
- 作業branchは feature/MS16
- MS16-B2が完了済みである
- Qt / PySide6 は削除済みである
- 旧 src/gui/ は削除済みである
- preview_transform.py は src/core/preview_transform.py に移動済みである
- 現行GUI主系は src/gui_wx/ である
```

### 6.2 MS16-B3 / B4 / B5との関係

MS16-B6は、原則として MS16-B3, B4, B5 完了後に実施する。

```text
MS16-B3:
- RightPane基盤がある
- 選択イベントタブがある
- selected event summary を表示できる helper がある、または追加可能である

MS16-B4:
- Preview shape が control_points ベースで表示される
- PreviewPanel が shape を受け取れる

MS16-B5:
- Preview shape contract が固定されている
- source_event_index または同等のevent参照がある
- shape_kind / frame_range / value_range が利用可能である
```

B5が未完了の場合、B6を開始しない。

理由:

```text
B6は、B5で固定した Preview shape contract を利用して選択状態の下地を作るBlockであるため。
```

### 6.3 Git状態に関する前提

作業開始時に以下を確認する。

```powershell
git status
git branch
git log --oneline -n 10
git diff --stat
git diff --name-only
git diff --cached --stat
git diff --cached --name-only
```

判定:

```text
- B2 / B3 / B4 / B5 の差分が未コミットで残っている場合は、B6実装を開始しない
- B6差分はB6対象に限定する
- staged差分とunstaged差分を区別して報告する
```

---

## 7. 対象ファイル

MS16-B6で変更対象となる候補は以下である。

```text
src/core/preview_transform.py
src/gui_wx/preview_panel.py
src/gui_wx/right_pane.py
src/gui_wx/main_frame.py
src/gui_wx/ui_state.py
src/gui_wx/app_controller.py

tests/test_wx_ms16_b6_event_selection_foundation.py
tests/test_wx_ms16_b5_preview_contract.py
tests/test_wx_ms16_b4_preview_shape.py
tests/test_preview_transform.py

docs/Version_Control.md
docs/repo_milestone.md
```

主対象は以下である。

```text
src/gui_wx/preview_panel.py
src/gui_wx/right_pane.py
src/gui_wx/main_frame.py
src/gui_wx/ui_state.py
tests/test_wx_ms16_b6_event_selection_foundation.py
```

`src/core/preview_transform.py` は、B5契約に不足が見つかった場合のみ最小変更する。  
B6では、preview transform のshape契約を大きく変更しない。

docs更新は最小限とする。  
MS16-B6単体の実装記録として必要な場合のみ、`docs/Version_Control.md` または `docs/repo_milestone.md` に短い記録を追加する。

---

## 8. 実装方針

### 8.1 基本方針

MS16-B6では、母音イベント選択の下地を作る。

基本方針は以下。

```text
- 正本は timing plan とする
- Preview shape は timing plan から派生する
- 選択状態は現在の timing plan / preview data に対応するものだけ有効とする
- 古い timing plan 由来の選択状態は使わない
- B6では編集しない
- B6では本格 hit-test を実装しない
- B6ではクリック選択UIを必須にしない
- 読み取り専用の選択summary表示を優先する
```

### 8.2 選択状態の推奨構造

B6で扱う選択状態は、最小限とする。

候補:

```text
selected_shape_index
selected_event_index
selected_source_event_index
selected_shape_kind
```

推奨は以下。

```text
selected_source_event_index
```

理由:

```text
- B5で固定した source_event_index を利用できる
- timing event との対応が明確
- shape list の並び替えにやや強い
- B6時点ではevent id体系を新設しすぎない方が安全
```

ただし、実装上 shape list のindexも必要な場合は、`selected_shape_index` を補助的に持ってよい。

### 8.3 選択状態を持つ場所

選択状態の保持場所は、現行設計に合わせる。

候補:

```text
UiState
MainFrame
PreviewPanel
```

推奨方針:

```text
- PreviewPanel:
  - 描画上の選択ハイライトや selected shape index を保持してよい

- UiState:
  - アプリ全体で参照する selected_source_event_index を持たせる場合は、最小限にする

- MainFrame:
  - PreviewPanel と RightPane の橋渡しを行う
```

B6では、過剰な状態管理を避ける。  
後続の編集機能で複雑化する可能性があるため、選択状態は読み取り専用用途に限定する。

### 8.4 選択操作の扱い

B6では、本格的なマウスクリック選択を必須にしない。

推奨実装:

```text
- select_preview_shape_by_source_event_index(index) のような内部helperを用意する
- clear_preview_selection() を用意する
- テストから選択状態を設定できる
- RightPaneへ選択summaryを表示できる
```

マウスクリック選択は、以下の条件をすべて満たす場合のみ最小実装してよい。

```text
- hit-testが簡単かつ安全に実装できる
- 既存Preview描画を壊さない
- 編集機能へ踏み込まない
- テストで安定確認できる
```

ただし、標準方針は **内部API / テスト用accessor中心** とする。

### 8.5 選択中イベントsummary

RightPane の「選択イベント」タブへ、読み取り専用のsummaryを表示する。

表示候補:

```text
- morph_name
- vowel
- source_event_index
- shape_kind
- start_sec
- end_sec
- duration_sec
- peak_value
- frame_range
- value_range
- fallback_reason
- is_short_span
- is_zero_peak
```

B6では、すべての項目を必ず表示する必要はない。  
ただし、将来の編集に必要な最低限の情報が確認できることを重視する。

推奨最小表示:

```text
morph_name
source_event_index
shape_kind
start_sec
end_sec
peak_value
frame_range
```

### 8.6 選択状態クリア条件

以下の場合、選択状態を必ずクリアする。

```text
- TEXT再読込
- 音声再読込
- 解析開始
- 解析失敗
- 解析キャンセル
- timing plan無効化
- Preview dataクリア
- Preview data更新
- 古いworker結果破棄
- パラメータ変更による再解析待ち
```

B6では、古い選択情報を現在の選択として見せないことが重要である。

### 8.7 PreviewPanelハイライト方針

B6では、選択中shapeの視覚的ハイライトは任意とする。

許容される最小実装:

```text
- selected shape を内部状態として保持する
- Refreshする
- 描画上はまだ明確なハイライトを出さなくてもよい
```

表示ハイライトを入れる場合の方針:

```text
- ThemePaletteの既存色を使う
- 新規色追加は最小限
- shape描画を壊さない
- 選択状態がない場合は既存表示と同じ
```

B6の主目的は選択の下地であり、視覚表現の作り込みではない。

### 8.8 RightPane連携方針

B3で追加した RightPane の「選択イベント」タブへ、選択summaryを流し込む。

方針:

```text
- MainFrameがPreviewPanelの選択状態を受け取る
- MainFrameがRightPane helperを呼ぶ
- RightPaneは読み取り専用表示に留める
- RightPaneの表示を正本にしない
```

RightPane側に必要なhelper候補:

```text
set_selected_event_summary(text: str) -> None
clear_selected_event() -> None
```

既にB3で実装済みなら、それを利用する。  
未実装または不足している場合は、B6で最小補修する。

---

## 9. 詳細ステップ

### Step 1: 作業前git状態確認

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

```text
- MS16-B2 / B3 / B4 / B5 の差分が残っていないか
- working tree がクリーンか
- B6以外の変更が混入していないか
```

MS16-B5の差分が未コミットで残っている場合は、B6実装に入らず報告する。

### Step 2: B5後のPreview shape contract確認

確認対象。

```text
src/core/preview_transform.py
src/gui_wx/preview_panel.py
tests/test_wx_ms16_b5_preview_contract.py
```

確認すること。

```text
- source_event_index が存在する
- shape_kind が存在する
- frame_range が存在する
- value_range が存在する
- selected summaryに使える情報がある
```

不足がある場合は、B6で大きくcontract変更せず、B5補修対象として報告する。  
軽微な不足ならB6内で最小補修してよい。

### Step 3: PreviewPanelの選択状態保持を追加

`src/gui_wx/preview_panel.py` に、選択状態の最小保持を追加する。

候補:

```text
self._selected_source_event_index
self._selected_shape_index
```

推奨 helper:

```text
set_selected_source_event_index(index: int | None) -> None
clear_selection() -> None
get_selected_source_event_index() -> int | None
```

方針:

```text
- 不正indexの場合は安全に無視またはclearする
- 選択状態変更時は Refresh() する
- Preview dataが空の場合は選択できない
- Preview data更新時は選択状態をclearする
```

### Step 4: source_event_index から shape を解決する helper を追加

PreviewPanel または関連helperに、選択対象を解決する処理を追加する。

候補:

```text
find_shape_by_source_event_index(index)
get_selected_shape_summary()
```

B6では、描画上のhit-testではなく、metadataからの解決を優先する。

確認すること。

```text
- source_event_index が存在するshapeを検索できる
- 該当shapeがない場合は None を返す
- 複数shapeが該当する場合の扱いを決める
```

複数shapeが同一eventに対応する可能性がある場合は、B6では最初のshapeまたは代表shapeを返す。  
複数shape対応の厳密化は後続で検討する。

### Step 5: 選択summary生成を追加

選択されたshapeから読み取り専用summaryを生成する。

候補項目。

```text
morph_name
vowel
source_event_index
shape_kind
start_sec
end_sec
duration_sec
peak_value
frame_range
value_range
fallback_reason
is_short_span
is_zero_peak
```

summaryは、RightPaneへ渡しやすい文字列でもよい。  
将来の拡張を考えると、内部的には dict / dataclass で持ち、RightPane表示時に文字列化する形が望ましい。

B6の推奨:

```text
- 内部では shape metadata を保持
- 表示用に format_selected_event_summary(shape) を用意
```

### Step 6: UiStateまたはMainFrameへの選択状態接続

現行設計に合わせて、選択状態を MainFrame から扱えるようにする。

候補:

```text
MainFrame.select_event_by_source_index(index)
MainFrame.clear_selected_event()
MainFrame.update_selected_event_display()
```

または、AppController 経由が現行設計に合う場合は、Controller側に最小メソッドを追加する。

方針:

```text
- B6では過剰にControllerへ寄せない
- 既存設計に合わせる
- 選択状態は読み取り専用表示のための状態に留める
```

### Step 7: RightPaneの選択イベントタブへ表示連携

B3で追加した RightPane helper を使う。

候補:

```text
right_pane.set_selected_event_summary(text)
right_pane.clear_selected_event()
```

表示内容:

```text
選択中のイベントはありません。
```

または、選択時:

```text
Morph: あ
Event Index: 3
Shape: trapezoid
Time: 1.20s - 1.48s
Peak: 0.72
Frame: 36 - 44
```

文言は既存UI方針に合わせる。  
B6では、正確性と読み取りやすさを優先し、凝った表示は不要。

### Step 8: 選択状態クリア条件を接続

以下の既存処理箇所を確認し、選択状態クリアを追加する。

```text
- Preview data clear
- Preview data update
- analysis invalidation
- input reload
- analysis failed
- analysis cancelled
- parameter changed
- old worker result discard
```

実装上の関数名は現行コードに従う。

重要:

```text
古いPreviewがクリアされる場面では、選択状態とRightPane選択表示もクリアする。
```

### Step 9: Optional: 選択ハイライトの最小表示

B6では任意。

ハイライトを実装する場合:

```text
- selected shape の枠線を少し強調する
- ThemePaletteの既存色を使う
- 選択なしの場合は既存表示と同じ
- Refresh() を呼ぶ
```

ハイライトが不安定または過剰になる場合は、B6では見送ってよい。  
その場合でも、内部選択状態とRightPane表示が成立していればB6の目的は満たす。

### Step 10: B6用テスト追加

推奨テストファイル。

```text
tests/test_wx_ms16_b6_event_selection_foundation.py
```

テスト観点。

```text
- Preview shape から source_event_index を取得できる
- set_selected_source_event_index で選択状態が更新される
- clear_selection で選択状態が消える
- 不正indexで例外が出ない
- 選択summaryが生成できる
- RightPaneの選択イベント表示を更新できる
- Preview data更新時に選択状態がクリアされる
- Preview clear時に選択状態がクリアされる
```

GUI描画のピクセル一致は行わない。

### Step 11: 既存テスト更新

必要に応じて以下を更新する。

```text
tests/test_wx_ms16_b5_preview_contract.py
tests/test_wx_ms16_b4_preview_shape.py
tests/test_wx_ms15_b2_preview.py
tests/test_preview_transform.py
```

更新方針。

```text
- B5 contractを壊さない
- B4のcontrol_points表示を壊さない
- 旧fallback前提に戻さない
```

### Step 12: 軽量確認・テスト実行

まず compileall を実行する。

```powershell
.\.venv\Scripts\python.exe -m compileall .\src
```

B6対象テストを実行する。

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_wx_ms16_b6_event_selection_foundation.py
```

Preview関連テストを実行する。

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_wx_ms16_b5_preview_contract.py tests\test_wx_ms16_b4_preview_shape.py
```

RightPane関連テストを実行する。

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_wx_ms16_b3_right_pane.py
```

必要に応じてwx系軽量テストも実行する。

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_wx_ms15_b5_state_theme.py
```

全体pytestは、ハング対策がある場合のみ実行する。

```powershell
.\.venv\Scripts\python.exe -m pytest
```

ハングした場合は、B6の失敗と即断せず、停止箇所と原因候補を報告する。

### Step 13: PySide6 / 旧gui参照が戻っていないか確認

B2後の状態を壊していないか確認する。

```powershell
Get-ChildItem -Recurse -File |
  Where-Object { $_.Extension -in ".py", ".toml", ".txt", ".ps1", ".spec", ".md" } |
  Select-String -Pattern "from PySide6|import PySide6|QtWidgets|QtCore|QtGui|shiboken6|from gui\.|import gui"
```

確認すること。

```text
- PySide6 / Qt import が戻っていない
- 旧 src/gui/ 参照が戻っていない
- src/core/preview_transform.py を参照している
```

### Step 14: 最終git差分確認

```powershell
git status
git diff --stat
git diff --name-only
git diff --cached --stat
git diff --cached --name-only
```

確認すること。

```text
- B6対象ファイルに収まっている
- Preview selection / RightPane selected event / tests 以外に不要変更がない
- writer shape ロジックを変更していない
- 音声拡張に変更が入っていない
- PySide6 / Qt / 旧gui参照が戻っていない
```

---

## 10. 状態遷移 / データ契約

MS16-B6では、選択状態に関する最小契約を追加する。  
ただし、pipeline の正本は変更しない。

### 10.1 変更しない契約

```text
- Pipelineの正本は timing plan
- Preview data は timing plan からの派生物
- VMD writer input は timing plan からの派生物
- VMD keyframe はwriterの出力結果であり、pipeline正本ではない
- observation は補助情報であり、timeline event の代替正本ではない
- input identity / job id による古いworker結果破棄を維持する
```

### 10.2 B6で追加する選択状態契約

```text
SelectionState:
  selected_source_event_index
  selected_shape_index optional
  selected_shape_summary optional
```

契約:

```text
- 選択状態は現在の Preview data / timing plan に対応する場合のみ有効
- source_event_index は現在の timing event list に対応する
- Preview data更新時は選択状態をクリアする
- timing plan無効化時は選択状態をクリアする
- 古いworker結果から選択状態を更新しない
```

### 10.3 RightPane表示契約

```text
RightPane の選択イベント表示は補助表示である。
RightPane表示を正本にしてはならない。
RightPane表示から timing plan を復元してはならない。
RightPane表示から writer input を生成してはならない。
```

### 10.4 PreviewPanel選択契約

```text
PreviewPanel は選択状態を表示または保持してよい。
ただし、選択状態はPreview表示用の補助状態であり、pipeline正本ではない。
```

### 10.5 クリア契約

以下では選択状態をクリアする。

```text
- set_preview_data
- clear_preview_data
- invalidate_analysis
- input reload
- analysis failure
- analysis cancel
- parameter change
- stale worker discard
```

実装上の関数名は現行コードに従う。

---

## 11. テスト方針

### 11.1 優先テスト

B6では以下を優先する。

```text
1. compileall
2. Preview selection単体テスト
3. RightPane selected event表示テスト
4. Preview contractテスト
5. Preview shapeテスト
6. 既存wx系軽量テスト
```

### 11.2 推奨テスト観点

```text
- selected_source_event_index を設定できる
- selected_source_event_index を取得できる
- clear_selection できる
- 不正indexで例外が出ない
- source_event_index からshapeを解決できる
- 選択summaryを生成できる
- RightPaneへsummaryを表示できる
- Preview data更新時に選択が消える
- Preview clear時に選択が消える
- input invalidation時に選択が消える
```

### 11.3 ピクセル一致テストについて

B6ではピクセル完全一致のスクリーンショットテストは行わない。

理由:

```text
- wxPythonの描画は環境差が出やすい
- B6の目的は選択状態の下地であり、見た目の完全一致ではない
- ハイライト表示は任意であり、主目的ではない
```

### 11.4 全体pytestの扱い

B1以降、全体pytestがGUI/ダイアログ起因でハングする可能性がある。

そのため、B6では全体pytestを絶対条件にしない。

実行できる場合のみ以下を行う。

```powershell
.\.venv\Scripts\python.exe -m pytest
```

ハングした場合は、以下を報告する。

```text
- 停止したテスト
- GUI初期化 / ダイアログ起因か
- B6変更に起因する可能性があるか
- B6対象テストは通っているか
```

---

## 12. 受け入れ条件

MS16-B6の受け入れ条件は以下である。

```text
- Preview shape から source_event_index を参照できる
- PreviewPanel または関連層で selected_source_event_index を保持できる
- 選択状態を設定するhelperがある
- 選択状態をクリアするhelperがある
- 不正indexで例外が出ない
- 選択中shape / event のsummaryを生成できる
- RightPane の選択イベントタブに読み取り専用summaryを表示できる
- Preview data更新時に選択状態がクリアされる
- Preview clear時に選択状態がクリアされる
- timing plan無効化時に選択状態がクリアされる
- 古いworker結果から選択状態が更新されない
- B5のPreview shape contractを壊していない
- B4の変形台形表示を壊していない
- B3のRightPane基盤を壊していない
- VMD writer shape ロジックを変更していない
- compileall が通る
- B6対象テストが通る
- 関連Preview / RightPaneテストが通る
- PySide6 / Qt / 旧 src/gui 参照が戻っていない
- mp3 / m4a / FFmpeg / MMD用WAV変更が混入していない
```

---

## 13. リスクと対策

### 13.1 リスク: B6で編集機能まで実装してしまう

対策:

```text
- B6は選択状態と読み取り専用summary表示に限定する
- start/end/peak/control_points の変更は行わない
- 編集保存やVMD再生成は実装しない
```

### 13.2 リスク: hit-test本実装へ踏み込みすぎる

対策:

```text
- B6では内部API / テスト用accessor中心とする
- クリック選択は必須にしない
- hit-test bounds の正式化は後続へ送る
```

### 13.3 リスク: 選択状態が古いtiming planに残る

対策:

```text
- Preview data更新時にclearする
- timing plan無効化時にclearする
- input reload時にclearする
- stale worker discard時にUIへ反映しない
```

### 13.4 リスク: RightPane表示を正本扱いしてしまう

対策:

```text
- RightPaneは補助表示と明記する
- RightPane表示からpipelineデータを復元しない
- RightPane表示からwriter inputを作らない
```

### 13.5 リスク: B5 contractを壊す

対策:

```text
- B5対象テストを継続実行する
- source_event_index / shape_kind / control_points の意味を変更しない
- B6では選択状態の追加に留める
```

### 13.6 リスク: B4のPreview表示を壊す

対策:

```text
- B4対象テストを継続実行する
- 選択ハイライトを入れる場合も既存shape描画を壊さない
- ハイライトが不安定ならB6では見送る
```

### 13.7 リスク: 旧Qt / PySide6参照が戻る

対策:

```text
- 旧 src/gui/ は参照しない
- PySide6 / Qt import 残存検索を実行する
- src/core/preview_transform.py を使う
```

---

## 14. Antigravity 実装時の注意

Antigravity は以下を厳守すること。

```text
今回は MS16-B6 の scoped implementation です。

目的は、母音イベント選択の下地を作ることです。
B6では、選択状態の内部保持、読み取り専用summary生成、RightPaneの選択イベントタブへの最小表示連携までを行います。

正本は timing plan です。
Preview shape は timing plan から派生する表示・選択準備用データです。
RightPane表示は補助表示です。

旧 src/gui/ は参照しないでください。
Qt / PySide6 を再導入しないでください。
preview_transform は src/core/preview_transform.py を使用してください。

B6では以下を行わないでください。
- 母音イベント編集
- start_sec / end_sec の変更
- peak_value の変更
- control_points のドラッグ編集
- hit-test本実装
- Previewクリック選択の本格実装
- VMD writer shape ロジックの変更
- VMD再生成UI
- Warning判定本体
- プリセット保存
- モデルプロファイル保存
- mp3 / m4a 入力対応
- FFmpeg / ffprobe 接続
- 解析用WAV生成
- MMD用WAV同時出力
```

---

## 15. Antigravity 作業開始用プロンプト

以下を Antigravity に渡す想定とする。

```text
MS16-B6: 母音イベント選択の下地 を実施してください。

今回は scoped implementation です。
目的は、B5で固定した Preview shape data contract を使い、将来の母音イベント選択・軽微編集に進める下地を作ることです。

前提:
- MS16-B2は完了済みです。
- Qt / PySide6 は削除済みです。
- 旧 src/gui/ は削除済みです。
- preview_transform は src/core/preview_transform.py に移動済みです。
- MS16-B3が完了済みであることを確認してください。
- MS16-B4が完了済みであることを確認してください。
- MS16-B5が完了済みであることを確認してください。
- 旧 src/gui/ を参照しないでください。
- Qt / PySide6 を再導入しないでください。

作業開始時に以下を実行してください。

```powershell
git status
git branch
git log --oneline -n 10
git diff --stat
git diff --name-only
git diff --cached --stat
git diff --cached --name-only
```

MS16-B2 / B3 / B4 / B5 の差分が未コミットで残っている場合は、B6実装を開始せず、状況を報告してください。
B2/B3/B4/B5差分とB6差分を混在させないでください。

実施内容:
1. `src/core/preview_transform.py` と `src/gui_wx/preview_panel.py` で、B5の Preview shape contract を確認する。
2. `source_event_index` を使って Preview shape と timing event の対応を解決できるようにする。
3. `PreviewPanel` または関連層に selected_source_event_index 相当の最小選択状態を追加する。
4. 選択状態を設定する helper を追加する。
5. 選択状態をクリアする helper を追加する。
6. 不正indexで例外が出ないようにする。
7. 選択中shape / event の読み取り専用summaryを生成できるようにする。
8. B3で追加された RightPane の「選択イベント」タブへsummaryを表示できるようにする。
9. Preview data更新時、Preview clear時、timing plan無効化時に選択状態をクリアする。
10. 古いworker結果から選択状態が更新されないことを確認する。
11. B6用の軽量テストを追加する。
12. compileall と関連テストを実行する。
13. PySide6 / Qt / 旧 src/gui 参照が戻っていないか確認する。

B6では以下を行わないでください。
- 母音イベント編集
- start_sec / end_sec の変更
- peak_value の変更
- control_points のドラッグ編集
- hit-test本実装
- Previewクリック選択の本格実装
- VMD writer shape ロジックの変更
- VMD再生成UI
- Warning判定本体
- プリセット保存
- モデルプロファイル保存
- mp3 / m4a 入力対応
- FFmpeg / ffprobe 接続
- 解析用WAV生成
- MMD用WAV同時出力

確認コマンド例:

```powershell
.\.venv\Scripts\python.exe -m compileall .\src
.\.venv\Scripts\python.exe -m pytest tests\test_wx_ms16_b6_event_selection_foundation.py
.\.venv\Scripts\python.exe -m pytest tests\test_wx_ms16_b5_preview_contract.py tests\test_wx_ms16_b4_preview_shape.py
.\.venv\Scripts\python.exe -m pytest tests\test_wx_ms16_b3_right_pane.py

Get-ChildItem -Recurse -File |
  Where-Object { $_.Extension -in ".py", ".toml", ".txt", ".ps1", ".spec", ".md" } |
  Select-String -Pattern "from PySide6|import PySide6|QtWidgets|QtCore|QtGui|shiboken6|from gui\.|import gui"
```

全体pytestは、過去にGUI/ダイアログ周りでハング実績があります。
B6では全体pytestに固執せず、compileall、B6対象テスト、Preview関連テスト、RightPane関連テスト、既存wx系の軽量テストを優先してください。
全体pytestを実行してハングした場合は、強制終了し、ハング箇所と原因候補を報告してください。

完了報告では以下を報告してください。

- 実行したコマンド
- 変更したファイル
- 新規作成したテスト
- 選択状態の保持場所
- selected_source_event_index の扱い
- source_event_index からshape/eventを解決する方法
- 選択summaryの内容
- RightPane選択イベントタブへの連携方法
- 選択状態クリア条件
- Preview data更新 / clear時の挙動
- 古いworker結果への対応
- 実行したテスト
- テスト結果
- PySide6 / Qt / 旧 src/gui 参照残存確認結果
- writer shapeロジックを変更していないこと
- MS17対象変更が混入していないこと
- 最終 git diff --stat

---

## 16. 完了報告形式

Antigravity は作業完了時に以下の形式で報告する。

```text
## MS16-B6 実装報告

### 1. 実行したコマンド

### 2. 作業前git状態
- branch:
- latest commit:
- working tree:

### 3. 変更したファイル

### 4. 新規作成したファイル

### 5. 選択状態の保持場所
- PreviewPanel:
- UiState:
- MainFrame:
- AppController:

### 6. selected_source_event_index
- 追加有無:
- 意味:
- 不正indexの扱い:
- clear条件:

### 7. shape / event 解決
- source_event_indexからshape解決:
- event summary生成:
- 複数shape対応:
- shapeがない場合:

### 8. RightPane連携
- 使用したhelper:
- 表示内容:
- clear表示:
- RightPaneを正本扱いしていないこと:

### 9. 選択状態クリア条件
- Preview data更新:
- Preview clear:
- input reload:
- analysis failure:
- analysis cancel:
- timing plan invalidation:
- stale worker discard:

### 10. Preview表示への影響
- ハイライト実装有無:
- Refresh:
- B4表示への影響:
- B5 contractへの影響:

### 11. PySide6 / Qt / 旧gui参照確認
- PySide6:
- shiboken6:
- QtWidgets / QtCore / QtGui:
- from gui / import gui:

### 12. テスト結果
- compileall:
- B6対象テスト:
- B5 contractテスト:
- B4 preview shapeテスト:
- B3 RightPaneテスト:
- 既存wx系テスト:
- 全体pytest:

### 13. writer変更の有無
- writer変更:
- 変更した場合の理由:
- 変更していない場合の確認:

### 14. MS17対象変更の混入確認
- mp3 / m4a:
- FFmpeg / ffprobe:
- 解析用WAV:
- MMD用WAV:

### 15. 最終git状態
- git diff --stat:
- git diff --name-only:

### 16. 残課題
- B7へ送るdocs補正:
- MS21以降へ送る編集機能:
- 後続で検討すべきhit-test:
```

---

## 17. 完了後の次アクション

MS16-B6完了後、通常は以下へ進む。

```text
MS16-B7: 統合確認 / Docs補正 / MS16 Closeout
```

B7では、MS16-B1〜B6の成果を統合確認し、以下を整理する。

```text
- Qt / PySide6 排除状態
- wxPython主系維持
- RightPane基盤
- Preview変形台形表示
- Preview shape data contract
- 母音イベント選択の下地
- MS17送り項目
- docs上のMS16/MS17境界
- 残課題
```

ただし、以下の場合はB7へ進む前に補修する。

```text
- 選択状態が古いPreview dataに残る
- RightPaneの選択イベント表示が古い情報を残す
- B5 contractが壊れている
- B4 Preview表示が壊れている
- B3 RightPaneが壊れている
- writer shapeロジックが意図せず変更されている
- PySide6 / Qt / 旧 src/gui 参照が戻っている
- MS17対象変更が混入している
```

---

## 18. 変更履歴

### 2026-05-01 / 初版

- MS16-B1〜B5までの流れを踏まえ、MS16-B6の実装プランを作成。
- B6を「母音イベント選択の下地」に限定。
- `source_event_index` を使った Preview shape と timing event の対応、選択状態保持、RightPane選択イベントタブへの読み取り専用summary表示を主対象に定義。
- 母音イベント編集、hit-test本実装、クリック選択本格実装、writer変更、音声拡張はOut of Scopeに明記。
- Preview data更新、Preview clear、timing plan無効化、古いworker結果破棄時に選択状態をクリアする契約を定義。
- B7 closeoutへ進むための受け入れ条件を整理。
