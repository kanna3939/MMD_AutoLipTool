# MS16-B3 Implementation Plan

## 1. 文書情報

- 文書名: `MS16-B3 Implementation Plan`
- 推奨ファイル名: `docs/Implementation_Plan/MS16-B3_Implementation_Plan.md`
- 対象プロジェクト: `MMD_AutoLipTool`
- 対象リポジトリ: `https://github.com/kanna3939/MMD_AutoLipTool-dev`
- 対象マイルストーン: `MS16`
- 対象Block: `MS16-B3`
- Block名: `GUI Layout Foundation / Right Pane 基盤`
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

MS16-B2で実施済みの主な内容は以下である。

```text
- PySide6 / shiboken6 依存を requirements.txt / pyproject.toml から削除
- 旧 src/gui/ を削除
- src/test_gui.py を削除
- 旧PySide6依存テストを削除
- src/gui/preview_transform.py を src/core/preview_transform.py へ移動
- wxPython主系および対象テストの import を core.preview_transform へ修正
````

MS16-B3では、次段階として、将来の情報表示・警告表示・選択イベント情報・プリセット・モデルプロファイルを受け止める **右ペイン型GUI基盤** を追加する。

MS16-B3は、情報ペインの **枠・構造・view helper** を作るBlockであり、本格的な警告判定、母音イベント編集、プリセット保存、モデルプロファイル保存は実装しない。

---

## 3. 目的

MS16-B3の目的は、wxPython主系のメイン画面に右ペイン型の情報タブ領域を追加し、将来拡張の受け皿を作ることである。

主目的は以下。

```text id="krlbns"
- 右ペイン領域を追加する
- Info タブを用意する
- Warning タブを用意する
- 選択イベント タブを用意する
- プリセット タブを用意する
- モデルプロファイル タブを用意する
- 各タブに placeholder または読み取り専用の最小表示を置く
- 後続Blockで情報を流し込める view helper を整備する
- 既存の波形 / Preview / 再生 / Zoom / Viewport / Theme / State を壊さない
```

MS16-B3完了後、MS16-B4以降で Preview 変形台形表示復元や shape data contract 整理を行う際に、必要な情報を右ペインへ表示できる下地ができている状態を目標とする。

---

## 4. In Scope

MS16-B3では以下を対象とする。

```text id="fqz1sq"
- wxPython主系 MainFrame への右ペイン追加
- 右ペイン用の新規クラスまたは新規モジュール追加
- wx.Notebook または同等のタブUI追加
- Info タブの追加
- Warning タブの追加
- 選択イベント タブの追加
- プリセット タブの追加
- モデルプロファイル タブの追加
- 各タブの placeholder / 最小表示
- 各タブの clear / set 系 view helper
- ThemeManager との接続
- Layout / Refresh / Update の要否確認
- 既存 action state への影響確認
- 既存 Waveform / Preview 領域の維持
- 軽量GUIテストまたは構造確認テストの追加
```

---

## 5. Out of Scope

MS16-B3では以下を行わない。

```text id="v11g3x"
- Warning判定本体
- 出力診断レポート本体
- 母音イベント選択ロジック本体
- 母音イベント編集
- Previewクリック選択
- ドラッグ編集
- プリセット保存
- プリセット編集
- モデルプロファイル保存
- モデルプロファイル編集
- mp3入力対応
- m4a入力対応
- FFmpeg / ffprobe 接続
- 解析用WAV生成
- MMD用WAV同時出力
- MMD互換WAV検証
- Preview変形台形表示の復元
- Preview shape data contract の修正
- VMD writer shape ロジックの変更
```

特に、MS16-B3は **右ペイン基盤のみ** を扱う。
Preview表示改善は MS16-B4、shape metadata整理は MS16-B5、母音イベント選択の下地は MS16-B6 で扱う。

---

## 6. 前提条件

### 6.1 作業前提

```text id="igptol"
- 作業branchは feature/MS16
- MS16-B2が完了済みである
- 旧 src/gui/ は削除済みである
- PySide6 / shiboken6 依存は削除済みである
- preview_transform.py は src/core/preview_transform.py に移動済みである
- 現行GUI主系は src/gui_wx/ である
```

### 6.2 Git状態に関する前提

MS16-B3開始時には、MS16-B2の変更がコミット済み、または少なくともB3作業と混ざらない状態で管理されている必要がある。

作業開始時に以下を確認する。

```powershell id="j6ikgs"
git status
git branch
git log --oneline -n 10
git diff --stat
git diff --name-only
git diff --cached --stat
git diff --cached --name-only
```

判定:

```text id="brqtd6"
- MS16-B2の差分が未コミットで残っている場合は、B3実装を開始せず、ユーザーへ報告する。
- B2差分とB3差分を混在させない。
- working tree がクリーン、またはB3用の作業開始状態として明確に分離されている場合のみ実装へ進む。
```

### 6.3 GUI前提

現行のGUIは以下を維持する。

```text id="qgwf76"
- 上部操作領域
- 左側 Info / 入力情報領域
- 中央 Waveform 領域
- 中央 Preview 領域
- 下部 Status 領域
- ThemeManager
- UiState
- AppController
- Viewport / Zoom / playback cursor
```

B3では既存導線を壊さない。

---

## 7. 対象ファイル

MS16-B3で変更対象となる候補は以下である。

```text id="r0wl5a"
src/gui_wx/main_frame.py
src/gui_wx/theme.py
src/gui_wx/ui_state.py
src/gui_wx/app_controller.py
src/gui_wx/placeholder_panels.py
src/gui_wx/info_panel.py
src/gui_wx/right_pane.py

tests/test_wx_ms16_b3_right_pane.py
tests/test_wx_ms16_b3_gui_layout.py

docs/Version_Control.md
docs/repo_milestone.md
```

実際の対象は、現行repo構成に従う。
`src/gui_wx/right_pane.py` が存在しない場合は、新規作成を推奨する。

docs更新は最小限とする。
MS16-B3単体の実装記録として必要な場合のみ、`docs/Version_Control.md` または `docs/repo_milestone.md` に短い記録を追加する。

---

## 8. 実装方針

### 8.1 基本方針

MS16-B3では、右ペインの構造を追加する。

基本方針は以下。

```text id="dwqtpn"
- 右ペインは src/gui_wx/right_pane.py に分離する
- MainFrame には右ペインを配置するための最小変更を加える
- 右ペインは wx.Notebook を基本候補とする
- 各タブは placeholder または読み取り専用の最小表示に留める
- ThemeManager によるテーマ追従を行う
- 既存の Waveform / Preview / playback / Zoom / Viewport を壊さない
```

### 8.2 推奨レイアウト

MS16-B3後の概念レイアウトは以下。

```text id="03epxh"
上部:
  TEXT読込 / WAV読込 / 解析 / 保存 / 再生 / Zoom / パラメータ操作

左:
  入力情報 / TEXT概要 / 音声概要

中央:
  Waveform
  Preview

右:
  RightPane
    - Info
    - Warning
    - 選択イベント
    - プリセット
    - モデルプロファイル

下部:
  Status
```

ただし、B3では見た目の完全固定を目的にしない。
目的は、後続Blockで拡張可能な構造を作ることである。

### 8.3 右ペインの推奨構成

新規ファイル候補:

```text id="fc29ic"
src/gui_wx/right_pane.py
```

推奨クラス構成:

```text id="bsb53n"
RightPane(wx.Panel)
  - notebook: wx.Notebook
  - info_panel
  - warning_panel
  - selected_event_panel
  - preset_panel
  - model_profile_panel
```

各タブ名の候補:

```text id="icpdob"
Info
Warning
選択イベント
プリセット
モデルプロファイル
```

タブ名は日本語UIとの整合を見て、既存GUIの言語方針に合わせる。
既存UIが英語中心の場合は、以下も許容する。

```text id="1g9avs"
Info
Warning
Selected Event
Preset
Model Profile
```

ただし、MS16-B3内で表記揺れを増やさない。

### 8.4 各タブのMS16-B3時点の表示内容

#### Info タブ

目的:

```text id="qhci40"
入力情報・解析概要・現在状態を表示する将来枠。
```

MS16-B3では以下でよい。

```text id="9t9j2n"
- placeholder text
- 現在は詳細情報なし
- 将来ここに入力情報や解析概要を表示する旨の短い文言
```

推奨 helper:

```text id="c4ygj1"
set_info_text(text: str) -> None
clear_info() -> None
```

#### Warning タブ

目的:

```text id="fw384h"
Warning / fallback / 診断情報を表示する将来枠。
```

MS16-B3では warning 判定を実装しない。

推奨 helper:

```text id="17k2g8"
set_warnings(items: list[str]) -> None
clear_warnings() -> None
```

MS16-B3時点では、空の場合に以下のような表示でよい。

```text id="ygm5px"
現在の警告はありません。
```

#### 選択イベント タブ

目的:

```text id="vu2ws2"
将来、Preview上で選択された母音イベント情報を表示する枠。
```

MS16-B3では選択ロジックを実装しない。

推奨 helper:

```text id="ru53ew"
set_selected_event_summary(text: str) -> None
clear_selected_event() -> None
```

初期表示:

```text id="r2lcua"
選択中のイベントはありません。
```

#### プリセット タブ

目的:

```text id="hfnl8q"
将来の生成設定プリセット表示・選択・編集の枠。
```

MS16-B3では保存や編集を実装しない。

推奨 helper:

```text id="eqqnjf"
set_preset_summary(text: str) -> None
clear_preset_summary() -> None
```

初期表示:

```text id="r57wr0"
プリセット機能は後続マイルストーンで対応予定です。
```

#### モデルプロファイル タブ

目的:

```text id="memfeg"
将来のMMDモデル別プロファイル表示・選択・編集の枠。
```

MS16-B3では保存や編集を実装しない。

推奨 helper:

```text id="pn3tsf"
set_model_profile_summary(text: str) -> None
clear_model_profile_summary() -> None
```

初期表示:

```text id="38l82g"
モデルプロファイル機能は後続マイルストーンで対応予定です。
```

### 8.5 Theme方針

右ペインと各タブは ThemeManager に接続する。

確認対象:

```text id="q16w2q"
- 背景色
- 文字色
- disabled文字色
- notebook背景
- panel背景
- border
- warning表示色
```

既存 `ThemePalette` に適切な色がある場合は再利用する。
新規色追加が必要な場合は最小限にする。

### 8.6 State方針

MS16-B3では、原則として `UiState` の大規模拡張は行わない。

許容される追加:

```text id="kiu1g9"
- 右ペイン表示用の最小状態
- 現在表示中の summary text
- warning list placeholder
```

ただし、以下はB6以降に送る。

```text id="qydbyn"
- selected_event_id
- selected_shape_id
- hit-test state
- event editing state
```

B3では、表示helperを中心に実装し、状態正本を増やしすぎない。

---

## 9. 詳細ステップ

### Step 1: 作業前git状態確認

```powershell id="92uqqn"
git status
git branch
git log --oneline -n 10
git diff --stat
git diff --name-only
git diff --cached --stat
git diff --cached --name-only
```

確認すること。

```text id="3kuz23"
- MS16-B2の差分が残っていないか
- working tree がクリーンか
- B3以外の変更が混入していないか
```

MS16-B2の差分が未コミットで残っている場合は、B3実装に入らず報告する。

### Step 2: 現行MainFrameレイアウト確認

確認対象。

```text id="xaljoc"
src/gui_wx/main_frame.py
src/gui_wx/placeholder_panels.py
src/gui_wx/info_panel.py
```

確認すること。

```text id="8eq8o4"
- 現在の root sizer
- 左ペイン / 中央ペイン / status の構造
- WaveformPanel と PreviewPanel の配置
- 右ペインを追加できる sizer
- Layout / Refresh の呼び出し箇所
- ThemeManager 適用箇所
```

このStepでは変更しない。

### Step 3: right_pane.py の新規作成

推奨ファイル。

```text id="e7w6h5"
src/gui_wx/right_pane.py
```

実装する主な要素。

```text id="761qpd"
- RightPane クラス
- wx.Notebook
- Info tab
- Warning tab
- Selected Event tab
- Preset tab
- Model Profile tab
- view helper
- clear helper
- apply_theme または同等のテーマ適用入口
```

最小構成例の概念。

```python id="hy6cph"
class RightPane(wx.Panel):
    def __init__(self, parent: wx.Window) -> None:
        super().__init__(parent)
        self.notebook = wx.Notebook(self)
        ...
```

実際のコードは既存 `src/gui_wx/` のスタイルに合わせる。

### Step 4: MainFrameへRightPaneを配置

`MainFrame` のレイアウトに `RightPane` を追加する。

方針。

```text id="rhm6p1"
- 既存の左ペイン / 中央ペインを壊さない
- Waveform / Preview の親子関係を不用意に変えない
- 右ペインは横方向に追加する
- 必要なら splitter または BoxSizer を使う
- 既存の最小サイズと表示バランスを確認する
```

B3での推奨は、過度なレイアウト再設計を避け、既存構造に右ペインを追加する最小変更である。

### Step 5: ThemeManagerとの接続

以下を確認し、必要な処理を追加する。

```text id="u5iagp"
- MainFrame のテーマ適用処理
- 子Windowへの再帰的テーマ適用
- RightPane / Notebook / 各タブの色
- placeholder text の文字色
```

既存の ThemeManager が再帰適用に対応している場合は、それを利用する。
RightPane固有のカスタム描画がない場合、RightPane側の `Refresh()` は最小限でよい。

### Step 6: view helper を整備

RightPaneに以下のような helper を追加する。

```text id="kogj2n"
set_info_text(text)
clear_info()

set_warnings(items)
clear_warnings()

set_selected_event_summary(text)
clear_selected_event()

set_preset_summary(text)
clear_preset_summary()

set_model_profile_summary(text)
clear_model_profile_summary()
```

実装は現行コードスタイルに合わせる。
B3では、helperが存在し、表示が更新できることを重視する。

### Step 7: MainFrameからRightPane helperへアクセスできるようにする

`MainFrame` 側で、必要に応じて以下を行う。

```text id="0n9cyn"
- self.right_pane を保持する
- 初期表示を設定する
- 入力読込時や解析成功時に無理に情報連携しない
- 既存InfoPanelとの責務衝突を避ける
```

B3では、既存InfoPanelとの統合・置換は行わない。
右ペインは将来拡張用の新領域として追加する。

### Step 8: Layout / Refresh 確認

GUI部品追加後、以下を確認する。

```text id="9c63d2"
- MainFrame初期化後に Layout が適切に行われる
- RightPaneが表示される
- リサイズ時に崩れない
- Waveform / Preview が消えない
- Status表示が残る
- Theme切替後に表示が更新される
```

必要に応じて以下を使う。

```text id="g63wi0"
Layout()
Refresh()
Update()
SendSizeEvent()
SetMinSize()
```

ただし、`Update()` は乱用しない。

### Step 9: テスト追加

B3用の軽量テストを追加する。

推奨ファイル名。

```text id="em3id0"
tests/test_wx_ms16_b3_right_pane.py
```

または現行テスト命名に合わせる。

確認項目。

```text id="e70drx"
- RightPane を生成できる
- Notebook が存在する
- 必要なタブが存在する
- 各helperで表示を更新できる
- clear helperで初期表示へ戻せる
- MainFrame が right_pane を保持する
```

GUIテストがHeadlessで不安定な場合は、可能な範囲で wx App の初期化を最小化する。
B1/B2で全体pytestハング実績があるため、B3でも対象テストを優先する。

### Step 10: 軽量確認・テスト実行

まず compileall を実行する。

```powershell id="fim2sb"
.\.venv\Scripts\python.exe -m compileall .\src
```

次にB3対象テストを実行する。

```powershell id="cwl7au"
.\.venv\Scripts\python.exe -m pytest tests\test_wx_ms16_b3_right_pane.py
```

必要に応じて既存wx系テストも実行する。

```powershell id="oxacx9"
.\.venv\Scripts\python.exe -m pytest tests\test_wx_ms15_b5_state_theme.py
.\.venv\Scripts\python.exe -m pytest tests\test_wx_ms15_b2_preview.py
```

全体pytestは、ハング対策がある場合のみ実行する。

```powershell id="o4bywm"
.\.venv\Scripts\python.exe -m pytest
```

ハングした場合は、B3の失敗と即断せず、どのテストで停止したかを報告する。

### Step 11: PySide6 / 旧gui参照が戻っていないか確認

B2後の状態を壊していないか確認する。

```powershell id="v8mu74"
Get-ChildItem -Recurse -File |
  Where-Object { $_.Extension -in ".py", ".toml", ".txt", ".ps1", ".spec", ".md" } |
  Select-String -Pattern "from PySide6|import PySide6|QtWidgets|QtCore|QtGui|shiboken6|from gui\.|import gui"
```

確認すること。

```text id="ql374z"
- PySide6 / Qt import が戻っていない
- 旧 src/gui/ 参照が戻っていない
- gui_wx は残ってよい
```

### Step 12: 最終git差分確認

```powershell id="txw32u"
git status
git diff --stat
git diff --name-only
git diff --cached --stat
git diff --cached --name-only
```

確認すること。

```text id="sswcu9"
- B3対象ファイルに収まっている
- 旧GUI / PySide6 が戻っていない
- Preview shape / writer / 音声拡張に変更が入っていない
- MS17対象変更が混入していない
```

---

## 10. 状態遷移 / データ契約

MS16-B3では、pipeline の正本や VMD writer 契約は変更しない。

### 10.1 変更しない契約

```text id="fm3xoj"
- Pipelineの正本は timing plan
- Preview data は timing plan からの派生物
- VMD writer input は timing plan からの派生物
- Waveform表示は現行の音声表示データに従う
- TEXT / 音声 / パラメータ変更時の結果無効化方針
- input identity / job id による古いworker結果破棄
```

### 10.2 B3で追加される表示契約

B3では、右ペインを表示用領域として追加する。

```text id="gdbsfb"
RightPane は表示用であり、pipeline の正本ではない。
RightPane の表示内容を元に timing plan を復元してはならない。
RightPane の表示内容を writer input として扱ってはならない。
```

### 10.3 Info / Warning / 選択イベント表示の扱い

```text id="ozgwi8"
- Info表示は補助表示である
- Warning表示はMS16-B3時点ではplaceholderである
- 選択イベント表示はMS16-B3時点ではplaceholderである
- 選択状態の正本はB3では導入しない
- プリセット / モデルプロファイルはB3時点では保存対象ではない
```

### 10.4 入力変更時の扱い

B3では本格連携を行わない場合でも、既存の入力変更時に古い重要情報が残る設計は避ける。

最低限、RightPaneの初期表示が古い解析結果や古い選択情報に見えないようにする。

---

## 11. テスト方針

### 11.1 優先テスト

B3では以下を優先する。

```text id="m0x36y"
1. compileall
2. RightPane単体生成テスト
3. MainFrame統合テスト
4. Theme適用テスト
5. 既存wx系テスト
```

### 11.2 推奨テスト観点

```text id="b3thzi"
- RightPaneが生成できる
- Notebookに5タブがある
- タブ名が期待通り
- helperが例外なく動作する
- clear helperが例外なく動作する
- MainFrameがright_pane属性を持つ
- Theme切替後に例外が出ない
- WaveformPanel / PreviewPanel が消えていない
- 既存action stateに影響しない
```

### 11.3 全体pytestの扱い

B1/B2で全体pytestがGUI/ダイアログ起因でハングする可能性が確認されている。

そのため、B3では全体pytestを絶対条件にしない。

実行できる場合のみ以下を行う。

```powershell id="sxiiim"
.\.venv\Scripts\python.exe -m pytest
```

ハングした場合は、以下を報告する。

```text id="d65882"
- 停止したテスト
- GUI初期化 / ダイアログ起因か
- B3変更に起因する可能性があるか
- 対象テストは通っているか
```

---

## 12. 受け入れ条件

MS16-B3の受け入れ条件は以下である。

```text id="jxf1n7"
- src/gui_wx/right_pane.py または同等の右ペイン実装が存在する
- MainFrameに右ペインが追加されている
- 右ペインにタブUIがある
- Info タブが存在する
- Warning タブが存在する
- 選択イベント タブが存在する
- プリセット タブが存在する
- モデルプロファイル タブが存在する
- 各タブにplaceholderまたは最小表示がある
- 各タブにset/clear系helperがある
- ThemeManagerまたは既存テーマ機構に追従する
- 既存Waveform / Preview 表示が壊れていない
- 既存Playback / Zoom / Viewportに影響していない
- compileall が通る
- B3対象テストが通る
- PySide6 / Qt / 旧 src/gui 参照が戻っていない
- mp3 / m4a / FFmpeg / MMD用WAV変更が混入していない
```

---

## 13. リスクと対策

### 13.1 リスク: 右ペイン追加で中央表示が狭くなる

対策:

```text id="h6bt8t"
- 右ペインに適切な最小幅を設定する
- 中央Waveform / Preview領域を過度に圧迫しない
- 必要なら splitter または proportion を調整する
```

### 13.2 リスク: 既存InfoPanelとの責務が重複する

対策:

```text id="vbdpxq"
- B3では既存InfoPanelを置き換えない
- 右ペインInfoは将来拡張用の補助表示として扱う
- 本格的な情報再配置は後続Blockまたは別計画で扱う
```

### 13.3 リスク: Warning機能を作り込みすぎる

対策:

```text id="6p86cq"
- B3ではWarning表示枠のみ
- Warning判定本体は実装しない
- fallback / diagnostic 判定は後続マイルストーンへ送る
```

### 13.4 リスク: 選択イベント機能を先取りする

対策:

```text id="gbfic7"
- B3では選択イベントタブのplaceholderのみ
- selected_event_id や hit-test はB6へ送る
- 編集機能は実装しない
```

### 13.5 リスク: Theme追従漏れ

対策:

```text id="1m8toq"
- ThemeManager経由で色を適用する
- Theme切替テストまたは軽量確認を行う
- 新規Panelに背景色・文字色を明示適用する
```

### 13.6 リスク: 旧Qt / PySide6参照が戻る

対策:

```text id="gl1m55"
- 旧 src/gui/ は参照しない
- PySide6 / Qt import 残存検索を実行する
- gui_wx と core のみを使う
```

### 13.7 リスク: B4/B5範囲へ踏み込む

対策:

```text id="l7wqzw"
- Preview shape 表示は変更しない
- control_points 生成契約は変更しない
- writer shape ロジックは変更しない
```

---

## 14. Antigravity 実装時の注意

Antigravity は以下を厳守すること。

```text id="jbldmk"
今回は MS16-B3 の scoped implementation です。

目的は、wxPython主系に右ペイン型GUI基盤を追加することです。

旧 src/gui/ は参照しないでください。
Qt / PySide6 を再導入しないでください。
preview_transform は src/core/preview_transform.py を参照してください。

B3では以下を行わないでください。
- Preview変形台形表示の復元
- Preview shape data contract の修正
- VMD writer shape ロジックの変更
- 母音イベント選択ロジック
- 母音イベント編集
- Warning判定本体
- プリセット保存
- モデルプロファイル保存
- mp3 / m4a 入力対応
- FFmpeg / ffprobe 接続
- 解析用WAV生成
- MMD用WAV同時出力

右ペインには、Info / Warning / 選択イベント / プリセット / モデルプロファイル のタブを用意し、MS16-B3時点ではplaceholderまたは読み取り専用の最小表示に留めてください。
```

---

## 15. Antigravity 作業開始用プロンプト

以下を Antigravity に渡す想定とする。

````text id="c3kzvx"
MS16-B3: GUI Layout Foundation / Right Pane 基盤 を実施してください。

今回は scoped implementation です。
目的は、wxPython主系のMainFrameに右ペイン型GUI基盤を追加することです。

前提:
- MS16-B2は完了済みです。
- Qt / PySide6 は削除済みです。
- 旧 src/gui/ は削除済みです。
- preview_transform は src/core/preview_transform.py に移動済みです。
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
````

MS16-B2の差分が未コミットで残っている場合は、B3実装を開始せず、状況を報告してください。
B2差分とB3差分を混在させないでください。

実施内容:

1. 現行 `src/gui_wx/main_frame.py` のレイアウトを確認する。
2. `src/gui_wx/right_pane.py` などの新規モジュールに `RightPane` を実装する。
3. `RightPane` に `wx.Notebook` または同等のタブUIを追加する。
4. 以下のタブを用意する。

   * Info
   * Warning
   * 選択イベント
   * プリセット
   * モデルプロファイル
5. 各タブには placeholder または読み取り専用の最小表示を置く。
6. 各タブに set / clear 系の view helper を用意する。
7. MainFrame に RightPane を追加する。
8. 既存の Waveform / Preview / Playback / Zoom / Viewport / Status を壊さない。
9. ThemeManager または既存テーマ機構に追従させる。
10. B3用の軽量テストを追加する。
11. compileall と対象テストを実行する。
12. PySide6 / Qt / 旧 src/gui 参照が戻っていないか確認する。

B3では以下を行わないでください。

* Preview変形台形表示の復元
* control_points生成契約の修正
* writer shape ロジックの変更
* 母音イベント選択ロジック
* 母音イベント編集
* Warning判定本体
* プリセット保存
* モデルプロファイル保存
* mp3 / m4a 入力対応
* FFmpeg / ffprobe 接続
* 解析用WAV生成
* MMD用WAV同時出力

確認コマンド例:

```powershell
.\.venv\Scripts\python.exe -m compileall .\src
.\.venv\Scripts\python.exe -m pytest tests\test_wx_ms16_b3_right_pane.py

Get-ChildItem -Recurse -File |
  Where-Object { $_.Extension -in ".py", ".toml", ".txt", ".ps1", ".spec", ".md" } |
  Select-String -Pattern "from PySide6|import PySide6|QtWidgets|QtCore|QtGui|shiboken6|from gui\.|import gui"
```

全体pytestは、過去にGUI/ダイアログ周りでハング実績があります。
B3では全体pytestに固執せず、compileall、B3対象テスト、既存wx系の軽量テストを優先してください。
全体pytestを実行してハングした場合は、強制終了し、ハング箇所と原因候補を報告してください。

完了報告では以下を報告してください。

* 実行したコマンド
* 変更したファイル
* 新規作成したファイル
* RightPane の構成
* 追加したタブ
* 追加した view helper
* MainFrameへの接続方法
* Theme確認結果
* Layout / Refresh / Update 確認結果
* 実行したテスト
* テスト結果
* PySide6 / Qt / 旧 src/gui 参照残存確認結果
* MS17対象変更が混入していないこと
* 最終 git diff --stat

---

## 16. 完了報告形式

Antigravity は作業完了時に以下の形式で報告する。

```text id="s9g2zs"
## MS16-B3 実装報告

### 1. 実行したコマンド

### 2. 作業前git状態
- branch:
- latest commit:
- working tree:

### 3. 新規作成したファイル

### 4. 変更したファイル

### 5. RightPane構成
- class:
- tabs:
- helper:

### 6. MainFrameへの接続
- 接続箇所:
- レイアウト方式:
- 既存Waveform / Previewへの影響:

### 7. 追加したタブ
- Info:
- Warning:
- 選択イベント:
- プリセット:
- モデルプロファイル:

### 8. view helper
- Info:
- Warning:
- 選択イベント:
- プリセット:
- モデルプロファイル:

### 9. Theme / Layout確認
- ThemeManager接続:
- Layout:
- Refresh:
- Update:
- リサイズ確認:

### 10. 既存機能への影響確認
- TEXT読込:
- WAV読込:
- 解析:
- Preview:
- Waveform:
- Playback:
- Zoom / Viewport:
- Status:

### 11. PySide6 / Qt / 旧gui参照確認
- PySide6:
- shiboken6:
- QtWidgets / QtCore / QtGui:
- from gui / import gui:

### 12. テスト結果
- compileall:
- B3対象テスト:
- 既存wx系テスト:
- 全体pytest:

### 13. MS17対象変更の混入確認
- mp3 / m4a:
- FFmpeg / ffprobe:
- 解析用WAV:
- MMD用WAV:

### 14. 最終git状態
- git diff --stat:
- git diff --name-only:

### 15. 残課題
- B4へ送る項目:
- B5へ送る項目:
- B6へ送る項目:
- B7へ送るdocs補正:
````

---

## 17. 完了後の次アクション

MS16-B3完了後、通常は以下へ進む。

```text id="fdipgb"
MS16-B4: Preview 変形台形表示復元
```

ただし、以下の場合はB4へ進む前に補修する。

```text id="9ahiy7"
- MainFrameが起動できない
- RightPane追加によりWaveform / Previewが表示されない
- Theme切替で例外が出る
- PySide6 / Qt / 旧 src/gui 参照が戻っている
- B3対象テストが失敗する
- MS17対象変更が混入している
```

MS16-B3では、右ペインのplaceholderが残っていてよい。
本格的な情報表示、選択イベント連携、Warning判定は後続Blockで扱う。

---

## 18. 変更履歴

### 2026-05-01 / 初版

* MS16-B2完了後の状態を前提として、MS16-B3の実装プランを作成。
* B3を「右ペイン型GUI基盤の追加」に限定。
* Info / Warning / 選択イベント / プリセット / モデルプロファイルの5タブ構成を定義。
* 各タブはplaceholderまたは読み取り専用最小表示に留める方針を定義。
* Preview変形台形表示復元、shape data contract修正、母音イベント選択、音声拡張はOut of Scopeに明記。
* B2差分とB3差分を混在させないため、作業開始時のgit状態確認を必須化。
