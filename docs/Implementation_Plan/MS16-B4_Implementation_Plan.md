# MS16-B4 Implementation Plan

## 1. 文書情報

- 文書名: `MS16-B4 Implementation Plan`
- 推奨ファイル名: `docs/Implementation_Plan/MS16-B4_Implementation_Plan.md`
- 対象プロジェクト: `MMD_AutoLipTool`
- 対象リポジトリ: `https://github.com/kanna3939/MMD_AutoLipTool`
- 対象マイルストーン: `MS16`
- 対象Block: `MS16-B4`
- Block名: `Preview 変形台形表示復元`
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

MS16-B2 までで、Qt / PySide6 系依存と旧GUI実装は削除され、Preview data 変換処理は旧 `src/gui/preview_transform.py` から `src/core/preview_transform.py` へ移動された。

MS16-B3 では、wxPython主系に右ペイン型GUI基盤を追加する計画である。

MS16-B4では、MS16-B1で確認された Preview 表示上の課題を扱う。

MS16-B1 の調査では、以下が確認されている。

```text
- wx版 PreviewPanel には control_points がある場合にポリゴン描画する処理が既に存在する。
- control_points が無い segment では DrawRoundedRectangle によるリボン型表示へフォールバックしている。
- 現在の preview_transform は、writer 側の形状概念を Preview 用 control_points に十分翻訳できていない。
- 結果として、wx版 Preview はリボン型表示になりやすい。
```

MS16-B4では、Preview表示を VMD writer の意味に近い **変形台形 / 三角形 / 簡易エンベロープ表示** へ戻す。

ただし、MS16-B4は **表示復元Block** であり、Preview shape data contract の正式固定は MS16-B5 で扱う。

---

## 3. 目的

MS16-B4の目的は、wxPython主系の Preview 表示を、単純なリボン型表示から、VMD出力の形状意味に近い変形台形系表示へ戻すことである。

主目的は以下である。

```text id="yphgd6"
- Preview segment に control_points を生成・付与する
- PreviewPanel で control_points を使ったポリゴン描画を安定させる
- 通常長の母音イベントを変形台形として表示する
- 短い母音イベントを三角形または短区間fallbackとして表示する
- peak_value に応じた高さをPreviewへ反映する
- closing hold / closing softness 相当の表示を可能な範囲で反映する
- Waveform / Preview / playback cursor / Viewport / Zoom の同期を維持する
- Theme追従を維持する
```

MS16-B4完了後、ユーザーが Preview 上で、リップモーションの開閉形状を視覚的に確認しやすい状態にする。

---

## 4. In Scope

MS16-B4では以下を対象とする。

```text id="jhlgnc"
- src/core/preview_transform.py の Preview data 生成処理確認
- Preview segment への control_points 生成
- 通常イベントの変形台形表示
- 短区間イベントの三角形または短区間fallback表示
- peak_value の高さ反映
- start_sec / end_sec に基づく横位置反映
- closing_hold / closing_softness が既にpreview transform入力にある場合の表示反映
- PreviewPanel の polygon描画経路の確認・最小補修
- control_points がある場合にリボン型fallbackへ落ちないことの確認
- Viewport / Zoom 範囲内での描画維持
- playback cursor 表示維持
- ThemeManager / ThemePalette との整合維持
- B4用テスト追加
- 既存Preview関連テストの必要最小限の更新
```

---

## 5. Out of Scope

MS16-B4では以下を行わない。

```text id="oyfthw"
- Preview shape data contract の正式固定
- source_event_index / event_id / hit-test metadata の正式整備
- 母音イベント選択ロジック
- Previewクリック選択
- 母音イベント編集
- drag編集
- Undo / Redo
- VMD writer shape ロジックの大規模変更
- VMD出力仕様の変更
- VMD出力対象の拡張
- ボーン / カメラ / 照明 / IK / 表示制御のVMD出力
- 右ペイン機能の拡張
- Warning判定本体
- プリセット保存
- モデルプロファイル保存
- mp3入力対応
- m4a入力対応
- FFmpeg / ffprobe 接続
- 解析用WAV生成
- MMD用WAV同時出力
- MMD互換WAV検証
```

特に、MS16-B4では Preview 表示の復元に集中する。

以下は後続Blockへ送る。

```text id="y2qkks"
MS16-B5:
- Preview shape data contract の正式固定
- source_event_index
- frame_range
- value_range
- shape_kind の契約整理
- hit-test 用metadataの下地整理

MS16-B6:
- 母音イベント選択の下地
- 選択イベント情報表示
```

---

## 6. 前提条件

### 6.1 作業前提

```text id="ozk7c6"
- 作業branchは feature/MS16
- MS16-B2が完了済みである
- Qt / PySide6 は削除済みである
- 旧 src/gui/ は削除済みである
- preview_transform.py は src/core/preview_transform.py に移動済みである
- 現行GUI主系は src/gui_wx/ である
```

### 6.2 MS16-B3との関係

MS16-B4は、原則として MS16-B3 完了後に実施する。

```text id="mm19pk"
- MS16-B3が完了済みの場合:
  - B4実装へ進んでよい。

- MS16-B3が未実装または未コミットの場合:
  - B4実装を開始せず、B3の状態を報告する。
  - B3差分とB4差分を混在させない。
```

B4自体は右ペインに強依存しないが、MS16の順序管理上、B3後に行う。

### 6.3 Git状態に関する前提

作業開始時に以下を確認する。

```powershell id="as5r7l"
git status
git branch
git log --oneline -n 10
git diff --stat
git diff --name-only
git diff --cached --stat
git diff --cached --name-only
```

判定:

```text id="u9v0nl"
- B2またはB3の差分が未コミットで残っている場合は、B4実装を開始しない。
- B4差分はB4対象に限定する。
- staged差分とunstaged差分を区別して報告する。
```

---

## 7. 対象ファイル

MS16-B4で変更対象となる候補は以下である。

```text id="butu0f"
src/core/preview_transform.py
src/gui_wx/preview_panel.py
src/gui_wx/main_frame.py
src/gui_wx/placeholder_panels.py
src/gui_wx/theme.py

tests/test_preview_transform.py
tests/test_wx_ms15_b2_preview.py
tests/test_wx_ms16_b4_preview_shape.py

docs/Version_Control.md
docs/repo_milestone.md
```

主対象は以下である。

```text id="vpwya2"
src/core/preview_transform.py
src/gui_wx/preview_panel.py
tests/test_wx_ms16_b4_preview_shape.py
```

`main_frame.py` や `placeholder_panels.py` は、Preview data の受け渡しに必要な場合のみ変更する。

docs更新は最小限とする。  
MS16-B4単体の実装記録として必要な場合のみ、`docs/Version_Control.md` または `docs/repo_milestone.md` に短い記録を追加する。

---

## 8. 実装方針

### 8.1 基本方針

MS16-B4では、Preview表示をリボン型中心から変形台形系へ戻す。

基本方針は以下。

```text id="u9z5iw"
- 正本は timing plan とする
- Preview data は timing plan からの派生物とする
- Preview data から timing plan を復元しない
- VMD writer 出力から timing plan を復元しない
- VMD writer の shape ロジックは原則変更しない
- Preview表示を writer の意味に近づける
- B4では正式なshape contract固定までは行わない
```

### 8.2 control_points 生成方針

B4では、Preview segment に `control_points` を生成する。

推奨する概念は以下。

```text id="hab3m5"
control_points:
- PreviewPanel が描画可能な、時間軸と値の点列
- 時刻は event の start / end を基準にする
- 値は 0.0〜peak_value を基準にする
- 表示時には PreviewPanel が panel座標へ変換する
```

既存実装で `control_points` の形式が既に定義されている場合は、それに従う。  
形式を勝手に大きく変えない。

B4で許容される形状:

```text id="oop9tn"
- triangle
- trapezoid
- asymmetric trapezoid
- simple envelope
```

B4では、以下の正式契約化は行わない。

```text id="hsaw7b"
- shape_kind の完全仕様化
- frame_range の正式追加
- source_event_index の正式追加
- hit-test metadata の正式追加
```

必要な最小フィールドが既に存在する場合は利用してよい。  
新規追加が必要な場合は、B5で正式化する前提で最小限に留める。

### 8.3 通常イベントの表示方針

通常長の母音イベントは、変形台形として表示する。

概念例:

```text id="e2xnhp"
start_zero
  ↓
rise
  ↓
top_start
  ↓
top_end
  ↓
fall
  ↓
end_zero
```

表示上の目的:

```text id="rf0k22"
- 発声開始で口が開く
- peak_value 付近で上辺を持つ
- 発声終了で閉じる
- リボン型の単純矩形表示を避ける
```

### 8.4 短区間イベントの表示方針

短すぎるイベントは、無理に台形にせず、三角形または短区間fallback表示にする。

方針:

```text id="k03s7a"
- zero-only shape を作らない
- peak_value が 0.0 の場合は通常発声shapeとして描画しない
- 短区間でも発声の存在が視認できるようにする
- writer の short fallback と意味が大きく乖離しないようにする
```

### 8.5 peak_value の扱い

`peak_value` はPreview表示の高さに反映する。

方針:

```text id="5u5kc4"
- 0.0 <= peak_value <= 1.0 を前提にする
- 範囲外の場合は安全に clamp する
- peak_value == 0.0 相当は通常shapeとして強調しない
- morph upper limit がPreview dataに反映済みなら、その結果を尊重する
```

B4では、peak_value の算出ロジックは変更しない。

### 8.6 closing hold / closing softness の扱い

B4では、既存Preview transform に closing hold / closing softness 相当の情報が渡っている場合に限り、表示へ反映する。

反映例:

```text id="nq8mxa"
- top_end を少し後ろへ伸ばす
- fall部分をなだらかにする
```

ただし、writer の closing hold / closing softness ロジックを変更してはならない。

情報がPreview側に渡っていない場合は、B4で大きなpipeline変更を行わず、以下のように扱う。

```text id="1gk96r"
- B4では start/end/peak_value に基づく変形台形表示まで行う
- closing hold / softness の完全反映はB5以降の契約整理候補として記録する
```

### 8.7 PreviewPanel描画方針

既に `control_points` によるポリゴン描画が存在する場合、それを活かす。

確認すること。

```text id="f1v5xu"
- control_points がある場合に polygon 描画される
- polygon が panel範囲外へ大きくはみ出さない
- Viewport外のshapeは適切にclampまたはskipされる
- control_points が無い場合のみ fallback 表示になる
- fallback表示が残っても、通常イベントでは多用されない
```

B4では、`DrawRoundedRectangle` のfallbackを完全削除しなくてもよい。  
ただし、通常の有効eventで fallback へ落ちる状態は解消する。

### 8.8 Theme方針

PreviewPanel の既存テーマ追従を維持する。

確認対象:

```text id="vo5nqg"
- 背景
- lane背景
- lane境界線
- 母音ラベル
- shape描画色
- cursor色
- grid色
- 無効表示色
```

新規色追加は原則不要。  
既存の preview shape 色を利用する。

### 8.9 Performance方針

B4では、描画負荷を増やしすぎない。

方針:

```text id="kdc4di"
- Viewport外shapeの描画を避ける
- 必要以上に点数を増やさない
- control_points は最小限の点列にする
- Paint処理内で重い計算を繰り返さない
```

---

## 9. 詳細ステップ

### Step 1: 作業前git状態確認

```powershell id="p6ab79"
git status
git branch
git log --oneline -n 10
git diff --stat
git diff --name-only
git diff --cached --stat
git diff --cached --name-only
```

確認すること。

```text id="murx05"
- MS16-B2 / B3 の差分が残っていないか
- working tree がクリーンか
- B4以外の変更が混入していないか
```

MS16-B2またはB3の差分が未コミットで残っている場合は、B4実装に入らず報告する。

### Step 2: 現行Preview構造確認

確認対象。

```text id="pqa6fz"
src/core/preview_transform.py
src/gui_wx/preview_panel.py
tests/test_preview_transform.py
tests/test_wx_ms15_b2_preview.py
```

確認すること。

```text id="zpj5zs"
- Preview segment のデータ構造
- control_points の有無
- control_points の形式
- PreviewPanel の polygon描画処理
- fallback の DrawRoundedRectangle 経路
- peak_value の扱い
- start_sec / end_sec の扱い
- Viewport / cursor / theme との接続
```

このStepでは、まず現状把握を行う。

### Step 3: Preview segment の control_points 生成箇所を特定

`src/core/preview_transform.py` 内で、Preview data を生成している関数を特定する。

確認すること。

```text id="m2gnbj"
- build_preview_data 相当の関数
- timing plan から segment を作る箇所
- start / end / value を持つデータ構造
- control_points を付与できる箇所
```

既に `control_points` フィールドがある場合:

```text id="hbn0v8"
- 未設定になっている原因を確認する
- 通常eventで設定されるようにする
```

`control_points` フィールドがない場合:

```text id="cwu7yq"
- B4で最小限のフィールド追加を検討する
- B5で正式契約化する前提をコメントまたはテスト名で明確にする
```

### Step 4: 変形台形用 control_points を生成

通常イベントに対して、変形台形の点列を生成する。

概念例。

```text id="b8o3qh"
[
  (start_sec, 0.0),
  (rise_end_sec, peak_value),
  (top_end_sec, peak_value),
  (end_sec, 0.0),
]
```

必要に応じて、以下を使う。

```text id="z8zq7g"
- event.start_sec
- event.end_sec
- event.duration_sec
- event.peak_value
- closing_hold_frames
- closing_softness_frames
```

ただし、使える情報がない場合は、start/end/peak_value だけで構成する。

### Step 5: 短区間fallback用 control_points を生成

短区間イベントに対して、三角形または簡易fallback点列を生成する。

概念例。

```text id="zv6233"
[
  (start_sec, 0.0),
  (center_sec, peak_value),
  (end_sec, 0.0),
]
```

短区間判定は、既存実装またはwriter側の概念を参考にする。  
ただし、writerロジックをB4で大きく変更しない。

### Step 6: zero peak / invalid event の扱いを確認

以下を確認する。

```text id="b80g1u"
- peak_value == 0.0 のeventを通常shapeとして描画していないか
- start_sec > end_sec の不正eventを描画していないか
- 負の時刻を描画していないか
- 値が 0.0〜1.0 を超えていないか
```

B4では、不正eventのpipeline修正までは行わない。  
Preview transform 内で安全にskipまたはclampする。

### Step 7: PreviewPanel polygon描画の補修

`src/gui_wx/preview_panel.py` を確認し、必要な最小補修を行う。

確認・補修対象。

```text id="mdavg0"
- control_points がある場合に polygon描画される
- x座標がViewportに対応する
- y座標がlane内に収まる
- peak_value が高さとして視認できる
- polygonが反転しない
- Theme色が使われる
- Refreshが呼ばれる
```

B4では、描画処理の大規模再設計は避ける。

### Step 8: fallback表示の扱いを整理

`DrawRoundedRectangle` のfallback表示は、以下の場合に限定する。

```text id="jyq5ud"
- 古いデータまたは互換データで control_points が無い場合
- placeholder 的なsegment
- テスト用の最小segment
```

通常の有効eventでは、原則として control_points が生成され、polygon描画されるようにする。

### Step 9: B4用テスト追加

推奨テストファイル。

```text id="uf1b3z"
tests/test_wx_ms16_b4_preview_shape.py
```

テスト観点。

```text id="vftx0l"
- 通常eventから control_points が生成される
- control_points が3点以上ある
- control_points の時刻が start_sec〜end_sec の範囲に収まる
- control_points の値が 0.0〜1.0 に収まる
- peak_value が control_points に反映される
- 短区間eventが三角形またはfallback点列になる
- peak_value == 0.0 のeventが通常shapeにならない
- PreviewPanel が control_points ありのsegmentを受け取れる
```

GUI描画そのものをピクセル単位で比較しない。  
B4では、データ構造と描画経路の確認を優先する。

### Step 10: 既存Previewテスト更新

必要に応じて以下を更新する。

```text id="c11oay"
tests/test_preview_transform.py
tests/test_wx_ms15_b2_preview.py
```

更新方針。

```text id="jswq8d"
- 旧リボン型fallback前提のテストがあれば更新する
- control_points が生成されることを期待値に加える
- 既存のPreview生成APIを壊さない
```

### Step 11: 軽量確認・テスト実行

まず compileall を実行する。

```powershell id="pvu06j"
.\.venv\Scripts\python.exe -m compileall .\src
```

次にB4対象テストを実行する。

```powershell id="ys6kxt"
.\.venv\Scripts\python.exe -m pytest tests\test_wx_ms16_b4_preview_shape.py
```

既存Preview関連テストを実行する。

```powershell id="vg6pzh"
.\.venv\Scripts\python.exe -m pytest tests\test_preview_transform.py tests\test_wx_ms15_b2_preview.py
```

必要に応じてwx系軽量テストも実行する。

```powershell id="twezu2"
.\.venv\Scripts\python.exe -m pytest tests\test_wx_ms15_b5_state_theme.py
```

全体pytestは、ハング対策がある場合のみ実行する。

```powershell id="gw8zvs"
.\.venv\Scripts\python.exe -m pytest
```

ハングした場合は、B4の失敗と即断せず、停止箇所と原因候補を報告する。

### Step 12: PySide6 / 旧gui参照が戻っていないか確認

B2後の状態を壊していないか確認する。

```powershell id="dv0k7i"
Get-ChildItem -Recurse -File |
  Where-Object { $_.Extension -in ".py", ".toml", ".txt", ".ps1", ".spec", ".md" } |
  Select-String -Pattern "from PySide6|import PySide6|QtWidgets|QtCore|QtGui|shiboken6|from gui\.|import gui"
```

確認すること。

```text id="a4sd2f"
- PySide6 / Qt import が戻っていない
- 旧 src/gui/ 参照が戻っていない
- gui_wx は残ってよい
- src/core/preview_transform.py を参照している
```

### Step 13: 最終git差分確認

```powershell id="gsnh4w"
git status
git diff --stat
git diff --name-only
git diff --cached --stat
git diff --cached --name-only
```

確認すること。

```text id="ukfyts"
- B4対象ファイルに収まっている
- Preview transform / PreviewPanel / tests 以外に不要変更がない
- writer shape ロジックを変更していない
- 音声拡張に変更が入っていない
- PySide6 / Qt / 旧gui参照が戻っていない
```

---

## 10. 状態遷移 / データ契約

MS16-B4では、pipeline の正本や writer 契約は変更しない。

### 10.1 変更しない契約

```text id="qwc3vy"
- Pipelineの正本は timing plan
- Preview data は timing plan からの派生物
- VMD writer input は timing plan からの派生物
- VMD keyframe はwriterの出力結果であり、pipeline正本ではない
- observation は補助情報であり、timeline event の代替正本ではない
- input identity / job id による古いworker結果破棄を維持する
```

### 10.2 B4で扱うPreview表示契約

B4では、Preview data に表示用の形状情報を追加または補完する。

```text id="vra2xm"
- control_points はPreview表示用の派生情報である
- control_points から timing plan を復元してはならない
- control_points を writer input の正本として扱ってはならない
- control_points は表示のために使う
```

### 10.3 B5へ送る契約

B4で暫定的に扱った以下は、B5で正式整理する。

```text id="shshf4"
- shape_kind
- control_points の正式形式
- source_event_index
- source_event_id
- frame_range
- value_range
- hit-test用metadata
- Previewとwriterのshape解釈差
```

### 10.4 古い結果の扱い

B4でも、以下は禁止する。

```text id="rh60w1"
- 入力変更後に古いPreview shapeを残す
- パラメータ変更後に古いPreview shapeを保存可能結果として見せる
- 古いworker結果から返ったPreview dataを現在UIへ反映する
```

既存の clear / invalidate 処理を壊さない。

---

## 11. テスト方針

### 11.1 優先テスト

B4では以下を優先する。

```text id="iq7j76"
1. compileall
2. preview_transform の control_points 生成テスト
3. PreviewPanel の control_points 受け取りテスト
4. 既存Preview関連テスト
5. 既存Theme / Viewport 関連の軽量テスト
```

### 11.2 推奨テスト観点

```text id="pjgj3x"
- 通常eventがcontrol_pointsを持つ
- 短区間eventがcontrol_pointsを持つ
- control_pointsの時刻が単調増加または描画可能な順序である
- control_pointsの値が0.0〜1.0に収まる
- peak_valueが高さに反映される
- control_pointsがある場合にPreviewPanelがリボンfallbackへ落ちない
- clear時に古い表示が残らない
- Theme切替後に例外が出ない
- Viewport変更後に例外が出ない
```

### 11.3 ピクセル一致テストについて

B4ではピクセル完全一致のスクリーンショットテストは行わない。

理由:

```text id="r4x1qd"
- wxPythonの描画は環境差が出やすい
- CI / headless環境で安定しにくい
- B4の目的は描画データと描画経路の復元である
```

代わりに、control_points と描画API経路の構造テストを優先する。

### 11.4 全体pytestの扱い

B1/B2で全体pytestがGUI/ダイアログ起因でハングする可能性が確認されている。

そのため、B4では全体pytestを絶対条件にしない。

実行できる場合のみ以下を行う。

```powershell id="jtqj0b"
.\.venv\Scripts\python.exe -m pytest
```

ハングした場合は、以下を報告する。

```text id="eok0n8"
- 停止したテスト
- GUI初期化 / ダイアログ起因か
- B4変更に起因する可能性があるか
- B4対象テストは通っているか
```

---

## 12. 受け入れ条件

MS16-B4の受け入れ条件は以下である。

```text id="f7dvbq"
- 通常のPreview segment に control_points が生成される
- control_points があるsegmentは polygon描画経路で扱われる
- 有効eventがリボン型fallbackへ落ちにくくなっている
- 通常長eventが変形台形相当として表示できる
- 短区間eventが三角形または短区間fallback相当として表示できる
- peak_value がPreviewの高さに反映される
- control_points の値が 0.0〜1.0 に収まる
- Viewport / Zoom / playback cursor が壊れていない
- Theme追従が維持されている
- Preview clear / invalidate が壊れていない
- compileall が通る
- B4対象テストが通る
- 既存Preview関連テストが通る
- VMD writer shape ロジックを大規模変更していない
- PySide6 / Qt / 旧 src/gui 参照が戻っていない
- mp3 / m4a / FFmpeg / MMD用WAV変更が混入していない
```

---

## 13. リスクと対策

### 13.1 リスク: Preview data を正本扱いしてしまう

対策:

```text id="vy0fa5"
- 正本は timing plan と明記する
- control_points は表示用派生情報として扱う
- writer input へ逆流させない
```

### 13.2 リスク: writer shape ロジックまで変更してしまう

対策:

```text id="xsjcv4"
- B4では writer を原則変更しない
- writer変更が必要に見える場合は、B5以降の契約整理候補として報告する
- B4では Preview transform 側の表示復元を優先する
```

### 13.3 リスク: B5のdata contract固定まで踏み込む

対策:

```text id="ev7nia"
- B4では control_points 生成と描画復元に限定する
- shape_kind / source_event_index / frame_range 等の正式契約はB5へ送る
- 新規フィールド追加が必要な場合は最小限に留める
```

### 13.4 リスク: Preview表示が環境差でテスト不安定になる

対策:

```text id="ui4jsb"
- ピクセル一致テストは避ける
- control_points の構造テストを中心にする
- PreviewPanel生成と描画データ受け取りを軽量確認する
```

### 13.5 リスク: Viewport / Zoom / cursor同期が壊れる

対策:

```text id="s24qbv"
- PreviewPanel の既存Viewport変換を維持する
- x座標変換を既存処理に合わせる
- B4対象テストにViewport条件を含める
```

### 13.6 リスク: Theme追従漏れ

対策:

```text id="s544aa"
- 既存ThemePaletteを使う
- 新規色を増やさない
- Theme切替後のPreview再描画を確認する
```

### 13.7 リスク: zero peak を通常shapeとして表示する

対策:

```text id="j04co5"
- peak_value == 0.0 相当は通常発声shapeとして強調しない
- zero-only shape を作らない
- 必要ならskipまたは無効表示にする
```

### 13.8 リスク: 旧Qt / PySide6参照が戻る

対策:

```text id="pakuxa"
- 旧 src/gui/ は参照しない
- PySide6 / Qt import 残存検索を実行する
- src/core/preview_transform.py を使う
```

---

## 14. Antigravity 実装時の注意

Antigravity は以下を厳守すること。

```text id="r6k8z3"
今回は MS16-B4 の scoped implementation です。

目的は、wxPython主系の Preview 表示を、リボン型中心から変形台形 / 三角形 / 簡易エンベロープ表示へ戻すことです。

旧 src/gui/ は参照しないでください。
Qt / PySide6 を再導入しないでください。
preview_transform は src/core/preview_transform.py を使用してください。

B4では以下を行わないでください。
- Preview shape data contract の正式固定
- source_event_index / hit-test metadata の正式追加
- 母音イベント選択ロジック
- 母音イベント編集
- VMD writer shape ロジックの大規模変更
- 右ペイン機能の拡張
- Warning判定本体
- プリセット保存
- モデルプロファイル保存
- mp3 / m4a 入力対応
- FFmpeg / ffprobe 接続
- 解析用WAV生成
- MMD用WAV同時出力

control_points はPreview表示用の派生情報として扱ってください。
正本は timing plan です。
```

---

## 15. Antigravity 作業開始用プロンプト

以下を Antigravity に渡す想定とする。

```text id="p7eirz"
MS16-B4: Preview 変形台形表示復元 を実施してください。

今回は scoped implementation です。
目的は、wxPython主系のPreview表示を、リボン型中心から、変形台形 / 三角形 / 簡易エンベロープ表示へ戻すことです。

前提:
- MS16-B2は完了済みです。
- Qt / PySide6 は削除済みです。
- 旧 src/gui/ は削除済みです。
- preview_transform は src/core/preview_transform.py に移動済みです。
- MS16-B3が完了済みであることを確認してください。
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

MS16-B2またはB3の差分が未コミットで残っている場合は、B4実装を開始せず、状況を報告してください。
B2/B3差分とB4差分を混在させないでください。

実施内容:
1. `src/core/preview_transform.py` のPreview data生成処理を確認する。
2. `src/gui_wx/preview_panel.py` のpolygon描画処理とfallback描画処理を確認する。
3. 通常の有効eventに `control_points` が生成されるようにする。
4. 通常長eventは変形台形相当の点列にする。
5. 短区間eventは三角形または短区間fallback相当の点列にする。
6. `peak_value` を高さへ反映する。
7. `control_points` の値を 0.0〜1.0 の範囲に収める。
8. `control_points` があるsegmentは polygon描画経路に乗るよう確認する。
9. DrawRoundedRectangle のリボン型fallbackは、control_points が無い互換ケース等に限定する。
10. Viewport / Zoom / playback cursor / Theme追従を壊さない。
11. B4用の軽量テストを追加する。
12. compileall とPreview関連テストを実行する。
13. PySide6 / Qt / 旧 src/gui 参照が戻っていないか確認する。

B4では以下を行わないでください。
- Preview shape data contract の正式固定
- source_event_index / hit-test metadata の正式追加
- 母音イベント選択ロジック
- 母音イベント編集
- VMD writer shape ロジックの大規模変更
- 右ペイン機能の拡張
- Warning判定本体
- mp3 / m4a 入力対応
- FFmpeg / ffprobe 接続
- 解析用WAV生成
- MMD用WAV同時出力

確認コマンド例:

```powershell
.\.venv\Scripts\python.exe -m compileall .\src
.\.venv\Scripts\python.exe -m pytest tests\test_wx_ms16_b4_preview_shape.py
.\.venv\Scripts\python.exe -m pytest tests\test_preview_transform.py tests\test_wx_ms15_b2_preview.py

Get-ChildItem -Recurse -File |
  Where-Object { $_.Extension -in ".py", ".toml", ".txt", ".ps1", ".spec", ".md" } |
  Select-String -Pattern "from PySide6|import PySide6|QtWidgets|QtCore|QtGui|shiboken6|from gui\.|import gui"
```

全体pytestは、過去にGUI/ダイアログ周りでハング実績があります。
B4では全体pytestに固執せず、compileall、B4対象テスト、Preview関連テスト、既存wx系の軽量テストを優先してください。
全体pytestを実行してハングした場合は、強制終了し、ハング箇所と原因候補を報告してください。

完了報告では以下を報告してください。

- 実行したコマンド
- 変更したファイル
- 新規作成したテスト
- control_points の生成方針
- 通常長eventの表示方針
- 短区間eventの表示方針
- peak_value反映の方法
- PreviewPanel polygon描画経路の確認結果
- fallback表示が残る条件
- Viewport / Zoom / cursor / Theme確認結果
- 実行したテスト
- テスト結果
- PySide6 / Qt / 旧 src/gui 参照残存確認結果
- writer shapeロジックを大規模変更していないこと
- MS17対象変更が混入していないこと
- 最終 git diff --stat

---

## 16. 完了報告形式

Antigravity は作業完了時に以下の形式で報告する。

```text id="yw5l2p"
## MS16-B4 実装報告

### 1. 実行したコマンド

### 2. 作業前git状態
- branch:
- latest commit:
- working tree:

### 3. 変更したファイル

### 4. 新規作成したファイル

### 5. control_points 生成方針
- 通常event:
- 短区間event:
- zero peak:
- invalid event:

### 6. PreviewPanel描画経路
- polygon描画:
- fallback描画:
- DrawRoundedRectangle が残る条件:

### 7. peak_value反映
- 高さ反映:
- clamp:
- morph upper limitとの関係:

### 8. Viewport / Zoom / cursor 確認
- Viewport:
- Zoom:
- playback cursor:
- auto-follow影響:

### 9. Theme確認
- ThemeManager:
- Light:
- Dark:
- System:

### 10. 既存機能への影響確認
- TEXT読込:
- WAV読込:
- 解析:
- Preview:
- Waveform:
- Playback:
- VMD保存:
- Status:

### 11. PySide6 / Qt / 旧gui参照確認
- PySide6:
- shiboken6:
- QtWidgets / QtCore / QtGui:
- from gui / import gui:

### 12. テスト結果
- compileall:
- B4対象テスト:
- Preview関連テスト:
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
- B5へ送る項目:
- B6へ送る項目:
- B7へ送るdocs補正:
```

---

## 17. 完了後の次アクション

MS16-B4完了後、通常は以下へ進む。

```text id="rhy3cj"
MS16-B5: Preview Shape Data Contract 固定
```

B5では、B4で復元した表示形状をもとに、以下を正式整理する。

```text id="p3f4ep"
- shape_kind
- control_points
- source_event_index
- frame_range
- value_range
- hit-test用metadata
- Preview と writer の shape 解釈差
```

ただし、以下の場合はB5へ進む前に補修する。

```text id="hmgag0"
- PreviewPanelがcontrol_pointsを描画できない
- 有効eventが依然としてリボン型fallbackへ落ちる
- Viewport / Zoom / cursor が壊れている
- Theme切替で例外が出る
- Preview関連テストが失敗する
- PySide6 / Qt / 旧 src/gui 参照が戻っている
- MS17対象変更が混入している
```

---

## 18. 変更履歴

### 2026-05-01 / 初版

- MS16-B1〜B3までの流れを踏まえ、MS16-B4の実装プランを作成。
- B4を「Preview変形台形表示復元」に限定。
- `src/core/preview_transform.py` での `control_points` 生成と、`src/gui_wx/preview_panel.py` でのpolygon描画確認を主対象に定義。
- 通常eventは変形台形、短区間eventは三角形または短区間fallbackとして表示する方針を定義。
- Preview shape data contract の正式固定、母音イベント選択、VMD writer大規模変更、音声拡張はOut of Scopeに明記。
- 全体pytestのハング実績を踏まえ、B4対象テストとPreview関連軽量テストを優先する方針を定義。
