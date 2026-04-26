# MS15-B6_Implementation_Plan

## 1. Document Control

- Document Name: `MS15-B6_Implementation_Plan.md`
- Milestone: `MS15`
- Block: `MS15-B6`
- Title: `MS15 Closeout / 最小 Polish / 最終検収`
- Target Series: `Ver 0.4.x`
- Project: `MMD_AutoLipTool`
- GUI Mainline: `wxPython`
- Primary GUI Path: `src/gui_wx/`
- Status: Draft for implementation

---

## 2. Purpose

MS15-B6 は、MS15-B1〜B5 で実装された以下の機能群を、MS15 として閉じられる状態へ整理・検収するための closeout block である。

- B1: waveform 表示基盤
- B2: Preview 表示基盤
- B3: 再生基盤と再生位置同期
- B4: viewport / Zoom / auto-follow
- B5: UI 状態統合 / 最小 UI 整理 / テーマカラー復元

B6 の目的は、新機能追加ではなく、MS15 範囲の最終確認、軽微な polish、状態・文言・テーマ・操作導線の不整合修正、ドキュメント同期を行い、MS16 へ進める状態を作ることである。

---

## 3. Fixed Decisions

### 3.1 B6 の主目的

B6 は以下を主目的とする。

- MS15-B1〜B5 の実装結果の最終確認
- MS15 範囲に限定した軽微な polish
- MS15 範囲に限定した不整合修正
- MS15 closeout に必要なドキュメント同期
- 自動テスト、Antigravity 実行確認、ユーザー実働確認による完了判定

B6 は、単なる確認だけではなく、MS15 を閉じるために必要な最小修正を許可する。

ただし、新機能追加は行わない。

---

### 3.2 status 文言整理の範囲

B6 で扱う status 文言整理は、MS15 で追加・変更された主要状態に限定する。

対象候補:

- idle / ready
- input loaded
- analysis invalidated
- analysis ready
- playback ready
- playing
- stopped
- playback failed
- zoom ready / zoom unavailable
- theme changed
- busy

以下は対象外とする。

- アプリ全体の status 文言体系の全面再設計
- すべてのエラー文言の統一
- 詳細な disabled reason 表示
- tooltip 全面整理

---

### 3.3 UI polish の範囲

B6 で扱う UI polish は、MS15 範囲の軽微な違和感修正に限定する。

対象候補:

- Play / Stop / Zoom In / Zoom Out / Reset Zoom の enable / disable 整合
- operation area 内でのボタン配置の明確な破綻修正
- theme 適用後の主要領域の視認性
- waveform / Preview / status / operation area の基本色の不整合
- light / dark / system 切替時に読めない文字や極端に見づらい領域
- 再生位置線、grid、label、Preview segment の最低限の視認性
- B1〜B5 の実装により生じた明確な操作違和感

以下は対象外とする。

- pixel-perfect なモックアップ再現
- spacing / margin の全面調整
- アイコン最終化
- DAW レベルの再生 UX 最適化
- Pan / Seek / Loop / Pause 追加
- continuous zoom
- mp3 対応
- 音声のみ入力対応

---

### 3.4 Done 条件に含める確認範囲

B6 の Done 条件には、以下を含める。

1. 自動テスト通過
2. Antigravity 側での実行確認
3. ユーザー側での実働確認

ユーザー実働確認は、MS15 closeout の最終受け入れ確認として扱う。

ただし、ユーザー実働確認で見つかった問題は、以下のように分類する。

- MS15-B1〜B5 の仕様不達または明確な回帰  
  → B6 内で修正対象にしてよい
- 見た目の好み、最終 polish、将来拡張に近いもの  
  → B6 では記録に留め、必要なら後続 block へ送る
- MS16 以降の機能に属するもの  
  → B6 では扱わない

---

### 3.5 ドキュメント更新

B6 では、MS15 closeout に必要なドキュメント更新を含める。

対象候補:

- `docs/MS15-B6_Implementation_Plan.md`
- `docs/MS15_Block_Breakdown.md`
- `docs/repo_milestone.md`
- `docs/Version_Control.md`
- 必要に応じた MS15 closeout note

ただし、ドキュメント更新は実装事実と検収結果に合わせる。

B6 開始時点で未完了の事項を、完了済みとして先に書かない。

---

### 3.6 新機能追加の禁止

B6 では新機能追加を禁止する。

禁止例:

- Pause
- Seek
- Loop
- Pan
- continuous Zoom
- mp3 対応
- 音声のみ入力対応
- 再生速度変更
- waveform 編集機能
- Preview 編集機能
- 新しい設定画面
- 新しい詳細 tooltip
- 詳細 disabled reason 表示
- 大規模 state machine

B6 で許可されるのは、既存 MS15 仕様を満たすための最小修正、検証補助、テスト補強、文書同期に限る。

---

## 4. Preconditions

B6 着手前に、以下を確認する。

### 4.1 Branch / Repo

- `git status`
- 現在 branch
- default branch
- MS15 関連 branch
- `git log --oneline -n 8`

想定される作業 branch:

- `feature/ms15-b1-waveform-foundation`

ただし、開始時点で必ず repo 状態を確認し、main を正本と決め打ちしない。

### 4.2 B4 / B5 差分修正の反映状況

直前に実施した以下の修正が反映済みであることを確認する。

- B4: 再生中 Zoom anchor が `playback_position_sec` + `anchor_ratio=0.6` になっている
- B5: Zoom action state が `duration_sec` / viewport controller ready / zoom_factor / busy を基準に判定されている

該当修正が未コミットの場合は、B6 本体に入る前に作業状態を明確化する。

---

## 5. In Scope

MS15-B6 に含めるものは以下とする。

### 5.1 実装確認

- B1 waveform 表示基盤の最終確認
- B2 Preview 表示基盤の最終確認
- B3 Play / Stop / playback position sync の最終確認
- B4 viewport / Zoom / auto-follow の最終確認
- B5 UiState / theme / action state の最終確認

### 5.2 軽微な polish

- MS15 範囲の status 文言の最小整理
- Play / Stop / Zoom 系ボタン状態の最小整理
- theme 切替後の主要 UI 視認性の最小修正
- operation area の明確な配置破綻の修正
- waveform / Preview の再生位置線・grid・label の視認性確認
- placeholder 表示の明確な破綻修正

### 5.3 テスト

- 既存 MS15 テストの実行
- B6 で必要な最小テスト追加または更新
- B4/B5 差分修正後の回帰確認
- theme / zoom / playback / invalidation 周辺の軽量テスト補強

### 5.4 実行確認

- Antigravity 側での起動確認
- TEXT + WAV 読み込み確認
- 解析実行確認
- waveform / Preview 表示確認
- Play / Stop 確認
- Zoom In / Zoom Out / Reset Zoom 確認
- 2x 以上での auto-follow 確認
- light / dark / system theme 切替確認
- theme 保存・復元確認

### 5.5 ドキュメント同期

- MS15-B6 実装結果の記録
- MS15 closeout 状態の記録
- `repo_milestone.md` 更新
- `Version_Control.md` 更新
- 必要に応じて `MS15_Block_Breakdown.md` 更新

---

## 6. Out of Scope

MS15-B6 では以下を行わない。

- 新機能追加
- MS16 以降の作業
- mp3 対応
- MMD 用 WAV 同時出力
- 音声のみ入力対応
- 同音母音谷スムージング改善
- 発音単位スロープ設定
- 英語対応
- Pause
- Seek
- Loop
- Pan
- continuous Zoom
- DAW レベルの再生 UX 最適化
- status 文言の全アプリ全面整理
- tooltip 全面整理
- detailed disabled reason 表示
- pixel-perfect UI polish
- spacing / margin 全面調整
- アイコン最終整理
- Qt / PySide6 側の丸移植
- 大規模 state machine 導入

---

## 7. Target Files

B6 で確認・変更対象になり得るファイルは以下とする。

### 7.1 Core MS15 wx GUI

- `src/gui_wx/main_frame.py`
- `src/gui_wx/app_controller.py`
- `src/gui_wx/ui_state.py`
- `src/gui_wx/waveform_panel.py`
- `src/gui_wx/preview_panel.py`
- `src/gui_wx/placeholder_panels.py`
- `src/gui_wx/playback_controller.py`
- `src/gui_wx/viewport_controller.py`
- `src/gui_wx/theme.py`
- `src/gui_wx/app.py`
- `src/main.py`

### 7.2 Related UI Panels

- `src/gui_wx/info_panel.py`
- `src/gui_wx/parameter_panel.py`

### 7.3 Settings

- `src/gui/settings_store.py`
- 既存 settings / config 関連ファイル

### 7.4 Tests

- `tests/test_wx_ms15_b1_waveform.py`
- `tests/test_wx_ms15_b2_preview.py`
- `tests/test_wx_ms15_b3_playback.py`
- `tests/gui_wx/test_viewport_controller.py`
- `tests/test_wx_ms15_b5_state_theme.py`
- 必要に応じて B6 用の追加テスト

### 7.5 Documents

- `docs/MS15-B6_Implementation_Plan.md`
- `docs/MS15_Block_Breakdown.md`
- `docs/repo_milestone.md`
- `docs/Version_Control.md`

---

## 8. Required Verification Points

### 8.1 B1 Waveform

確認項目:

- WAV 読み込み後に waveform panel が表示される
- placeholder から waveform 表示へ遷移する
- 再生位置線を受け取れる
- viewport 変更に応じて描画範囲が変わる
- theme 切替後も波形・grid・label・cursor が視認できる

### 8.2 B2 Preview

確認項目:

- 解析成功後に Preview が表示される
- `analysis_result_valid == False` 時に placeholder へ戻る
- 再生位置線を受け取れる
- viewport 変更に応じて描画範囲が変わる
- theme 切替後も lane / segment / label / cursor が視認できる

### 8.3 B3 Playback

確認項目:

- WAV 読み込み後、解析結果なしでも Play できる
- Play 開始位置は `0.0 sec`
- 再生中 Play 再押下は無視される
- Stop で `0.0 sec` に戻る
- 自然終了時も `0.0 sec` に戻る
- busy 中 Play は不可
- waveform / Preview に同一 playback position が供給される

### 8.4 B4 Viewport / Zoom / Auto-follow

確認項目:

- `1x / 2x / 4x / 8x` の離散 Zoom が成立する
- Reset Zoom で full-range + `1x` に戻る
- waveform / Preview が同一 viewport を受ける
- 2x 以上で auto-follow が視認できる
- 80% 到達で follow 判定される
- follow 後は 60% 付近へ再配置される
- 再生中 Zoom は `playback_position_sec` 60% anchor になる
- 停止中 Zoom は viewport center anchor になる
- clamp 時は合法 viewport が優先される

### 8.5 B5 UiState / Action State / Theme

確認項目:

- `busy` が overlay flag として扱われている
- `analysis_ready` と `playback_ready` が分離されている
- Play は `analysis_result_valid` に依存しない
- Save VMD は `analysis_ready` に依存する
- Zoom は `duration_sec` / viewport ready / zoom_factor / busy に依存する
- Zoom In は `8x` で disabled になる
- Zoom Out は `1x` で disabled になる
- Reset Zoom は duration 有効時に可能
- `light / dark / system` が選択できる
- user selected theme mode と resolved theme が分離されている
- 保存対象は user selected theme mode である
- 起動時に theme mode が復元される

---

## 9. Implementation Steps

### Step 0. Entry Check

- `git status`
- 現在 branch 確認
- HEAD 確認
- MS15 関連 branch 確認
- B4/B5 差分修正が反映済みか確認
- 未コミット変更がある場合は内容を確認

Exit condition:

- 作業対象 branch と現在状態が明確になっている
- B6 で扱うべき差分が把握されている

---

### Step 1. Read MS15 Plans and Current Implementation

読む文書:

- `docs/MS15-B1_Implementation_Plan.md`
- `docs/MS15-B2_Implementation_Plan.md`
- `docs/MS15-B3_Implementation_Plan.md`
- `docs/MS15-B4_Implementation_Plan.md`
- `docs/MS15-B5_Implementation_Plan.md`
- `docs/MS15_Block_Breakdown.md`

読む実装:

- `src/gui_wx/` の MS15 関連ファイル
- MS15 関連テスト

Exit condition:

- B1〜B5 の仕様と現行実装の対応関係が確認済みである

---

### Step 2. Run Existing MS15 Tests

最低限、以下を実行する。

```bash
python -m pytest tests/gui_wx/test_viewport_controller.py tests/test_wx_ms15_b3_playback.py tests/test_wx_ms15_b5_state_theme.py
python -m pytest tests/test_wx_ms15_b1_waveform.py tests/test_wx_ms15_b2_preview.py
````

必要に応じて、環境に合わせて以下のように `PYTHONPATH` を設定する。

```powershell
$env:PYTHONPATH="src;tests"
.\.venv\Scripts\python.exe -m pytest tests/gui_wx/test_viewport_controller.py tests/test_wx_ms15_b3_playback.py tests/test_wx_ms15_b5_state_theme.py
.\.venv\Scripts\python.exe -m pytest tests/test_wx_ms15_b1_waveform.py tests/test_wx_ms15_b2_preview.py
```

Exit condition:

* 既存 MS15 テストの結果が記録されている
* 失敗があれば、B6 対象か対象外か分類されている

---

### Step 3. Check and Fix MS15-Scoped Status Text

MS15 範囲の主要状態について、明確な破綻または不整合があれば最小修正する。

対象候補:

* idle
* ready for analysis
* analysis invalidated
* analysis ready
* playback ready
* playing
* stopped
* playback failed
* theme changed

方針:

* 全面再設計しない
* 詳細 reason を増やさない
* 文言は短く、既存 UI に馴染むものにする
* status 文言の管理箇所をむやみに増やさない

Exit condition:

* MS15 操作中に明確に矛盾する status が出ない

---

### Step 4. Check and Fix Button Action States

以下の button / menu 状態を確認する。

* Load TEXT
* Load WAV
* Run Analysis
* Save VMD
* Play
* Stop
* Zoom In
* Zoom Out
* Reset Zoom
* Theme menu

方針:

* `UiState` と `AppController` query helper を優先する
* `MainFrame` に過剰な状態判断を増やさない
* Play は analysis result に依存させない
* Save VMD は analysis ready に依存させる
* Zoom は duration / viewport ready / zoom factor / busy に依存させる

Exit condition:

* 押せるべきでない主要操作が disabled またはロジックガードで安全に拒否される
* 押せるべき操作が不要に disabled になっていない

---

### Step 5. Check and Fix Theme Visibility

light / dark / system の各 theme で主要 UI の視認性を確認する。

対象:

* MainFrame
* operation area
* parameter panel
* info panel
* waveform panel
* Preview panel
* status area
* playback cursor
* waveform grid
* Preview lane / segment / label

方針:

* 基本色の不整合のみ直す
* pixel-perfect polish は行わない
* spacing / margin 最終調整は行わない
* OS theme リアルタイム監視は行わない

Exit condition:

* light / dark の双方で主要 UI が読める
* system 選択時に resolved theme が反映される
* theme mode が保存・復元される

---

### Step 6. Manual Execution Check in Antigravity

Antigravity 側で可能な範囲の実行確認を行う。

確認シナリオ:

1. アプリ起動
2. TEXT 読み込み
3. WAV 読み込み
4. waveform 表示
5. Play
6. Stop
7. Zoom In
8. Zoom Out
9. Reset Zoom
10. 2x 以上で Play し、auto-follow を確認
11. 解析実行
12. Preview 表示
13. 入力変更時に Preview が placeholder へ戻る
14. light / dark / system theme 切替
15. アプリ再起動後の theme 復元

Exit condition:

* 実行確認結果が記録されている
* 明確な MS15 仕様不達があれば修正または報告されている

---

### Step 7. Add or Update Minimal Tests

必要な場合のみ、B6 用に最小テストを追加または更新する。

候補:

* Zoom action state の境界条件
* theme mode 保存・復元 helper
* analysis invalidation 時の Preview placeholder
* playback ready と analysis ready の分離
* Reset Zoom state
* status key の最小遷移

方針:

* GUI 描画そのものを過剰にテストしない
* wx の実ウィンドウ依存を増やしすぎない
* controller / state helper のテストを優先する

Exit condition:

* B6 で修正したロジックに対する最低限の回帰テストがある

---

### Step 8. Documentation Sync

実装・検証完了後、ドキュメントを同期する。

対象:

* `docs/MS15-B6_Implementation_Plan.md`
* `docs/MS15_Block_Breakdown.md`
* `docs/repo_milestone.md`
* `docs/Version_Control.md`

記載内容:

* MS15-B6 の実施内容
* MS15 closeout 状態
* 実行テスト
* 残した保留事項
* MS16 に送る事項

Exit condition:

* MS15 が closeout されたことが docs 上で追跡可能である
* MS16 に進む前提が明確になっている

---

## 10. Acceptance Criteria

MS15-B6 の Acceptance Criteria は以下とする。

1. B1〜B5 の主要実装が repo 上で確認できる
2. B4/B5 の既知差分修正が反映済みである
3. MS15 関連自動テストが通過している
4. waveform が WAV 読み込み後に表示される
5. Preview が解析成功後に表示される
6. Preview が解析 invalid 時に placeholder へ戻る
7. Play / Stop が B3 仕様どおり動作する
8. 再生位置線が waveform / Preview に同期表示される
9. Zoom In / Zoom Out / Reset Zoom が B4/B5 仕様どおり動作する
10. 2x 以上で auto-follow が視認できる
11. 再生中 Zoom anchor が `playback_position_sec` 60% 仕様に一致している
12. 停止中 Zoom anchor が viewport center 仕様に一致している
13. Zoom enable 条件が duration / viewport ready / zoom factor / busy に基づく
14. Play が `analysis_result_valid` に依存しない
15. Save VMD が `analysis_ready` に依存する
16. `busy` が overlay flag として扱われている
17. `analysis_ready` と `playback_ready` が分離されている
18. light / dark / system theme が選択できる
19. theme mode が保存・復元される
20. 主要 UI が light / dark 双方で視認できる
21. MS15 範囲の status 文言に明確な矛盾がない
22. MS15-B6 で新機能追加をしていない
23. MS15-B6 で pixel-perfect polish をしていない
24. Antigravity 側で実行確認が行われている
25. ユーザー側で実働確認が行われている
26. MS15 closeout に必要な docs が更新されている

---

## 11. Definition of Done

MS15-B6 は、以下を満たした時点で Done とする。

1. `git status` が意図した状態である
2. MS15-B6 の変更対象が B6 scope 内に収まっている
3. MS15 関連テストが通過している
4. Antigravity 側の実行確認が完了している
5. ユーザー側の実働確認が完了している
6. 発見された問題が以下のいずれかに分類済みである

   * B6 内で修正済み
   * B6 対象外として後続へ送る
   * 記録のみ
7. `docs/MS15-B6_Implementation_Plan.md` が追加されている
8. `docs/MS15_Block_Breakdown.md` が必要に応じて更新されている
9. `docs/repo_milestone.md` が MS15 closeout 状態に更新されている
10. `docs/Version_Control.md` が更新されている
11. MS16 へ進む前提が明確である
12. 新機能追加が混入していない
13. B6 の commit が作成されている

---

## 12. Expected Final Report Format

B6 実装完了時、Antigravity は以下を報告する。

1. 作業 branch / HEAD
2. 変更したファイル一覧
3. 実施した確認内容
4. 実施した軽微修正内容
5. status 文言整理の有無と内容
6. UI polish の有無と内容
7. theme 視認性確認結果
8. Play / Stop / Zoom / auto-follow 確認結果
9. 実行したテストと結果
10. Antigravity 側実行確認結果
11. ユーザー実働確認が必要な項目
12. 更新した docs
13. 残した保留事項
14. commit hash
15. MS15 を closeout 可能かどうかの判定

---

## 13. User Verification Checklist

ユーザー側の実働確認では、最低限以下を確認する。

1. アプリが起動する
2. TEXT を読み込める
3. WAV を読み込める
4. waveform が表示される
5. Play できる
6. Stop で先頭へ戻る
7. Zoom In / Zoom Out / Reset Zoom が動く
8. 2x 以上で再生中に auto-follow する
9. 解析実行後に Preview が表示される
10. 再生位置線が waveform / Preview の両方に出る
11. theme を light / dark / system で切り替えられる
12. 再起動後に theme が復元される
13. 明らかに読めない文字・背景がない
14. MS15 範囲で明らかに押せてはいけないボタンが押せる状態になっていない

ユーザー確認で発見された問題は、MS15 仕様不達か、B6 対象外 polish か、MS16 以降の課題かを分類する。

---

## 14. Handoff to MS16

MS15-B6 完了後、次 milestone は MS16 とする。

MS16 の予定領域:

* mp3 対応
* MMD 用 WAV 同時出力

MS15-B6 では MS16 の実装には入らない。

MS15-B6 の完了時点で、MS16 開始前に以下を確認できる状態にする。

* wx 主系で waveform / Preview / playback / viewport / theme が成立している
* MS15 の実装と docs が同期している
* MS15 由来の大きな未解決仕様差分が残っていない
* MS16 が音声入力形式拡張に集中できる
