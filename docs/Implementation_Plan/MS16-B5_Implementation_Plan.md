# MS16-B5 Implementation Plan

## 1. 文書情報

- 文書名: `MS16-B5 Implementation Plan`
- 推奨ファイル名: `docs/Implementation_Plan/MS16-B5_Implementation_Plan.md`
- 対象プロジェクト: `MMD_AutoLipTool`
- 対象リポジトリ: `https://github.com/kanna3939/MMD_AutoLipTool`
- 対象マイルストーン: `MS16`
- 対象Block: `MS16-B5`
- Block名: `Preview Shape Data Contract 固定`
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

MS16-B2 までで、Qt / PySide6 系依存と旧GUI実装は削除され、`preview_transform.py` は `src/core/preview_transform.py` へ移動された。

MS16-B3 では、wxPython主系に右ペイン型GUI基盤を追加する。

MS16-B4 では、wxPython主系の Preview 表示を、リボン型中心から `control_points` ベースの変形台形 / 三角形 / 簡易エンベロープ表示へ戻す。

MS16-B5では、B4で復元した表示形状を、後続Blockで安全に扱えるように **Preview shape data contract** として整理・固定する。

B5で特に重要な点は以下である。

```text
- Preview data は pipeline の正本ではない
- 正本は timing plan である
- Preview shape は timing plan から派生する表示用データである
- Preview shape から timing plan を復元してはならない
- Preview shape を VMD writer input の正本として扱ってはならない
- ただし、Preview と writer は shape の意味を大きく乖離させてはならない
```

B5は、将来の MS16-B6「母音イベント選択の下地」および MS21以降の軽微編集に備えるための契約整備Blockである。

---

## 3. 目的

MS16-B5の目的は、Preview shape に関するデータ契約を固定し、Preview / writer / 将来の選択イベント表示が同じ意味で形状情報を扱えるようにすることである。

主目的は以下である。

```text
- Preview shape の基本フィールドを明確化する
- shape_kind を導入または整理する
- control_points の意味・形式・値範囲を固定する
- source_event_index または同等のevent参照を整備する
- frame_range を導入または整理する
- value_range を導入または整理する
- morph_name / vowel / start_sec / end_sec / peak_value の意味を明確化する
- zero peak / short span / fallback の扱いをPreview shape上で追跡可能にする
- Preview と VMD writer の shape解釈差を確認・記録する
- 将来の hit-test / selected event 表示に必要な最小metadataを整備する
```

MS16-B5完了後、Preview shape は単なる描画用の一時データではなく、**timing plan から派生した表示・選択準備用データ** として安定した形式を持つ。

---

## 4. In Scope

MS16-B5では以下を対象とする。

```text
- src/core/preview_transform.py の shape data contract 整理
- Preview segment / shape の必須フィールド確認
- shape_kind の導入または整理
- control_points の形式固定
- source_event_index の導入または整理
- source_event_id 相当の要否確認
- frame_range の導入または整理
- value_range の導入または整理
- morph_name / vowel / start_sec / end_sec / peak_value の意味確認
- zero_peak / short_span / fallback_reason の扱い整理
- PreviewPanel が新contractを読めることの確認
- RightPane / 選択イベントタブへ将来渡せる最小summaryの準備
- Preview と writer の shape解釈差分確認
- B5用テスト追加
- 既存Preview関連テストの必要最小限の更新
```

---

## 5. Out of Scope

MS16-B5では以下を行わない。

```text
- 母音イベント選択ロジック本体
- Previewクリック選択
- hit-test本実装
- drag編集
- 母音イベント編集
- 編集値保存
- Undo / Redo
- VMD再生成UI
- RightPaneへの本格的な選択イベント連携
- Warning判定本体
- 出力診断レポート本体
- プリセット保存
- モデルプロファイル保存
- VMD writer shape ロジックの大規模変更
- VMD出力仕様の変更
- VMD出力対象の拡張
- mp3入力対応
- m4a入力対応
- FFmpeg / ffprobe 接続
- 解析用WAV生成
- MMD用WAV同時出力
- MMD互換WAV検証
```

B5は data contract 固定Blockであり、GUI編集・選択操作・音声拡張は扱わない。

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

### 6.2 MS16-B3 / B4との関係

MS16-B5は、原則として MS16-B3 および MS16-B4 完了後に実施する。

```text
- MS16-B3:
  - RightPane基盤がある
  - 選択イベントタブのplaceholderがある

- MS16-B4:
  - Preview表示が control_points ベースの変形台形系表示へ復元されている
  - 通常eventがリボン型fallbackへ落ちにくくなっている
```

B4が未完了の場合、B5を開始しない。

理由:

```text
B5は、B4で復元した control_points 表示を正式な shape data contract として整理するBlockであるため。
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
- B2 / B3 / B4 の差分が未コミットで残っている場合は、B5実装を開始しない
- B5差分はB5対象に限定する
- staged差分とunstaged差分を区別して報告する
```

---

## 7. 対象ファイル

MS16-B5で変更対象となる候補は以下である。

```text
src/core/preview_transform.py
src/gui_wx/preview_panel.py
src/gui_wx/right_pane.py
src/gui_wx/main_frame.py

tests/test_preview_transform.py
tests/test_wx_ms15_b2_preview.py
tests/test_wx_ms16_b4_preview_shape.py
tests/test_wx_ms16_b5_preview_contract.py

docs/Version_Control.md
docs/repo_milestone.md
```

主対象は以下である。

```text
src/core/preview_transform.py
src/gui_wx/preview_panel.py
tests/test_wx_ms16_b5_preview_contract.py
```

`right_pane.py` や `main_frame.py` は、将来の選択イベント表示に必要な最小summary helperを接続する場合のみ変更する。

docs更新は最小限とする。  
MS16-B5単体の実装記録として必要な場合のみ、`docs/Version_Control.md` または `docs/repo_milestone.md` に短い記録を追加する。

---

## 8. 実装方針

### 8.1 基本方針

MS16-B5では、Preview shape のデータ契約を固定する。

基本方針は以下。

```text
- 正本は timing plan とする
- Preview shape は timing plan から派生する
- Preview shape を正本化しない
- Preview shape から timing plan を復元しない
- Preview shape を writer input の正本にしない
- writer と Preview の shape意味が大きく乖離しないよう確認する
- hit-test / 選択表示に必要な最小metadataを整える
```

### 8.2 Preview shape の推奨フィールド

Preview shape には、概念上、以下の情報を持たせる。

```text
morph_name
vowel
start_sec
end_sec
peak_value
shape_kind
control_points
source_event_index
frame_range
value_range
fallback_reason
is_zero_peak
is_short_span
```

実装上のデータ型は現行コードに従う。

既存実装が dataclass / dict / tuple のいずれであっても、B5では意味契約を優先する。  
ただし、将来のメンテナンスを考えると、可能であれば dataclass または型付き構造へ寄せることが望ましい。

### 8.3 必須フィールドと任意フィールド

#### 必須候補

```text
morph_name
start_sec
end_sec
peak_value
control_points
shape_kind
source_event_index
```

#### 推奨候補

```text
vowel
frame_range
value_range
fallback_reason
is_zero_peak
is_short_span
```

#### B5では任意または後続候補

```text
source_event_id
hit_test_bounds
display_bounds
selection_key
warning_summary
observation_summary
```

B5では、hit-test 本実装は行わない。  
ただし、将来 hit-test に必要な `source_event_index` と描画shapeの対応は整備する。

### 8.4 shape_kind 方針

`shape_kind` は、Preview shape の種類を表す。

推奨候補:

```text
trapezoid
triangle
short_fallback
envelope
zero_peak
invalid
```

必要に応じて、既存実装の名前に合わせる。

方針:

```text
- 通常長eventは trapezoid または envelope
- 短区間eventは triangle または short_fallback
- peak_value == 0.0 相当は zero_peak
- 不正eventは invalid または skip
```

`shape_kind` は表示と将来の選択情報表示に使う。  
writerの出力shape種別と完全一致する必要はないが、意味が大きくずれてはならない。

### 8.5 control_points 方針

`control_points` は Preview 表示用の点列である。

推奨形式:

```text
[(time_sec, value), ...]
```

または現行実装の形式に従う。

条件:

```text
- time_sec は秒単位
- value は 0.0〜1.0
- 基本的に start_sec〜end_sec の範囲内
- 描画可能な順序で並ぶ
- 少なくとも三角形は3点以上
- 台形は4点以上
- zero-only shape を通常発声shapeとして扱わない
```

B5では、`control_points` の形式をテストで固定する。

### 8.6 source_event_index 方針

`source_event_index` は、Preview shape がどの timing event に由来するかを示す。

方針:

```text
- timing event list の index を保持する
- Preview shape と timing event の対応を失わない
- source_event_index が不正範囲を指さないようにする
- 入力変更 / timing plan変更時には古いindexを使い回さない
```

B5では、将来の選択イベント表示に備え、`source_event_index` を最小metadataとして扱う。

`source_event_id` の導入は、現行コードに event id 相当が存在する場合のみ検討する。  
存在しない場合は、B5では無理に新規ID体系を導入せず、B6または後続で検討する。

### 8.7 frame_range 方針

`frame_range` は、Preview shape が概念上対応するフレーム範囲である。

推奨形式:

```text
(start_frame, end_frame)
```

基準:

```text
30fps
frame_no = round(time_sec * 30)
```

条件:

```text
- start_frame >= 0
- end_frame >= 0
- start_frame <= end_frame
- start_sec / end_sec と大きく矛盾しない
```

B5では、writerと完全一致する丸め規則まで再設計しない。  
既存writerに一貫した丸め規則がある場合は、それを尊重する。

### 8.8 value_range 方針

`value_range` は、Preview shape の値範囲である。

推奨形式:

```text
(min_value, max_value)
```

条件:

```text
- 0.0 <= min_value <= 1.0
- 0.0 <= max_value <= 1.0
- min_value <= max_value
- max_value は peak_value と整合する
```

通常shapeでは、概ね以下になる。

```text
value_range = (0.0, peak_value)
```

ただし、fallbackやzero_peakの場合は、実装に合わせて安全に扱う。

### 8.9 fallback / warning 方針

B5では、fallbackやwarningの本格判定は行わない。

ただし、Preview shape に以下のような補助情報を持たせることは許容する。

```text
fallback_reason
is_short_span
is_zero_peak
```

目的:

```text
- 後続のWarning表示
- 選択イベント情報表示
- デバッグしやすさ
```

Warning判定本体は、B5では実装しない。

### 8.10 PreviewPanelとの関係

PreviewPanel は、B5で固定された shape data contract を読める必要がある。

確認すること。

```text
- shape_kind があっても描画が壊れない
- control_points を使って polygon描画できる
- source_event_index 等のmetadataが描画処理を邪魔しない
- 古い互換segmentがある場合も安全にfallbackできる
```

PreviewPanel は表示層であり、contractの正本ではない。  
contractの生成は原則として `src/core/preview_transform.py` 側に置く。

### 8.11 writerとの関係

B5では、writerのshapeロジックを大規模変更しない。

ただし、以下は確認する。

```text
- writer側のshape概念とPreview shape_kindが大きく矛盾していないか
- closing hold / closing softness の意味がPreview上で誤解されないか
- short fallback / zero peak の扱いがPreviewとwriterで大きくずれていないか
```

writer変更が必要に見える場合は、B5で無理に直さず、差分を記録し、後続Blockまたは補修対象にする。

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
- MS16-B2 / B3 / B4 の差分が残っていないか
- working tree がクリーンか
- B5以外の変更が混入していないか
```

MS16-B4の差分が未コミットで残っている場合は、B5実装に入らず報告する。

### Step 2: B4後のPreview shape現状確認

確認対象。

```text
src/core/preview_transform.py
src/gui_wx/preview_panel.py
tests/test_wx_ms16_b4_preview_shape.py
tests/test_preview_transform.py
```

確認すること。

```text
- B4で追加された control_points 形式
- 通常eventのshape
- 短区間eventのshape
- zero peakの扱い
- PreviewPanelのpolygon描画経路
- fallback描画が残る条件
```

このStepでは、B4の実装結果を前提として、B5で正式化すべき項目を確認する。

### Step 3: Preview shapeの既存構造を整理

`src/core/preview_transform.py` 内で、Preview segment / shape の構造を確認する。

確認すること。

```text
- dataclass か dict か tuple か
- 既存フィールド名
- 既存テストの期待値
- 後方互換が必要な箇所
```

既存構造を大きく壊さず、B5で必要なcontract項目を追加・整理する。

### Step 4: shape_kind を追加または整理

Preview shape に `shape_kind` 相当を持たせる。

推奨値:

```text
trapezoid
triangle
short_fallback
envelope
zero_peak
invalid
```

既存実装が別名を使っている場合は、既存名に合わせる。  
ただし、意味が曖昧な場合はB5で整理する。

テスト観点:

```text
- 通常eventが期待するshape_kindを持つ
- 短区間eventが短区間用shape_kindを持つ
- zero peakが通常発声shape_kindにならない
```

### Step 5: control_points の形式を固定

B4で生成された `control_points` の形式を確認し、テストで固定する。

条件:

```text
- list または tuple の点列である
- 各点が time_sec と value を持つ
- time_sec は数値
- value は数値
- value は 0.0〜1.0
- 描画可能な順序である
```

既存実装が `(time_sec, value)` ではなく dict形式を使っている場合は、その形式を明記し、テストで固定する。

### Step 6: source_event_index を追加または整理

Preview shape に `source_event_index` を付与する。

方針:

```text
- 元 timing event のindexを保持する
- indexが無い互換データでは None などで安全に扱う
- source_event_index が範囲外にならない
```

テスト観点:

```text
- shape数とevent数の対応が取れる
- source_event_index が正しいeventを指す
- source_event_index が負にならない
```

B5では、event id体系を新設しすぎない。  
必要ならB6へ送る。

### Step 7: frame_range を追加または整理

Preview shape に `frame_range` を付与する。

方針:

```text
- start_sec / end_sec から30fps基準で算出する
- writer側の丸め規則が明確ならそれを尊重する
- 不明な場合は round(time_sec * 30) を基準にする
```

テスト観点:

```text
- frame_range が2要素である
- start_frame <= end_frame
- 負のframeがない
- start_sec / end_sec と概ね対応する
```

### Step 8: value_range を追加または整理

Preview shape に `value_range` を付与する。

方針:

```text
- control_points のvalueから算出してよい
- peak_value と矛盾しない
- 0.0〜1.0に収める
```

テスト観点:

```text
- value_range が2要素である
- min_value <= max_value
- 0.0 <= min_value <= 1.0
- 0.0 <= max_value <= 1.0
```

### Step 9: zero_peak / short_span / fallback_reason を整理

B5では、Preview shape が特殊状態を追跡できるようにする。

候補:

```text
is_zero_peak
is_short_span
fallback_reason
```

方針:

```text
- zero peakを通常発声shapeとして扱わない
- short spanをshape_kindまたはis_short_spanで識別可能にする
- fallback理由がある場合は表示またはテストで確認可能にする
```

Warning判定本体は実装しない。

### Step 10: PreviewPanel が新contractを読めることを確認

`src/gui_wx/preview_panel.py` を確認し、B5で増えたmetadataにより描画が壊れないことを確認する。

必要な場合のみ最小修正する。

確認すること。

```text
- control_pointsを従来通り描画できる
- shape_kindなどのmetadataを無視しても描画できる
- 将来必要ならshape_kindで描画分岐できる
- fallback互換が壊れていない
```

B5では、描画表現の大幅変更は行わない。  
描画表現はB4で扱った内容を維持する。

### Step 11: 右ペイン連携の最小準備を確認

B3で `RightPane` と選択イベントタブが存在する場合、B5では本格連携しない。

ただし、将来B6で使えるように、Preview shape summaryを文字列化できる helper を `preview_transform` またはテスト内で確認してもよい。

B5で許容される範囲:

```text
- shape summary作成関数の最小追加
- テスト用のsummary確認
```

B5で行わないこと:

```text
- 実際の選択イベント表示連携
- クリック選択
- selected_event state導入
```

### Step 12: writerとのshape意味差を確認・記録

以下を確認する。

```text
- writerのshort fallbackとPreviewのshort shapeが大きく矛盾していないか
- writerのtrapezoid相当とPreviewのtrapezoidが大きく矛盾していないか
- closing hold / closing softness のPreview反映に未対応箇所があるか
- zero peak / zero-only shapeの扱いが矛盾していないか
```

B5で修正しないものは、完了報告で残課題として記録する。

### Step 13: B5用テスト追加

推奨テストファイル。

```text
tests/test_wx_ms16_b5_preview_contract.py
```

テスト観点。

```text
- shape_kind が存在する
- control_points の形式が固定されている
- source_event_index が存在する
- frame_range が存在する
- value_range が存在する
- zero_peak が通常shapeとして扱われない
- short span が識別可能
- fallback_reason が必要に応じて保持される
- PreviewPanel が新contractのshapeを受け取れる
```

### Step 14: 既存Previewテスト更新

必要に応じて以下を更新する。

```text
tests/test_preview_transform.py
tests/test_wx_ms15_b2_preview.py
tests/test_wx_ms16_b4_preview_shape.py
```

更新方針。

```text
- B4で追加されたcontrol_points期待値を壊さない
- B5で追加されたcontract項目を確認する
- 旧リボンfallback前提に戻さない
```

### Step 15: 軽量確認・テスト実行

まず compileall を実行する。

```powershell
.\.venv\Scripts\python.exe -m compileall .\src
```

B5対象テストを実行する。

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_wx_ms16_b5_preview_contract.py
```

Preview関連テストを実行する。

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_preview_transform.py tests\test_wx_ms15_b2_preview.py tests\test_wx_ms16_b4_preview_shape.py
```

必要に応じてwx系軽量テストを実行する。

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_wx_ms15_b5_state_theme.py
```

全体pytestは、ハング対策がある場合のみ実行する。

```powershell
.\.venv\Scripts\python.exe -m pytest
```

ハングした場合は、B5の失敗と即断せず、停止箇所と原因候補を報告する。

### Step 16: PySide6 / 旧gui参照が戻っていないか確認

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

### Step 17: 最終git差分確認

```powershell
git status
git diff --stat
git diff --name-only
git diff --cached --stat
git diff --cached --name-only
```

確認すること。

```text
- B5対象ファイルに収まっている
- Preview contract / Preview tests 以外に不要変更がない
- writer shape ロジックを大規模変更していない
- 音声拡張に変更が入っていない
- PySide6 / Qt / 旧gui参照が戻っていない
```

---

## 10. 状態遷移 / データ契約

MS16-B5では、Preview shape data contract を固定する。  
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

### 10.2 B5で固定するPreview shape contract

B5で固定する概念は以下である。

```text
PreviewShape:
  morph_name
  vowel
  start_sec
  end_sec
  peak_value
  shape_kind
  control_points
  source_event_index
  frame_range
  value_range
  fallback_reason
  is_zero_peak
  is_short_span
```

実装上の型名は現行コードに合わせてよい。  
重要なのは、各フィールドの意味と不変条件である。

### 10.3 control_points契約

```text
control_points:
  - 表示用点列
  - 各点は time_sec と value を持つ
  - time_sec は秒単位
  - value は 0.0〜1.0
  - timing plan から派生する
  - writer input の正本ではない
```

### 10.4 source_event_index契約

```text
source_event_index:
  - 元timing eventへの参照
  - 将来の選択イベント表示のための最小metadata
  - 入力変更やtiming plan無効化後に使い回してはならない
```

### 10.5 frame_range契約

```text
frame_range:
  - Preview shape が概念上対応する30fpsフレーム範囲
  - start_sec / end_sec から派生
  - writerと大きく矛盾しないこと
```

### 10.6 value_range契約

```text
value_range:
  - Preview shape の値範囲
  - 基本的には control_points から算出
  - 0.0〜1.0 に収まる
```

### 10.7 古い結果の扱い

B5でも、以下は禁止する。

```text
- 入力変更後に古いPreview shapeを残す
- パラメータ変更後に古いPreview shapeを保存可能結果として見せる
- 古いworker結果から返ったPreview dataを現在UIへ反映する
- 古いsource_event_indexを現在のtiming planに対応しているものとして扱う
```

---

## 11. テスト方針

### 11.1 優先テスト

B5では以下を優先する。

```text
1. compileall
2. Preview contract単体テスト
3. Preview transformテスト
4. PreviewPanel受け取りテスト
5. B4 Preview shapeテスト
6. 既存wx系軽量テスト
```

### 11.2 推奨テスト観点

```text
- shape_kind が存在する
- control_points が期待形式である
- source_event_index が存在する
- frame_range が存在する
- value_range が存在する
- value_range が control_points と整合する
- peak_value が value_range と矛盾しない
- short span が識別できる
- zero peak が通常shapeとして扱われない
- fallback_reason が必要に応じて追跡できる
```

### 11.3 ピクセル一致テストについて

B5ではピクセル完全一致のスクリーンショットテストは行わない。

理由:

```text
- wxPythonの描画は環境差が出やすい
- CI / headless環境で安定しにくい
- B5の目的はdata contract固定であり、見た目のピクセル一致ではない
```

### 11.4 全体pytestの扱い

B1以降、全体pytestがGUI/ダイアログ起因でハングする可能性がある。

そのため、B5では全体pytestを絶対条件にしない。

実行できる場合のみ以下を行う。

```powershell
.\.venv\Scripts\python.exe -m pytest
```

ハングした場合は、以下を報告する。

```text
- 停止したテスト
- GUI初期化 / ダイアログ起因か
- B5変更に起因する可能性があるか
- B5対象テストは通っているか
```

---

## 12. 受け入れ条件

MS16-B5の受け入れ条件は以下である。

```text
- Preview shape に shape_kind がある
- Preview shape に control_points がある
- control_points の形式がテストで確認されている
- Preview shape に source_event_index または同等のevent参照がある
- Preview shape に frame_range がある
- Preview shape に value_range がある
- value_range が 0.0〜1.0 に収まる
- peak_value と value_range が大きく矛盾しない
- zero peak が通常発声shapeとして扱われない
- short span が識別可能である
- fallback_reason が必要に応じて追跡できる
- PreviewPanel が新contractのshapeを受け取れる
- B4で復元した変形台形表示を壊していない
- writer shape ロジックを大規模変更していない
- compileall が通る
- B5対象テストが通る
- Preview関連テストが通る
- PySide6 / Qt / 旧 src/gui 参照が戻っていない
- mp3 / m4a / FFmpeg / MMD用WAV変更が混入していない
```

---

## 13. リスクと対策

### 13.1 リスク: Preview shape を正本扱いしてしまう

対策:

```text
- 正本は timing plan と明記する
- Preview shape は派生物とする
- Preview shape から timing plan を復元しない
```

### 13.2 リスク: B5で編集機能まで実装してしまう

対策:

```text
- B5はdata contract固定に限定する
- hit-test本体やクリック選択はB6以降
- 編集機能はMS21以降
```

### 13.3 リスク: metadataを増やしすぎる

対策:

```text
- B5では将来選択に必要な最小metadataに限定する
- source_event_idやhit_test_boundsは必要性が明確な場合のみ
- 過剰なGUI状態は導入しない
```

### 13.4 リスク: writerとの整合を取ろうとしてwriterを大きく変更する

対策:

```text
- B5ではwriter変更を原則避ける
- 不一致は記録し、必要なら後続Blockで扱う
- writer出力仕様を勝手に変えない
```

### 13.5 リスク: B4で復元した表示を壊す

対策:

```text
- B4対象テストを継続実行する
- control_points の形式変更は最小限にする
- PreviewPanelとの互換を確認する
```

### 13.6 リスク: 旧Qt / PySide6参照が戻る

対策:

```text
- 旧 src/gui/ は参照しない
- PySide6 / Qt import 残存検索を実行する
- src/core/preview_transform.py を使う
```

### 13.7 リスク: source_event_index が古いtiming planに対応してしまう

対策:

```text
- source_event_index は現在のtiming plan由来として扱う
- 入力変更 / plan無効化時のPreview clearを壊さない
- 古いworker結果をUIへ反映しない既存契約を維持する
```

---

## 14. Antigravity 実装時の注意

Antigravity は以下を厳守すること。

```text
今回は MS16-B5 の scoped implementation です。

目的は、Preview shape data contract を固定することです。

正本は timing plan です。
Preview shape は timing plan から派生する表示・選択準備用データです。
Preview shape から timing plan を復元しないでください。
Preview shape を writer input の正本にしないでください。

旧 src/gui/ は参照しないでください。
Qt / PySide6 を再導入しないでください。
preview_transform は src/core/preview_transform.py を使用してください。

B5では以下を行わないでください。
- 母音イベント選択ロジック
- Previewクリック選択
- hit-test本実装
- 母音イベント編集
- VMD writer shape ロジックの大規模変更
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
MS16-B5: Preview Shape Data Contract 固定 を実施してください。

今回は scoped implementation です。
目的は、B4で復元した Preview 変形台形表示を、将来の選択イベント表示・hit-test準備・writer整合確認に耐える shape data contract として固定することです。

前提:
- MS16-B2は完了済みです。
- Qt / PySide6 は削除済みです。
- 旧 src/gui/ は削除済みです。
- preview_transform は src/core/preview_transform.py に移動済みです。
- MS16-B3が完了済みであることを確認してください。
- MS16-B4が完了済みであることを確認してください。
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

MS16-B2 / B3 / B4 の差分が未コミットで残っている場合は、B5実装を開始せず、状況を報告してください。
B2/B3/B4差分とB5差分を混在させないでください。

実施内容:
1. `src/core/preview_transform.py` のPreview shape構造を確認する。
2. B4で追加された `control_points` の形式を確認する。
3. Preview shape に `shape_kind` を導入または整理する。
4. `control_points` の形式をテストで固定する。
5. Preview shape に `source_event_index` または同等のevent参照を追加・整理する。
6. Preview shape に `frame_range` を追加・整理する。
7. Preview shape に `value_range` を追加・整理する。
8. `zero_peak`, `short_span`, `fallback_reason` 相当の扱いを整理する。
9. `src/gui_wx/preview_panel.py` が新contractのshapeを受け取れることを確認する。
10. writer shapeロジックは大規模変更しない。
11. B5用の軽量テストを追加する。
12. compileall とPreview関連テストを実行する。
13. PySide6 / Qt / 旧 src/gui 参照が戻っていないか確認する。

B5では以下を行わないでください。
- 母音イベント選択ロジック
- Previewクリック選択
- hit-test本実装
- 母音イベント編集
- VMD writer shape ロジックの大規模変更
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
.\.venv\Scripts\python.exe -m pytest tests\test_wx_ms16_b5_preview_contract.py
.\.venv\Scripts\python.exe -m pytest tests\test_preview_transform.py tests\test_wx_ms15_b2_preview.py tests\test_wx_ms16_b4_preview_shape.py

Get-ChildItem -Recurse -File |
  Where-Object { $_.Extension -in ".py", ".toml", ".txt", ".ps1", ".spec", ".md" } |
  Select-String -Pattern "from PySide6|import PySide6|QtWidgets|QtCore|QtGui|shiboken6|from gui\.|import gui"
```

全体pytestは、過去にGUI/ダイアログ周りでハング実績があります。
B5では全体pytestに固執せず、compileall、B5対象テスト、Preview関連テスト、既存wx系の軽量テストを優先してください。
全体pytestを実行してハングした場合は、強制終了し、ハング箇所と原因候補を報告してください。

完了報告では以下を報告してください。

- 実行したコマンド
- 変更したファイル
- 新規作成したテスト
- Preview shape contract の内容
- shape_kind の定義
- control_points の形式
- source_event_index の扱い
- frame_range の扱い
- value_range の扱い
- zero_peak / short_span / fallback_reason の扱い
- PreviewPanel 側の対応内容
- writer shapeロジックを大規模変更していないこと
- 実行したテスト
- テスト結果
- PySide6 / Qt / 旧 src/gui 参照残存確認結果
- MS17対象変更が混入していないこと
- 最終 git diff --stat

---

## 16. 完了報告形式

Antigravity は作業完了時に以下の形式で報告する。

## MS16-B5 実装報告

### 1. 実行したコマンド

### 2. 作業前git状態
- branch:
- latest commit:
- working tree:

### 3. 変更したファイル

### 4. 新規作成したファイル

### 5. Preview shape contract
- 型または構造:
- 必須フィールド:
- 任意フィールド:
- 不変条件:

### 6. shape_kind
- 定義:
- 通常event:
- 短区間event:
- zero peak:
- invalid:

### 7. control_points
- 形式:
- 値範囲:
- 時刻範囲:
- テスト内容:

### 8. source_event_index
- 追加有無:
- 意味:
- 範囲チェック:
- B6への引き継ぎ:

### 9. frame_range
- 追加有無:
- 算出方法:
- 30fps基準:
- writerとの関係:

### 10. value_range
- 追加有無:
- 算出方法:
- peak_valueとの関係:

### 11. zero_peak / short_span / fallback_reason
- zero_peak:
- short_span:
- fallback_reason:

### 12. PreviewPanel対応
- 新contract受け取り:
- polygon描画:
- fallback描画:
- 互換性:

### 13. writer変更の有無
- writer変更:
- 変更した場合の理由:
- 変更していない場合の確認:
- 残る差分:

### 14. PySide6 / Qt / 旧gui参照確認
- PySide6:
- shiboken6:
- QtWidgets / QtCore / QtGui:
- from gui / import gui:

### 15. テスト結果
- compileall:
- B5対象テスト:
- Preview関連テスト:
- 既存wx系テスト:
- 全体pytest:

### 16. MS17対象変更の混入確認
- mp3 / m4a:
- FFmpeg / ffprobe:
- 解析用WAV:
- MMD用WAV:

### 17. 最終git状態
- git diff --stat:
- git diff --name-only:

### 18. 残課題
- B6へ送る項目:
- B7へ送るdocs補正:
- 後続で検討すべきwriter差分:

---

## 17. 完了後の次アクション

MS16-B5完了後、通常は以下へ進む。

```text
MS16-B6: 母音イベント選択の下地
```

B6では、B5で固定した shape data contract を使い、以下を扱う。

```text
- Preview shape と timing event の対応
- selected_event_id / selected_shape_id 相当の内部保持
- 選択中イベント情報の読み取り専用表示
- RightPaneの選択イベントタブへの最小連携
```

ただし、以下の場合はB6へ進む前に補修する。

```text
- Preview shape contract がテストで確認できない
- source_event_index が不正になる
- PreviewPanelが新contractを受け取れない
- B4で復元した変形台形表示が壊れている
- writer shapeロジックが意図せず変更されている
- PySide6 / Qt / 旧 src/gui 参照が戻っている
- MS17対象変更が混入している
```

---

## 18. 変更履歴

### 2026-05-01 / 初版

- MS16-B1〜B4までの流れを踏まえ、MS16-B5の実装プランを作成。
- B5を「Preview Shape Data Contract 固定」に限定。
- `shape_kind`, `control_points`, `source_event_index`, `frame_range`, `value_range`, `zero_peak`, `short_span`, `fallback_reason` を主な契約項目として定義。
- Preview shape は timing plan から派生する表示・選択準備用データであり、pipeline正本ではないことを明記。
- 母音イベント選択、hit-test本実装、編集機能、writer大規模変更、音声拡張はOut of Scopeに明記。
- B6へ進むための前提として、Preview shape と timing event の対応を整備する方針を定義。
