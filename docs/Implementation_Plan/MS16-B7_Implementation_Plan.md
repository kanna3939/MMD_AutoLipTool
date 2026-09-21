# MS16-B7 Implementation Plan

## 1. 文書情報

- 文書名: `MS16-B7 Implementation Plan`
- 推奨ファイル名: `docs/Implementation_Plan/MS16-B7_Implementation_Plan.md`
- 対象プロジェクト: `MMD_AutoLipTool`
- 対象リポジトリ: `https://github.com/kanna3939/MMD_AutoLipTool`
- 対象マイルストーン: `MS16`
- 対象Block: `MS16-B7`
- Block名: `統合確認 / Docs補正 / MS16 Closeout`
- 主対象GUI: `wxPython`
- 旧GUI系: `Qt / PySide6` は再導入しない
- 主対象読者: `Google Antigravity / Gemini 3.1 Pro`
- 主開発環境: `Windows 11`
- Shell: `Windows PowerShell`
- Python: repo の現在要件に従う
- 仮想環境: `.venv`
- 作成日: 2026-05-11
- 文書種別: Implementation Plan
- 実装区分: `closeout / documentation sync / integration verification`

---

## 2. 背景

MS16は、MS15 closeout 後の wxPython 主系をさらに安定化し、将来拡張の土台を整えるためのマイルストーンである。

MS16-B1〜B6では、以下の作業を段階的に行う。

```text
MS16-B1: Repo / Dependency / Preview Shape Contract 現状調査
MS16-B2: Qt / PySide6 Removal
MS16-B3: GUI Layout Foundation / Right Pane 基盤
MS16-B4: Preview 変形台形表示復元
MS16-B5: Preview Shape Data Contract 固定
MS16-B6: 母音イベント選択の下地
```

MS16-B7では、これらを統合確認し、MS16をcloseoutする。

B7の中心目的は、追加実装ではなく、以下を確認・整理することである。

```text
- MS16-B1〜B6の成果が仕様と一致しているか
- Qt / PySide6 が再混入していないか
- wxPython主系が維持されているか
- Preview / Waveform / Playback / Viewport / Theme / RightPane が破綻していないか
- Preview shape data contract と選択イベント下地が成立しているか
- docs上のMS16/MS17境界が明確になっているか
- MS17送りの音声拡張を実装済み扱いしていないか
```

また、前セッションからの未解決メモとして、以下が残っている。

```text
.agent/skills/build-packaging-verification/SKILL.md
```

このSkillは、リモート上で文字化けが確認され、ローカルでは修正済みとされている。  
単体コミットはしない方針だったため、B7では、MS16 closeout の docs / skills 整備コミットに含めるか確認する。

---

## 3. 目的

MS16-B7の目的は、MS16全体を完了状態として安全に閉じることである。

主目的は以下である。

```text
- MS16-B1〜B6の実装・調査結果を統合確認する
- Qt / PySide6 排除状態を確認する
- wxPython主系が壊れていないことを確認する
- RightPane基盤が成立していることを確認する
- Preview変形台形表示が成立していることを確認する
- Preview shape data contract が成立していることを確認する
- 母音イベント選択の下地が成立していることを確認する
- 既存のTEXT読込 / WAV読込 / 解析 / Preview / Waveform / 再生 / VMD保存導線が壊れていないことを確認する
- docs / README / milestone / changelog をMS16完了状態へ同期する
- 音声拡張とm4a対応がMS17対象であることを明確にする
- MS16で実装していない機能を実装済み扱いしない
```

MS16-B7完了後、次のマイルストーンである MS17 に安全に進める状態を作る。

---

## 4. In Scope

MS16-B7では以下を対象とする。

```text
- MS16-B1〜B6の変更内容確認
- git履歴と差分確認
- Qt / PySide6 / shiboken6 / QtWidgets / QtCore / QtGui 残存確認
- 旧 src/gui/ 参照の残存確認
- preview_transform が src/core/preview_transform.py にあることの確認
- wxPython主系の起動・import確認
- RightPane / Info / Warning / 選択イベント / プリセット / モデルプロファイル タブ確認
- Preview変形台形表示の確認
- Preview shape data contract の確認
- 母音イベント選択下地の確認
- Preview clear / invalidate / stale worker discard による古い表示・古い選択状態の破棄確認
- Theme追従確認
- compileall
- B3〜B6対象テストの再実行
- Preview関連テストの再実行
- wx系軽量テストの再実行
- 実行可能な範囲での手動GUI確認
- README.md のMS16完了状態への同期
- docs/Version_Control.md の更新
- docs/repo_milestone.md の更新
- docs/MS16_and_Beyond_Milestone_Map_for_Antigravity.md の必要最小限の同期
- docs/MMD_Audio_WAV_Compatibility_Specification.md のMS16/MS17表記確認・補正
- docs/MS16_Block_Breakdown_for_Antigravity.md の必要最小限の同期
- .agent/skills/build-packaging-verification/SKILL.md の文字化け修正差分確認
- MS17送り項目の明記
```

---

## 5. Out of Scope

MS16-B7では以下を行わない。

```text
- 新機能実装
- mp3入力対応
- m4a入力対応
- FFmpeg / ffprobe 接続
- 解析用WAV生成
- MMD用WAV同時出力
- MMD互換WAV検証
- 音声変換系エラー処理本体
- 母音イベント編集
- Preview drag編集
- Undo / Redo
- VMD再生成UI
- Warning判定本体
- 出力診断レポート本体
- プリセット保存
- モデルプロファイル保存
- PyInstaller配布ビルドの本格closeout
- MS17実装開始
```

B7は closeout Block であり、機能を増やすBlockではない。

不具合が見つかった場合は、以下のいずれかとして扱う。

```text
- B7内で直すべき軽微なdocs補正
- MS16補修実装として別途扱うべき問題
- MS17以降へ送るべき課題
```

---

## 6. 前提条件

### 6.1 作業前提

```text
- 作業branchは feature/MS16
- MS16-B1〜B6が完了済みである
- MS16-B1〜B6の差分がコミット済み、またはB7作業と明確に分離されている
- Qt / PySide6 は削除済みである
- 旧 src/gui/ は削除済みである
- preview_transform.py は src/core/preview_transform.py に移動済みである
- RightPane基盤が存在する
- Preview変形台形表示が存在する
- Preview shape data contract が存在する
- 母音イベント選択の下地が存在する
```

### 6.2 Git状態に関する前提

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
- B1〜B6の未コミット差分が残っている場合は、B7作業を開始しない
- B7差分はdocs / closeout / 必要最小限の補正に限定する
- staged差分とunstaged差分を区別して報告する
```

### 6.3 MS17送りの確定事項

ユーザー判断により、以下はMS17へ送る。

```text
- 音声拡張
- m4a対応
- mp3対応
- FFmpeg / ffprobe
- 解析用WAV生成
- MMD用WAV同時出力
- MMD互換WAV検証
```

B7では、これらをMS16実装済みとして記録してはならない。

---

## 7. 対象ファイル

MS16-B7で確認・変更対象となる候補は以下である。

```text
README.md

docs/MS16_Block_Breakdown_for_Antigravity.md
docs/MS16_and_Beyond_Milestone_Map_for_Antigravity.md
docs/Specification_Prompt_v4.md
docs/GUI_State_Theme_Specification.md
docs/Pipeline_Data_Contract_Specification.md
docs/VMD_Output_Specification.md
docs/MMD_Audio_WAV_Compatibility_Specification.md
docs/Error_Handling_Specification.md
docs/Security_Safety_Specification.md
docs/Release_Package_Manifest.md
docs/Version_Control.md
docs/repo_milestone.md

docs/Implementation_Plan/MS16-B1_Implementation_Plan.md
docs/Implementation_Plan/MS16-B2_Implementation_Plan.md
docs/Implementation_Plan/MS16-B3_Implementation_Plan.md
docs/Implementation_Plan/MS16-B4_Implementation_Plan.md
docs/Implementation_Plan/MS16-B5_Implementation_Plan.md
docs/Implementation_Plan/MS16-B6_Implementation_Plan.md
docs/Implementation_Plan/MS16-B7_Implementation_Plan.md

src/core/preview_transform.py
src/gui_wx/
src/vmd_writer/

tests/

.agent/skills/build-packaging-verification/SKILL.md
```

主な変更対象は以下である。

```text
README.md
docs/Version_Control.md
docs/repo_milestone.md
docs/MS16_and_Beyond_Milestone_Map_for_Antigravity.md
docs/MMD_Audio_WAV_Compatibility_Specification.md
docs/MS16_Block_Breakdown_for_Antigravity.md
.agent/skills/build-packaging-verification/SKILL.md
```

コードファイルは原則として確認のみとする。  
B7でコード修正が必要になった場合は、closeout内の軽微修正として妥当か、補修Blockへ分けるべきかを判断する。

---

## 8. 実装方針

### 8.1 基本方針

MS16-B7では、MS16全体を統合確認し、docsを実装済み状態へ同期する。

基本方針は以下。

```text
- 実装済み / 未実装 / MS17送り / 将来課題を分ける
- MS16で実装していない機能を完了扱いしない
- READMEはエンドユーザー向けに簡潔にする
- docsは開発者 / Antigravity向けに詳細を記録する
- 旧Qt / PySide6の現行依存がないことを明記する
- 音声拡張とm4a対応はMS17対象として明記する
```

### 8.2 MS16完了として記録する項目

B7でMS16完了として記録する候補は以下。

```text
- Qt / PySide6 依存削除
- 旧 src/gui/ 削除
- preview_transform.py の src/core/ 移動
- wxPython主系維持
- RightPane基盤追加
- Info / Warning / 選択イベント / プリセット / モデルプロファイル タブ追加
- Preview変形台形表示復元
- Preview shape data contract 固定
- 母音イベント選択の下地
- 読み取り専用の選択イベントsummary表示
```

実際には、B1〜B6の実装結果と照合して、実装済みのものだけを記録する。

### 8.3 MS17送りとして記録する項目

B7でMS17送りとして明記する項目は以下。

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

### 8.4 docs/MMD_Audio_WAV_Compatibility_Specification.md の扱い

この仕様書は、音声拡張・MMD用WAV互換仕様の正本として重要である。

ただし、ユーザー判断により、音声拡張とm4a対応はMS17へ送ることが確定している。

そのため、B7では以下を確認・補正する。

```text
- 「MS16初期対応」と書かれている箇所がないか
- `.wav / .mp3 / .m4a` がMS16実装済みと誤読される記述がないか
- MMD用WAV同時出力がMS16実装済みと誤読される記述がないか
- 主対象マイルストーンを MS17 以降、または MS17 初期対応へ補正すべきか
```

補正方針:

```text
- 仕様内容自体は原則残す
- 実装時期だけMS17以降として明確化する
- MS16では未実装であることを明記する
```

### 8.5 .agent skill文字化け修正の扱い

前セッションから以下の未解決メモがある。

```text
.agent/skills/build-packaging-verification/SKILL.md
```

B7では、以下を確認する。

```text
- 現在のファイルに文字化けが残っているか
- ローカル修正差分が存在するか
- MS16 closeoutのdocs/skills整備として含めるべきか
```

方針:

```text
- B7でdocs/skills整備コミットに含めることは許容する
- ただし、内容変更が大きい場合は別途報告する
- build-packaging-verification の機能自体はB7で拡張しない
```

### 8.6 README更新方針

READMEはエンドユーザー向けである。

B7でREADMEを更新する場合は、以下を守る。

```text
- MS16で実装済みの範囲だけを書く
- 音声拡張 / m4a / mp3 / MMD用WAVを実装済み扱いしない
- wxPython主系であることを明確にする
- Qt / PySide6 を現行要件として書かない
- 詳細な内部Block履歴を書きすぎない
```

### 8.7 repo_milestone / Version_Control 更新方針

`docs/repo_milestone.md` にはMS16 closeoutの履歴を記録する。

記録すべき内容。

```text
- MS16-B1〜B6の完了
- 主要変更点
- テスト結果
- 手動確認結果
- MS17への引き継ぎ
- 残課題
```

`docs/Version_Control.md` には変更ログとして、ユーザーや開発者が追える粒度で記録する。

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
- B1〜B6の差分が未コミットで残っていないか
- working tree がクリーンか
- B7以外の変更が混入していないか
```

未コミット差分がある場合は、B7作業に入らず報告する。

### Step 2: MS16-B1〜B6の実装結果確認

git logと対象ファイルから、B1〜B6の実装結果を確認する。

確認対象。

```text
- B1調査結果
- B2 Qt / PySide6 Removal
- B3 RightPane基盤
- B4 Preview変形台形表示
- B5 Preview shape data contract
- B6 母音イベント選択下地
```

確認すること。

```text
- 各Blockが実装済みか
- 各Blockの対象範囲を逸脱していないか
- B7に持ち越すべき問題があるか
```

### Step 3: Qt / PySide6 / 旧gui 残存確認

以下を実行する。

```powershell
Get-ChildItem -Recurse -File |
  Where-Object { $_.Extension -in ".py", ".toml", ".txt", ".ps1", ".spec", ".md" } |
  Select-String -Pattern "from PySide6|import PySide6|QtWidgets|QtCore|QtGui|shiboken6|from gui\.|import gui"
```

確認すること。

```text
- 実行コードにPySide6 / Qt importが残っていない
- testsにPySide6 / Qt importが残っていない
- build/specにQt収集が残っていない
- 旧 src/gui/ 参照が戻っていない
```

docs内の履歴記述は、現行依存と誤読されない範囲なら許容する。  
ただし、現行要件として見える記述は補正対象とする。

### Step 4: 依存定義確認

以下を確認する。

```powershell
Select-String -Path .\requirements.txt, .\pyproject.toml -Pattern "PySide6|shiboken6|Qt|gui"
```

確認すること。

```text
- PySide6 / shiboken6 が依存に戻っていない
- packages.find.include に旧 gui が戻っていない
- gui_wx / core / vmd_writer は維持されている
```

`gui_wx` の文字列は正常である。

### Step 5: Preview / RightPane / Selectionの構造確認

以下のファイルを確認する。

```text
src/core/preview_transform.py
src/gui_wx/preview_panel.py
src/gui_wx/right_pane.py
src/gui_wx/main_frame.py
src/gui_wx/ui_state.py
```

確認すること。

```text
- control_points が存在する
- shape_kind が存在する
- source_event_index が存在する
- frame_range / value_range が存在する
- RightPaneが存在する
- 選択イベントタブが存在する
- selected event summary 表示が可能である
- Preview clear / update時に選択状態がクリアされる
```

### Step 6: compileall実行

```powershell
.\.venv\Scripts\python.exe -m compileall .\src
```

失敗した場合は、B7でcloseoutできない。  
エラー内容を報告し、補修が必要か判断する。

### Step 7: Block対象テスト実行

B3〜B6対象テストを実行する。

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_wx_ms16_b3_right_pane.py
.\.venv\Scripts\python.exe -m pytest tests\test_wx_ms16_b4_preview_shape.py
.\.venv\Scripts\python.exe -m pytest tests\test_wx_ms16_b5_preview_contract.py
.\.venv\Scripts\python.exe -m pytest tests\test_wx_ms16_b6_event_selection_foundation.py
```

存在しないテストファイルがある場合は、現行repoのテスト名に合わせて実行する。  
存在しない場合は、どのテストで代替したかを報告する。

### Step 8: Preview / wx系関連テスト実行

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_preview_transform.py tests\test_wx_ms15_b2_preview.py
.\.venv\Scripts\python.exe -m pytest tests\test_wx_ms15_b5_state_theme.py
```

必要に応じて、以下の既存wx系テストも実行する。

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_wx_ms15_b1_waveform.py
.\.venv\Scripts\python.exe -m pytest tests\test_wx_ms15_b3_playback.py
.\.venv\Scripts\python.exe -m pytest tests\test_wx_ms15_b4_viewport.py
```

実際のファイル名は現行repoに従う。

### Step 9: 全体pytestの扱い

過去にGUI/ダイアログ周りで全体pytestがハングした実績がある。

B7では、全体pytestを実行できる状態なら実行する。

```powershell
.\.venv\Scripts\python.exe -m pytest
```

ただし、ハングが再発する場合は、強制終了し、以下を報告する。

```text
- 停止したテスト
- GUI初期化 / ダイアログ起因か
- B7対象テストは通っているか
- 全体pytestをcloseout必須条件から外してよいか
```

B7では、対象テストが十分に通っており、ハング原因が既存のGUIテスト環境問題である場合、全体pytest未完了でもcloseout候補にできる。  
ただし、その判断理由をdocsに記録する。

### Step 10: 手動GUI確認

可能であれば、アプリを手動起動し、以下を確認する。

```text
- アプリ起動
- TEXT読込
- WAV読込
- 解析
- Waveform表示
- Preview表示
- Preview変形台形表示
- RightPane表示
- 選択イベント表示の初期状態
- 再生
- Stop
- Zoom In
- Zoom Out
- Reset Zoom
- Theme切替
- VMD保存
- 入力再読込時のPreview clear
- 入力再読込時の選択状態clear
- 解析失敗時の古い表示残りなし
```

手動確認ができない場合は、理由を報告する。

### Step 11: README.md 更新

READMEをMS16完了状態に同期する。

更新方針。

```text
- wxPython主系であることを明記
- Qt / PySide6 を現行要件として残さない
- MS16で実装済みの内容を必要最小限で記載
- 音声拡張 / mp3 / m4a / MMD用WAVはMS17予定または未実装として扱う
```

READMEはエンドユーザー向けであるため、内部Block名を過剰に並べない。

### Step 12: docs/Version_Control.md 更新

MS16 closeoutの変更ログを追加する。

記録候補。

```text
- Qt / PySide6依存削除
- 旧GUI削除
- Preview transform の core 移動
- RightPane基盤追加
- Preview変形台形表示復元
- Preview shape data contract固定
- 母音イベント選択下地
- テスト結果
- MS17送り項目
```

### Step 13: docs/repo_milestone.md 更新

MS16 closeoutのマイルストーン記録を追加する。

記録候補。

```text
## 2026-05-xx / MS16 Closeout メモ

- 対象: MS16-B1〜B7
- 実装反映:
  - ...
- 確認状態:
  - ...
- 次のステップ:
  - MS17: wav / mp3 / m4a 入力対応、FFmpeg / ffprobe、解析用WAV、MMD用WAV同時出力
```

日付は実際の作業日に合わせる。

### Step 14: docs/MS16_and_Beyond_Milestone_Map_for_Antigravity.md 更新

MS16が完了済みになった場合、マップを更新する。

確認すること。

```text
- MS16が未着手のままになっていないか
- MS16が実装済み範囲と一致しているか
- MS17が音声拡張として整理されているか
- MS18以降の順序に矛盾がないか
```

必要最小限の更新に留める。

### Step 15: docs/MMD_Audio_WAV_Compatibility_Specification.md 更新

MS17送り方針に合わせて、マイルストーン表記を補正する。

補正候補。

```text
- 主対象マイルストーン: MS17 以降
- `.wav / .mp3 / .m4a` 入力はMS17初期対応
- 解析用WAV生成はMS17対象
- MMD用WAV同時出力はMS17対象
- MS16では未実装
```

注意:

```text
仕様内容は削除しない。
実装時期と未実装状態を明確にする。
```

### Step 16: docs/MS16_Block_Breakdown_for_Antigravity.md 更新

B7実施後、Block Breakdown文書を必要に応じて更新する。

確認すること。

```text
- B1〜B7が完了済み状態と矛盾しないか
- MS17送り項目が明確か
- B7 closeoutの結果が反映されているか
```

### Step 17: .agent skill文字化け修正確認

以下を確認する。

```powershell
git status -- .\.agent\skills\build-packaging-verification\SKILL.md
```

必要に応じて内容を開く。

```powershell
Get-Content .\.agent\skills\build-packaging-verification\SKILL.md -Encoding UTF8
```

確認すること。

```text
- 文字化けが残っていないか
- ローカル修正差分があるか
- B7 closeoutのdocs/skills整備に含めてよいか
```

含める場合は、完了報告で明記する。

### Step 18: 最終整合確認

docs更新後、以下を確認する。

```powershell
Get-ChildItem -Recurse -File .\docs |
  Where-Object { $_.Extension -eq ".md" } |
  Select-String -Pattern "MS16初期対応|m4a|mp3|FFmpeg|MMD用WAV"
```

確認すること。

```text
- MS16実装済みと誤読される音声拡張記述がないか
- MS17対象として整理されているか
- 古いQt / PySide6現行依存記述がないか
```

### Step 19: 最終git差分確認

```powershell
git status
git diff --stat
git diff --name-only
git diff --cached --stat
git diff --cached --name-only
```

確認すること。

```text
- B7対象ファイルに収まっている
- 新機能実装が混入していない
- 音声拡張実装が混入していない
- 旧Qt / PySide6参照が戻っていない
- docs更新が実装状態と一致している
```

---

## 10. 状態遷移 / データ契約

MS16-B7では、pipeline の状態遷移やデータ契約は原則変更しない。

### 10.1 変更しない契約

```text
- Pipelineの正本は timing plan
- Preview data は timing plan からの派生物
- VMD writer input は timing plan からの派生物
- VMD keyframe はwriterの出力結果であり、pipeline正本ではない
- observation は補助情報であり、timeline event の代替正本ではない
- input identity / job id による古いworker結果破棄を維持する
```

### 10.2 B7で確認する契約

B7では以下が維持されているか確認する。

```text
- Preview clear時に古いshapeが残らない
- timing plan無効化時にPreviewと選択状態が無効化される
- input reload時に古いPreview / 選択イベント表示が残らない
- stale worker result がUIへ反映されない
- RightPane表示は補助表示であり正本ではない
```

### 10.3 MS17に引き継ぐ契約

MS17では音声入力拡張により、以下の契約追加が必要になる。

```text
- 解析用WAVを音声解析・波形表示の正本にする
- input identity に音声変換元 / 解析用WAV / 変換条件を含める
- mp3 / m4a 変換後に古いPreview / timing plan / 選択状態を無効化する
- MMD用WAV出力はVMD出力とは別系統として扱う
```

B7では実装せず、MS17への引き継ぎとして記録する。

---

## 11. テスト方針

### 11.1 優先テスト

B7では以下を優先する。

```text
1. compileall
2. B3 RightPaneテスト
3. B4 Preview shapeテスト
4. B5 Preview contractテスト
5. B6 Event selection foundationテスト
6. Preview関連既存テスト
7. wx系軽量テスト
8. 実行可能な範囲での手動GUI確認
```

### 11.2 推奨コマンド

```powershell
.\.venv\Scripts\python.exe -m compileall .\src

.\.venv\Scripts\python.exe -m pytest tests\test_wx_ms16_b3_right_pane.py
.\.venv\Scripts\python.exe -m pytest tests\test_wx_ms16_b4_preview_shape.py
.\.venv\Scripts\python.exe -m pytest tests\test_wx_ms16_b5_preview_contract.py
.\.venv\Scripts\python.exe -m pytest tests\test_wx_ms16_b6_event_selection_foundation.py

.\.venv\Scripts\python.exe -m pytest tests\test_preview_transform.py tests\test_wx_ms15_b2_preview.py
```

存在しないファイルがある場合は、現行repoに存在する近いテストを実行し、代替内容を報告する。

### 11.3 全体pytestの扱い

過去に全体pytestがGUI/ダイアログ周りでハングした実績がある。

そのため、B7では以下の方針とする。

```text
- 全体pytestは可能であれば実行する
- ハングする場合は強制終了してよい
- ハングした場合は、対象テスト結果とハング原因候補を報告する
- 対象テストが十分に通っている場合、closeout可能か判断する
```

### 11.4 手動GUI確認

可能であれば以下を確認する。

```text
- アプリ起動
- TEXT読込
- WAV読込
- 解析
- Waveform表示
- Preview表示
- Preview変形台形表示
- RightPane表示
- 選択イベントsummary初期状態
- 再生 / Stop
- Zoom In / Zoom Out / Reset Zoom
- Theme切替
- VMD保存
- 入力変更時の古い表示クリア
```

手動確認ができない場合は、理由を記録する。

---

## 12. 受け入れ条件

MS16-B7の受け入れ条件は以下である。

```text
- MS16-B1〜B6の成果が確認されている
- Qt / PySide6 / shiboken6 が依存に戻っていない
- 実行コードに PySide6 / Qt import が戻っていない
- 旧 src/gui/ 参照が戻っていない
- wxPython主系が維持されている
- RightPane基盤が存在する
- Info / Warning / 選択イベント / プリセット / モデルプロファイルの枠が存在する
- Preview変形台形表示が成立している
- Preview shape data contract が成立している
- 母音イベント選択の下地が成立している
- 古いPreview / 古い選択状態が残らない設計である
- compileall が通る
- B3〜B6対象テストが通る
- Preview関連テストが通る
- READMEがMS16完了状態と矛盾していない
- docs/Version_Control.md が更新されている
- docs/repo_milestone.md が更新されている
- docs/MMD_Audio_WAV_Compatibility_Specification.md がMS17送り方針と矛盾していない
- 音声拡張 / m4a / mp3 / FFmpeg / MMD用WAV がMS16実装済み扱いされていない
- .agent/skills/build-packaging-verification/SKILL.md の文字化け修正扱いが確認されている
- MS17への引き継ぎ事項が明記されている
```

---

## 13. リスクと対策

### 13.1 リスク: B7で新機能実装を始めてしまう

対策:

```text
- B7はcloseout / docs sync / verificationに限定する
- 新機能が必要なら別BlockまたはMS17へ送る
- コード変更は軽微補修に限る
```

### 13.2 リスク: MS17対象をMS16実装済み扱いする

対策:

```text
- 音声拡張とm4a対応はMS17送りと明記する
- docs/MMD_Audio_WAV_Compatibility_Specification.md の表記を補正する
- READMEで未実装機能を実装済みと書かない
```

### 13.3 リスク: docsだけが先行し実装と矛盾する

対策:

```text
- B1〜B6の実装結果と照合する
- 実装済み / 未実装 / 将来課題を分ける
- 断定できないものは「予定」「未実装」「MS17対象」として書く
```

### 13.4 リスク: 旧Qt / PySide6記述が現行依存に見える

対策:

```text
- 実行コード・依存・build/specは残存確認する
- docsの履歴記述は残してもよいが、現行要件と誤読されないようにする
```

### 13.5 リスク: 全体pytestがハングする

対策:

```text
- 対象テストを優先する
- 全体pytestは可能な場合のみ実行する
- ハングした場合は、対象テスト結果と原因候補を記録する
```

### 13.6 リスク: Skill文字化け修正が漏れる

対策:

```text
- .agent/skills/build-packaging-verification/SKILL.md をB7確認対象に含める
- 修正済みならdocs/skills整備として含める
- 単体コミットせず、B7 closeout整備に含めたことを記録する
```

### 13.7 リスク: READMEが内部開発者向けに寄りすぎる

対策:

```text
- READMEはエンドユーザー向けに保つ
- 詳細なBlock履歴は docs に置く
- READMEには現行機能と未実装予定を簡潔に書く
```

---

## 14. Antigravity 実装時の注意

Antigravity は以下を厳守すること。

```text
今回は MS16-B7 の closeout / documentation sync / integration verification です。

目的は、MS16-B1〜B6の成果を統合確認し、README / docs / milestone / changelog をMS16完了状態へ同期することです。

新機能実装は行わないでください。
MS17相当の音声拡張を開始しないでください。

音声拡張、m4a対応、mp3対応、FFmpeg / ffprobe、解析用WAV生成、MMD用WAV同時出力はMS17対象です。
MS16実装済みとして書かないでください。

旧 src/gui/ を参照しないでください。
Qt / PySide6 を再導入しないでください。
preview_transform は src/core/preview_transform.py を使用してください。

docs更新では、実装済み / 未実装 / MS17送り / 将来課題を明確に分けてください。
```

---

## 15. Antigravity 作業開始用プロンプト

以下を Antigravity に渡す想定とする。

```text
MS16-B7: 統合確認 / Docs補正 / MS16 Closeout を実施してください。

今回は closeout / documentation sync / integration verification です。
新機能実装ではありません。

目的:
- MS16-B1〜B6の成果を統合確認する
- Qt / PySide6 が再混入していないことを確認する
- wxPython主系が維持されていることを確認する
- RightPane / Preview変形台形表示 / Preview shape contract / 母音イベント選択下地が成立していることを確認する
- README / docs / repo_milestone / Version_Control をMS16完了状態へ同期する
- 音声拡張とm4a対応がMS17対象であることを明確にする

前提:
- MS16-B2は完了済みです。
- Qt / PySide6 は削除済みです。
- 旧 src/gui/ は削除済みです。
- preview_transform は src/core/preview_transform.py に移動済みです。
- MS16-B3〜B6が完了済みであることを確認してください。
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

MS16-B1〜B6の差分が未コミットで残っている場合は、B7作業を開始せず、状況を報告してください。
B1〜B6差分とB7差分を混在させないでください。

実施内容:
1. MS16-B1〜B6の実装結果を確認する。
2. PySide6 / shiboken6 / Qt / 旧 src/gui 参照が戻っていないか確認する。
3. requirements.txt / pyproject.toml / spec / build.ps1 を確認する。
4. RightPane / Preview変形台形表示 / Preview shape contract / 母音イベント選択下地が成立していることを確認する。
5. compileall を実行する。
6. B3〜B6対象テストを実行する。
7. Preview関連テストとwx系軽量テストを実行する。
8. 可能であれば手動GUI確認を行う。
9. README.md をMS16完了状態へ同期する。
10. docs/Version_Control.md を更新する。
11. docs/repo_milestone.md を更新する。
12. docs/MS16_and_Beyond_Milestone_Map_for_Antigravity.md を必要最小限更新する。
13. docs/MMD_Audio_WAV_Compatibility_Specification.md のMS16/MS17表記を確認し、音声拡張がMS17対象であることが明確になるよう補正する。
14. docs/MS16_Block_Breakdown_for_Antigravity.md を必要に応じて同期する。
15. .agent/skills/build-packaging-verification/SKILL.md の文字化け修正状態を確認し、B7のdocs/skills整備に含めるか判断する。
16. MS17への引き継ぎ事項を明記する。

B7では以下を行わないでください。
- mp3 / m4a 入力対応
- FFmpeg / ffprobe 接続
- 解析用WAV生成
- MMD用WAV同時出力
- MMD互換WAV検証
- 母音イベント編集
- Preview drag編集
- VMD再生成UI
- Warning判定本体
- プリセット保存
- モデルプロファイル保存
- MS17実装開始

確認コマンド例:

```powershell
.\.venv\Scripts\python.exe -m compileall .\src

.\.venv\Scripts\python.exe -m pytest tests\test_wx_ms16_b3_right_pane.py
.\.venv\Scripts\python.exe -m pytest tests\test_wx_ms16_b4_preview_shape.py
.\.venv\Scripts\python.exe -m pytest tests\test_wx_ms16_b5_preview_contract.py
.\.venv\Scripts\python.exe -m pytest tests\test_wx_ms16_b6_event_selection_foundation.py
.\.venv\Scripts\python.exe -m pytest tests\test_preview_transform.py tests\test_wx_ms15_b2_preview.py

Get-ChildItem -Recurse -File |
  Where-Object { $_.Extension -in ".py", ".toml", ".txt", ".ps1", ".spec", ".md" } |
  Select-String -Pattern "from PySide6|import PySide6|QtWidgets|QtCore|QtGui|shiboken6|from gui\.|import gui"

Select-String -Path .\requirements.txt, .\pyproject.toml -Pattern "PySide6|shiboken6|Qt|gui"

Get-ChildItem -Recurse -File .\docs |
  Where-Object { $_.Extension -eq ".md" } |
  Select-String -Pattern "MS16初期対応|m4a|mp3|FFmpeg|MMD用WAV"
```

全体pytestは、過去にGUI/ダイアログ周りでハング実績があります。
B7では全体pytestに固執せず、compileall、B3〜B6対象テスト、Preview関連テスト、既存wx系の軽量テストを優先してください。
全体pytestを実行してハングした場合は、強制終了し、ハング箇所と原因候補を報告してください。

完了報告では以下を報告してください。

- 実行したコマンド
- 確認したファイル
- 変更したファイル
- MS16-B1〜B6の確認結果
- Qt / PySide6 / 旧gui 残存確認結果
- RightPane確認結果
- Preview変形台形表示確認結果
- Preview shape contract確認結果
- 母音イベント選択下地確認結果
- 実行したテスト
- テスト結果
- 手動GUI確認結果
- README更新内容
- Version_Control更新内容
- repo_milestone更新内容
- MMD_Audio_WAV_Compatibility_Specificationの補正内容
- .agent skill文字化け修正の扱い
- MS17送り項目
- 最終 git diff --stat

---

## 16. 完了報告形式

Antigravity は作業完了時に以下の形式で報告する。

```text
## MS16-B7 Closeout 報告

### 1. 実行したコマンド

### 2. 作業前git状態
- branch:
- latest commit:
- working tree:

### 3. 確認したファイル

### 4. 変更したファイル

### 5. MS16-B1〜B6確認結果
- B1:
- B2:
- B3:
- B4:
- B5:
- B6:

### 6. Qt / PySide6 / 旧gui 残存確認
- requirements.txt:
- pyproject.toml:
- src:
- tests:
- build/spec:
- docs:

### 7. wxPython主系確認
- gui_wx:
- app起動:
- MainFrame:
- AppController:
- UiState:
- Theme:

### 8. RightPane確認
- Info:
- Warning:
- 選択イベント:
- プリセット:
- モデルプロファイル:

### 9. Preview確認
- 変形台形表示:
- control_points:
- shape_kind:
- source_event_index:
- frame_range:
- value_range:

### 10. 母音イベント選択下地確認
- selected_source_event_index:
- RightPane summary:
- clear条件:
- stale worker対策:

### 11. テスト結果
- compileall:
- B3対象テスト:
- B4対象テスト:
- B5対象テスト:
- B6対象テスト:
- Preview関連テスト:
- wx系軽量テスト:
- 全体pytest:

### 12. 手動GUI確認
- 実施有無:
- 確認項目:
- 未実施の場合の理由:

### 13. docs更新
- README.md:
- docs/Version_Control.md:
- docs/repo_milestone.md:
- docs/MS16_and_Beyond_Milestone_Map_for_Antigravity.md:
- docs/MMD_Audio_WAV_Compatibility_Specification.md:
- docs/MS16_Block_Breakdown_for_Antigravity.md:

### 14. .agent skill確認
- 対象:
- 文字化け状態:
- 修正有無:
- B7に含めたか:

### 15. MS17送り項目
- wav / mp3 / m4a:
- FFmpeg / ffprobe:
- 解析用WAV:
- MMD用WAV:
- 音声変換エラー処理:
- ライセンス / 配布:

### 16. MS16 Closeout判定
- closeout可否:
- 理由:
- 残課題:

### 17. 最終git状態
- git diff --stat:
- git diff --name-only:
- staged / unstaged:

### 18. 推奨コミットメッセージ
```

---

## 17. 完了後の次アクション

MS16-B7完了後、通常は MS16 closeout とする。

次に進むべきマイルストーンは以下。

```text
MS17: wav / mp3 / m4a 入力対応 + FFmpeg / ffprobe + 解析用WAV + MMD用WAV同時出力
```

MS17開始前に、以下の設計を別途行う。

```text
- MS17 Block Breakdown
- FFmpeg / ffprobe 接続方針
- FFmpeg同梱有無
- ライセンス / NOTICE / THIRD_PARTY_LICENSES 方針
- 解析用WAV生成基盤
- MMD用WAV保存導線
- 音声変換系エラー分類
- GUI Busy / 300秒確認ダイアログ / terminate / kill 方針
```

ただし、以下の場合はMS17へ進む前に補修する。

```text
- Qt / PySide6 が残存している
- wxPython主系が起動できない
- RightPaneが壊れている
- Preview表示が壊れている
- shape contract が壊れている
- 選択状態が古い結果に残る
- docsがMS16実装済み範囲と矛盾している
- 音声拡張がMS16実装済み扱いされている
```

---

## 18. 変更履歴

### 2026-05-11 / 初版

- MS16-B1〜B6までの流れを踏まえ、MS16-B7の実装プランを作成。
- B7を「統合確認 / Docs補正 / MS16 Closeout」に限定。
- MS16で実装済みの範囲、MS17へ送る音声拡張範囲、docs補正対象を整理。
- Qt / PySide6排除、RightPane、Preview変形台形表示、Preview shape data contract、母音イベント選択下地の確認観点を定義。
- `docs/MMD_Audio_WAV_Compatibility_Specification.md` のMS16/MS17表記補正をB7対象に含めた。
- `.agent/skills/build-packaging-verification/SKILL.md` の文字化け修正確認をB7対象に含めた。
- 全体pytestのハング実績を踏まえ、対象テスト・軽量テスト・手動GUI確認を優先する方針を定義。
