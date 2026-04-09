# MS13-B5 Implementation Plan

## 1. Document Control

- Document Name: `MS13-B5_Implementation_Plan.md`
- Milestone: `MS13`
- Block: `MS13-B5`
- Title: `将来拡張の接続点整理`
- Target Series: `Ver 0.4.x`
- Project: `MMD_AutoLipTool`

---

## 2. Purpose

MS13-B5 では、wxPython 主系 GUI に対して、将来 block で実装される機能を安全に差し込めるように、**handler / controller / status / worker 受け口の最小接続点**を整理する。

本 block の目的は、機能実装そのものではなく、**今後の MS14 以降で GUI と処理本体を無理なく接続できる導線を先に整えておくこと**である。

---

## 3. Fixed Decisions

本 block では、以下の前提を固定とする。

### 3.1 B5 の到達点
- 将来機能を差し込むための handler / controller 接続点まで用意する
- 命名整理だけで終えず、後続 block で実際に配線しやすい受け口を定義する
- ただし、処理本体の実装までは行わない

### 3.2 GUI から将来機能への接続方式
- `MainFrame` から別の controller / actions 受け口へ委譲する
- `MainFrame` に処理本体を直接増やさない
- pub-sub / event bus のような新基盤は導入しない

### 3.3 Worker 系の受け皿
- worker 起動入口を用意する
- 完了 / 失敗 / 進捗反映の受け口まで stub を置く
- 実際の thread / worker 実装は行わない

### 3.4 将来拡張対象の範囲
- 解析実行
- file 操作
- 再生系主要操作

上記の将来接続点は整理対象に含める。  
一方で、waveform / preview / 設定画面本体などの個別実装は対象外とする。

### 3.5 UI 部品アクセス整理
- 必要最小限の accessor / view helper を用意して参照経路を整理する
- ただし、panel / widget の大規模クラス分割は行わない

### 3.6 ステータス更新
- ステータス更新用の共通入口を 1 本用意する
- 個別処理が frame に直接書き込む形を避ける

### 3.7 settings との関係
- B4 で作成した load / apply 導線は維持する
- 将来保存や設定変更通知に備えた hook 名だけ置いてよい
- 保存側の枠組みは作らない

---

## 4. Goal

MS13-B5 の完了条件は、以下を満たすこととする。

1. `MainFrame` から将来機能を直接実装せず、controller / actions 受け口へ委譲できる
2. 解析実行 / file 操作 / 再生系主要操作の接続点が命名整理されている
3. worker 開始 / 進捗 / 完了 / 失敗の最小受け口が存在する
4. ステータス更新が共通入口経由で扱える
5. B4 の settings load / apply を壊さず、将来保存や変更通知に向けた hook 名だけ置ける
6. 実処理、保存、thread 実装、MS14 以降の機能本体を流入させていない

---

## 5. In Scope

MS13-B5 に含めるものは以下とする。

- `MainFrame` から分離された controller / actions 受け口の導入
- 将来機能ごとの handler 名 / method 名 / 接続点の整理
- file 操作 / 解析実行 / 再生系主要操作の最小 routing 受け口
- worker 起動 / 進捗 / 完了 / 失敗の stub 受け口
- ステータス更新用の共通入口
- 必要最小限の accessor / view helper
- settings 保存や変更通知の将来用 hook 名の最小整理

---

## 6. Out of Scope

MS13-B5 では以下を行わない。

- file dialog の本実装
- 実ファイル読込 / 保存の本実装
- 音声再生の本実装
- 解析処理の本実装
- VMD 出力の本実装
- waveform / preview の本実装
- worker / thread の実運用
- pub-sub / event bus の導入
- 大規模な MVC 再編
- settings 保存
- settings migration
- B6 の統合整理
- MS14 以降の parity 回復や再生 UX 実装

---

## 7. Expected Functional Boundary

B5 は、**将来の機能実装が差し込まれる「口」を整理する block** である。  
ここで作るのは「処理」ではなく「接続点」である。

block 境界は以下のように切る。

- B1: wx 主系入口
- B2: frame 最小骨格
- B3: メニュー / 基本操作列 / ステータス最小配置
- B4: settings load / apply
- **B5: 将来機能の接続点整理**
- B6: MS13 統合整理

したがって、B5 では「押したら動く」よりも、**押された後にどの controller 入口へ委譲されるべきかが明確であること**を優先する。

---

## 8. Design Policy

## 8.1 MainFrame Fatigue Avoidance
`MainFrame` に将来機能の処理本体を増やさない。  
UI 構築とイベント受理に寄せ、実際の操作意図は controller / actions 側へ渡す。

## 8.2 Minimal Controller Boundary
本格アーキテクチャ導入ではなく、後続 block で安全に拡張できる最小 controller 境界だけを用意する。

## 8.3 Stub First, Real Logic Later
B5 時点では、受け口は stub でよい。  
ただし、後続実装時に名前や責務がそのまま引き継げるように整理する。

## 8.4 One Status Entry
ステータス更新は 1 本の共通入口に集約する。  
複数箇所から status label を直接触る構造を避ける。

## 8.5 View Access by Helper
後続 block で widget 参照が散らばらないよう、必要最小限の accessor / view helper を用意する。  
ただし、この段階で大規模分割はしない。

## 8.6 Preserve B4
B4 までの settings load / apply 導線は壊さない。  
B5 では、保存や変更通知の「将来 hook 名」までに留める。

---

## 9. Future Expansion Targets to Prepare

B5 で接続点を整理する対象は以下とする。

### 9.1 File Operation Entry Points
- text 選択
- wav 選択
- vmd 保存
- 必要なら「最近使ったパス」や「初期ディレクトリ」へ将来つながる名前だけを整理する

### 9.2 Analysis Entry Points
- 解析実行開始
- 実行前 validation
- 実行中の UI 状態反映
- 完了時反映
- 失敗時反映

### 9.3 Playback Entry Points
- 再生
- 一時停止
- 停止
- シーク系の将来接続点
- 再生状態更新の将来接続点

### 9.4 Worker Entry Points
- 処理開始 request
- 進捗通知受け口
- 完了通知受け口
- 失敗通知受け口

### 9.5 Settings Hook Names
- 将来の設定変更通知
- 将来の保存要求
- 必要なら UI 反映再実行の入口名

B5 ではこれらを **実装しない**。  
将来 block が迷わず差し込めるように、名前・責務・接続方向を決める。

---

## 10. Recommended Internal Structure

repo 実態に合わせて調整してよいが、概念上は以下の構成を推奨する。

### 10.1 MainFrame
責務:
- UI 構築
- UI イベント受理
- controller / actions への委譲
- status 更新入口の保持
- 必要最小限の view helper 公開

責務に含めないもの:
- 解析処理本体
- 再生処理本体
- file 保存 / 読み込み本体
- worker 実処理

### 10.2 App Controller / UI Actions Sink
責務:
- GUI 操作意図を受け取る
- 現段階では stub / no-op / status 更新のみでもよい
- 将来 block で実処理を受け入れる最小境界になる

候補メソッド例:
- `request_select_text()`
- `request_select_wav()`
- `request_run_analysis()`
- `request_save_vmd()`
- `request_play()`
- `request_pause()`
- `request_stop()`

### 10.3 Worker Hooks
責務:
- `start_*` 系入口名
- `on_progress`
- `on_success`
- `on_error`

現時点では stub でよいが、将来 thread / worker が接続しやすいように分ける。

### 10.4 Status Update Entry
責務:
- UI 上の status 表示更新を一元化する
- 他の handler が直接 label を触らないようにする

### 10.5 View Accessor / View Helper
責務:
- 後続 block が必要最小限の UI 状態へアクセスするための補助
- widget 参照名を分散させない

---

## 11. Suggested Naming Direction

実装時の命名は repo の既存規約に合わせること。  
ただし方向性は以下を推奨する。

### 11.1 UI Event Names
- `on_select_text`
- `on_select_wav`
- `on_run_analysis`
- `on_save_vmd`
- `on_play`
- `on_pause`
- `on_stop`

### 11.2 Controller Request Names
- `request_select_text`
- `request_select_wav`
- `request_run_analysis`
- `request_save_vmd`
- `request_playback_play`
- `request_playback_pause`
- `request_playback_stop`

### 11.3 Worker Hook Names
- `start_analysis_worker`
- `on_analysis_progress`
- `on_analysis_success`
- `on_analysis_error`

### 11.4 Settings Hook Names
- `on_settings_changed`
- `request_settings_save`
- `reapply_settings_to_view`

命名は固定ではないが、**UI イベント名** と **controller 側 request 名** を分ける方針は維持する。

---

## 12. UI Enable/Disable Policy in B5

B3 で未実装項目は disabled とする方針があるため、B5 でもこの原則を維持する。

- UI が disabled のままでもよい
- ただし、将来の接続先として handler / controller 名は整理してよい
- 必要があっても、B5 を理由に実機能を有効化しない
- 一部の安全な placeholder 操作を有効にする場合でも、実処理ではなく stub で止める

B5 の主眼は「押せること」ではなく「どこへ渡るかが定まること」である。

---

## 13. Step Breakdown

## Step 1. Confirm B3 / B4 State
- B3 までの wx UI 構成を確認する
- B4 の settings load / apply 導線を確認する
- B5 で変更可能な箇所と壊してはいけない箇所を明確にする

### Exit Condition
- 現在の `MainFrame` 構成と B4 接続位置が把握できている

---

## Step 2. Identify Future Entry Points
- file 操作
- 解析実行
- 再生系主要操作
について、将来必要となる操作入口を洗い出す

### Exit Condition
- B5 で用意すべき request / hook 一覧が確定している

---

## Step 3. Introduce Controller / Actions Sink
- `MainFrame` から委譲される受け口を導入する
- まずは最小単位でよい
- 処理本体は持たせない
- 必要なら status 更新だけ返す stub とする

### Exit Condition
- `MainFrame` が将来機能の入口を直接抱え込まない構造になっている

---

## Step 4. Organize UI Event Routing
- menu / button / 将来操作候補のイベントを整理する
- UI イベントから controller / actions sink に流れる導線を作る
- ただし disabled ポリシーは壊さない

### Exit Condition
- イベント受理と処理受け口の責務が分離されている

---

## Step 5. Add Worker Stub Hooks
- analysis 実行など将来非同期化される箇所について、worker 入口名を整理する
- progress / success / error の受け口 stub を追加する
- 実際の thread 起動は行わない

### Exit Condition
- worker 系の将来接続点が名前として揃っている

---

## Step 6. Add One Status Entry
- ステータス更新を 1 本の共通入口へまとめる
- controller / actions sink からも扱えるようにする
- label 直書きが散らばらないようにする

### Exit Condition
- ステータス表示更新の経路が一元化されている

---

## Step 7. Add Minimal View Accessor / Helper
- 後続 block が必要最小限の UI 状態を参照できるようにする
- widget 生参照の散乱を抑える
- ただし大規模 class 分割はしない

### Exit Condition
- view access の最小整理ができている

---

## Step 8. Add Settings-Related Hook Names
- B4 の導線は維持したまま、将来用の hook 名だけを整理する
- 保存や migration は入れない

### Exit Condition
- settings 周りの将来接続点が追加されているが、保存機能は未実装のままである

---

## Step 9. Boundary Audit
- 実処理が混入していないか確認する
- thread / worker 実装が混入していないか確認する
- B6 / MS14 以降が流入していないか確認する

### Exit Condition
- B5 が「接続点整理」に閉じている

---

## 14. Candidate File Touch Areas

repo 実態に応じて判断するが、変更対象は概ね以下に留める。

- `src/gui_wx/` 配下
  - `MainFrame`
  - UI event binding 周辺
  - status 表示周辺
  - 必要最小限の view helper
- controller / actions 受け口用の最小新規ファイル
- worker hook 名を置く最小 helper / stub
- B4 settings との接続名整理に必要な最小箇所

`src/main.py` は原則として大きく触らない。  
B5 の中心は wx GUI 層とその接続点整理である。

---

## 15. Acceptance Criteria

以下をすべて満たしたら B5 完了とみなす。

1. `MainFrame` から controller / actions 受け口へ委譲する導線が存在する
2. file 操作 / 解析実行 / 再生系主要操作の将来接続点が整理されている
3. worker 開始 / 進捗 / 完了 / 失敗の stub 受け口が存在する
4. ステータス更新用の共通入口が存在する
5. 必要最小限の accessor / view helper がある
6. B4 の settings load / apply を壊していない
7. 保存を実装していない
8. 実 worker / 実解析 / 実再生 / 実ファイル操作を実装していない
9. B6 / MS14 以降を流入させていない

---

## 16. Test Plan

## 16.1 Startup Regression
- B5 導入後も wx GUI が起動することを確認する
- B4 の settings load / apply が壊れていないことを確認する

## 16.2 Event Routing Smoke Check
- 既存 UI イベントが controller / actions 側に流れることを確認する
- ただし実処理は発火しなくてよい
- status 更新や no-op で十分

## 16.3 Disabled Policy Preservation
- B3 で disabled のままにすべき項目が勝手に有効化されていないことを確認する

## 16.4 Worker Hook Presence
- analysis など将来非同期化される箇所に、start / progress / success / error の入口名が存在することを確認する

## 16.5 Status Entry Consistency
- 複数箇所からステータス更新を呼んでも、共通入口経由になっていることを確認する

## 16.6 No Feature Leakage
- file dialog 本体
- 保存本体
- 再生本体
- thread / worker 実装
が混入していないことを確認する

---

## 17. Risks and Control

## Risk 1. MainFrame Overgrowth
委譲先を作らず `MainFrame` に実装が寄る可能性がある。  
**Control:** UI イベントと処理受け口を分離する。

## Risk 2. Premature Architecture
B5 を理由に大規模 MVC / event bus 導入へ進む可能性がある。  
**Control:** controller / actions sink は最小に留める。

## Risk 3. Feature Leakage
stub のつもりが実処理を書き始める可能性がある。  
**Control:** 実機能はすべて out of scope として明記し、status 更新または no-op に限定する。

## Risk 4. Settings Regression
接続点整理中に B4 の settings 導線を壊す可能性がある。  
**Control:** B4 既存導線は温存し、B5 では hook 名追加までに留める。

## Risk 5. Widget Access Scatter
後続 block が widget を直接触り始めて参照が散る可能性がある。  
**Control:** 最小 accessor / view helper を先に置く。

---

## 18. Definition of Done

MS13-B5 は、以下の状態になった時点で完了とする。

- wx GUI が将来機能を受けるための controller / actions 境界を持っている
- file / analysis / playback の主要操作に対する接続点が整理されている
- worker 受け皿が start / progress / success / error まで stub 化されている
- ステータス更新が一元化されている
- settings の将来 hook 名が置かれている
- 実機能、保存、thread 実装、MS14 以降の内容を流入させていない

---

## 19. Handoff Notes for Implementation

- B5 の主眼は「機能追加」ではなく「接続点整理」である
- `MainFrame` から controller / actions sink への委譲を優先すること
- worker は受け皿だけ作り、実運用しないこと
- ステータス更新は共通入口へ集約すること
- settings 保存を始めないこと
- B6 や MS14 以降の設計を先取りしすぎないこと
- 実装時は block boundary を厳守すること
