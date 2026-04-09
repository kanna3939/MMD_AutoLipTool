# MS13-B6 Implementation Plan

## 1. Document Control

- Document Name: `MS13-B6_Implementation_Plan.md`
- Milestone: `MS13`
- Block: `MS13-B6`
- Title: `MS13 統合整理と完了確認`
- Target Series: `Ver 0.4.x`
- Project: `MMD_AutoLipTool`

---

## 2. Purpose

MS13-B6 では、MS13-B1 から MS13-B5 までで構築された wxPython 最小基盤を統合し、**起動確認・構成整合確認・最小限の接着修正・完了条件の検証** を行う。

本 block の目的は、新しい機能を追加することではない。  
**MS13 の範囲内で積み上げた成果を 1 つの最小動作基盤としてまとめ、Ver0.4 系 wx 主系移行の最初の到達点として閉じること** が目的である。

---

## 3. Fixed Decisions

本 block では、以下の前提を固定とする。

### 3.1 B6 の主目的
- MS13-B1〜B5 の成果を統合する
- 起動確認と構成整理を行う
- MS13 完了条件を満たしているかを確認する
- 新規機能追加は行わない

### 3.2 B6 で許容する修正の強さ
- 統合作業で発見した不整合に対する、**最小限の接着修正のみ** 許可する
- 命名整理、配置整理、小規模リファクタを主目的として行わない
- B6 を「救済 block」にしない

### 3.3 settings の確認範囲
- B4 で導入した settings load / apply が、MS13 全体統合後も壊れていないことだけ確認する
- 保存、migration、将来 hook の具体化には踏み込まない

### 3.4 disabled 項目の扱い
- 未実装項目は disabled のまま維持する
- 表示状態と構成整合のみ確認する
- B6 を理由に仮有効化しない

### 3.5 B6 の完了確認方法
- 起動確認
- 最小手動確認
- 必要最小限の既存テスト確認
- 必要なら MS13 用の軽い統合チェックテストを追加してよい

### 3.6 文書整備範囲
- 実装結果要約を残す
- MS13 完了条件の達成状況を整理する
- 未実装事項と後続 block への引継ぎ事項を整理する
- MS14 詳細設計までは行わない

### 3.7 外観調整の扱い
- 明らかな崩れや不整合だけ最小限修正してよい
- polish を目的とした見た目改善は行わない

---

## 4. Goal

MS13-B6 の完了条件は、以下を満たすこととする。

1. wx 主系アプリが `src/main.py` から起動できる
2. B1〜B5 の成果が競合せず共存している
3. B3 までの最小 UI 構成が崩れていない
4. B4 の settings load / apply が統合後も機能している
5. B5 の controller / actions / worker stub / status 導線が統合後も破綻していない
6. disabled 項目が方針どおり維持されている
7. MS13 の範囲を超える機能が流入していない
8. MS13 完了条件と後続 block への引継ぎ事項が明文化されている

---

## 5. In Scope

MS13-B6 に含めるものは以下とする。

- B1〜B5 の統合確認
- 起動経路の最終確認
- 最小 UI 構成の整合確認
- settings load / apply の回帰確認
- controller / actions / worker stub / status 導線の統合確認
- 明らかな接着不良に対する最小修正
- 必要最小限の軽量統合チェック
- MS13 完了条件の明文化
- 未実装事項と後続 block 向け引継ぎ整理

---

## 6. Out of Scope

MS13-B6 では以下を行わない。

- 新規機能追加
- file dialog 本実装
- 実ファイル読込 / 実保存
- 解析処理本体
- 再生処理本体
- waveform / preview 本実装
- settings 保存
- settings migration
- worker / thread 実運用
- parity 回復作業
- 再生 UX 改善
- mp3 対応
- 音声のみ入力対応
- MS14 以降の内容
- 見た目 polish を目的とした改善
- 大規模リファクタ

---

## 7. Expected Functional Boundary

B6 は **MS13 の出口確認 block** である。  
ここでやるべきことは、「新しいものを足す」ことではなく、「ここまで作ったものが MS13 として閉じているかを確認する」ことである。

各 block の責務は以下のとおり。

- B1: wx 主系入口作成
- B2: メインフレーム最小骨格作成
- B3: メニュー / 基本操作列 / ステータス最小配置
- B4: settings load 接続と起動時適用
- B5: 将来拡張の接続点整理
- **B6: 統合整理と完了確認**

したがって B6 では、B1〜B5 の責務不足を埋めるための新規設計を始めない。  
あくまで **統合・確認・最小接着修正** に限定する。

---

## 8. Integration Checklist

B6 で重点的に統合確認する対象は以下とする。

### 8.1 Entry / Boot Path
- `src/main.py` から wx 主系へ入れるか
- 起動経路に不要な Qt 依存が残っていないか
- 最低限のアプリ生成と frame 表示が成立するか

### 8.2 B2 / B3 UI Structure
- 上部操作域 / 中央主領域 / 下部ステータス域の 3 分割が維持されているか
- メニューが最小構成で表示されるか
- 基本操作列が崩れていないか
- ステータス表示域が維持されているか
- 未実装項目が disabled のまま維持されているか

### 8.3 B4 Settings
- 既存設定ファイルの読み込み導線が残っているか
- 起動時 apply が走るか
- 設定欠損 / 破損時に既定値で継続できるか
- B6 統合作業によって壊れていないか

### 8.4 B5 Future Hooks
- `MainFrame` から controller / actions 受け口へ委譲できるか
- status 更新共通入口が残っているか
- worker 用 stub 受け口が残っているか
- 設定将来 hook 名が壊れていないか

---

## 9. Design Policy

## 9.1 Complete MS13, Do Not Expand It
B6 は MS13 を閉じるための block であり、MS14 を先取りする block ではない。

## 9.2 Minimal Glue Fix Only
統合作業で不整合が見つかった場合、許容されるのは最小接着修正のみとする。  
構造改善の名目で改修を広げない。

## 9.3 Preserve Disabled Policy
未実装項目は disabled のままとする。  
「せっかくだから動かす」は禁止する。

## 9.4 Preserve Settings Boundary
B4 の settings load / apply が動くことを確認する。  
保存や migration の準備に進まない。

## 9.5 Integration Test Over Feature Test
B6 では個別機能テストではなく、**MS13 全体として破綻していないか** を見る。

## 9.6 Leave Clean Handoff
MS13 完了時点で、何が完了し、何が未実装で、次にどこへ進むかが分かる状態を残す。

---

## 10. Step Breakdown

## Step 1. Confirm B1-B5 Integration Baseline
- B1〜B5 の成果が repo 上でどう構成されているか確認する
- 起動入口、frame、UI、settings、controller 導線の位置関係を把握する
- 競合箇所や重複箇所がないか確認する

### Exit Condition
- MS13 全体の統合対象が把握できている

---

## Step 2. Boot Smoke Check
- `src/main.py` から wx 主系が起動するか確認する
- 起動直後に例外で落ちないか確認する
- frame が表示されるか確認する

### Exit Condition
- wx 主系アプリの最小起動が成立する

---

## Step 3. UI Structure Consistency Check
- B2 / B3 で作成した最小 UI 構成が維持されているか確認する
- メニュー、操作列、ステータス域が存在するか確認する
- disabled 項目が想定どおり disabled のままか確認する
- 明らかなレイアウト崩れのみ最小修正してよい

### Exit Condition
- 最小 UI 構成が MS13 として整っている

---

## Step 4. Settings Regression Check
- B4 の settings load / apply が統合後も機能しているか確認する
- 正常設定、設定欠損、設定破損のケースで起動継続できるか確認する
- B6 の修正で settings 境界を壊していないか確認する

### Exit Condition
- B4 の導線が回帰していない

---

## Step 5. Future Hook Integration Check
- B5 の controller / actions 受け口が残っているか確認する
- UI イベント委譲導線が破綻していないか確認する
- worker stub が存在しているか確認する
- status 共通入口が残っているか確認する

### Exit Condition
- B5 で整理した接続点が統合後も使える状態にある

---

## Step 6. Minimal Glue Fix
- 上記確認で見つかった接着不良を最小限だけ修正する
- 命名整理や構造整理を目的化しない
- 修正は「MS13 として起動・整合するために必要な最小量」に限定する

### Exit Condition
- B1〜B5 が最小構成で共存できる

---

## Step 7. Add Light Integration Check
- 必要最小限の既存テストを確認する
- 必要なら MS13 用の軽い統合チェックを追加してよい
- GUI 全面自動化や将来回帰テスト雛形までは作らない

### Exit Condition
- MS13 統合状態を確認できる最低限のチェックが存在する

---

## Step 8. Completion Summary and Handoff
- MS13 の完了条件達成状況を整理する
- 現時点で intentionally 未実装のものを明記する
- MS14 以降へ渡す引継ぎ事項を整理する

### Exit Condition
- MS13 の完了状態と未実装範囲が明文化されている

---

## 11. Candidate File Touch Areas

repo 実態に応じて調整してよいが、変更対象は以下の範囲に留める。

- `src/main.py`
  - 起動導線の最終整合確認に必要な最小修正のみ
- `src/gui_wx/` 配下
  - `MainFrame`
  - UI 構成
  - status 表示
  - controller / actions 接続点
  - worker stub / settings hook 周辺
- 必要最小限のテストファイル
- MS13 完了整理用ドキュメント

B6 では新規大規模モジュール追加は原則行わない。

---

## 12. Acceptance Criteria

以下をすべて満たしたら B6 完了とみなす。

1. `src/main.py` から wx 主系アプリが起動する
2. B2 / B3 の最小 UI 構成が維持されている
3. 未実装項目が disabled のまま維持されている
4. B4 の settings load / apply が統合後も機能している
5. B5 の controller / actions / worker stub / status 導線が統合後も機能的に残っている
6. 必要最小限の統合確認が行われている
7. 保存、migration、実 worker、実再生、実解析などが流入していない
8. MS13 完了条件達成状況が明文化されている
9. 未実装事項と後続 block への引継ぎが整理されている

---

## 13. Test Plan

## 13.1 Boot Smoke Test
- `src/main.py` から起動する
- 例外で即落ちしない
- frame が表示される

## 13.2 UI Structure Check
- 最小メニュー表示確認
- 基本操作列表示確認
- ステータス域表示確認
- disabled 項目の表示状態確認

## 13.3 Settings Regression Check
- 正常な設定ファイルで起動
- 設定ファイル欠損で起動
- 設定ファイル破損で起動継続
- 起動時 apply が走ることを確認

## 13.4 Future Hook Wiring Check
- UI イベントが controller / actions 受け口へ流れることを確認
- status 更新共通入口が使われることを確認
- worker stub 受け口が存在することを確認

## 13.5 Light Integration Check
- 必要最小限の既存テストを確認
- 必要なら MS13 用軽量統合チェックテストを追加
- ただし GUI 全面自動テスト化までは行わない

## 13.6 Scope Guard Check
- 保存が入っていない
- migration が入っていない
- 実 file 操作 / 実解析 / 実再生が入っていない
- B6 が追加実装 block になっていない

---

## 14. Risks and Control

## Risk 1. B6 Becoming a Catch-All Fix Block
統合中に見つかった不満点を次々直し始めると、B6 が肥大化する。  
**Control:** 最小接着修正のみ許可する。

## Risk 2. Silent Regression in Settings
UI 整理中に B4 の settings 導線を壊す可能性がある。  
**Control:** B4 は回帰確認対象として明示する。

## Risk 3. Disabled Policy Breakage
接続確認のために未実装項目を有効化してしまう可能性がある。  
**Control:** disabled 項目は維持を原則とする。

## Risk 4. Premature MS14 Leakage
次段の parity や UX 改善を B6 で先取りしてしまう可能性がある。  
**Control:** B6 は MS13 完了確認に限定する。

## Risk 5. Excessive Test Investment
統合確認を理由に重い GUI テスト整備へ進む可能性がある。  
**Control:** 軽量統合チェックまでに留める。

---

## 15. Definition of Done

MS13-B6 は、以下の状態になった時点で完了とする。

- wx 主系が最小構成で起動する
- B1〜B5 の成果が統合され、相互に破綻していない
- settings load / apply が回帰していない
- 将来拡張用接続点が保持されている
- 未実装項目は disabled のまま管理されている
- MS13 の完了条件が確認されている
- 未実装事項と次 block への引継ぎが整理されている
- MS13 の範囲外は流入していない

---

## 16. Handoff Notes for Implementation

- B6 は「仕上げ」ではあるが、「追加実装 block」ではない
- 最小接着修正だけを許可し、それ以上は後続へ送ること
- B4 の settings 境界を壊さないこと
- B5 の接続点整理を壊さないこと
- disabled 項目を勝手に有効化しないこと
- 必要なら軽量統合チェックを追加してよいが、重い回帰基盤づくりには進まないこと
- 完了時には、MS13 の達成範囲と未実装事項を明文化すること
