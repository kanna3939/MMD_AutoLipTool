# MS14-B6 Implementation Plan

## 1. Document Control

- Document Name: `MS14-B6_Implementation_Plan.md`
- Milestone: `MS14`
- Block: `MS14-B6`
- Title: `統合整理と parity closeout`
- Target Series: `Ver 0.4.x`
- Project: `MMD_AutoLipTool`

---

## 2. Purpose

MS14-B6 では、MS14-B1 から MS14-B5B までで段階的に回復した wx 主系のコア導線を **統合状態として点検し、MS14 全体の出口を閉じる**。

本 block の目的は、新機能追加ではない。  
MS14-B6 は、以下を最小範囲で成立させるための closeout block とする。

- B1〜B5B の結合状態に破綻がないことの確認
- TEXT → WAV → 解析 → VMD保存 の最小実用導線の再確認
- recent / settings save / busy / cancel / timeout warning を含む最小整合確認
- `requirements.txt` / `pyproject.toml` / packaging 定義の最小整合
- README と docs の現在地同期
- MS15 に送る未実装事項・既知制約の整理

B6 は、MS14 全体を「最低限使える wx 主系」として閉じるための block であり、  
波形 / Preview / playback の本格移植や UI polish を行う block ではない。

---

## 3. Fixed Decisions

### 3.1 B6 の役割
- B6 は **統合整理と closeout** に限定する
- 新規の実機能追加 block として扱わない
- B1〜B5B の成果物を結合し、接着不良があれば最小修正する block とする

### 3.2 B6 で許容する修正
B6 で許容する実装修正は、以下に限定する。

- block 間接着不良の最小修正
- README / docs / dependency / package 定義の整合修正
- 軽量統合チェック追加または既存テスト更新
- 実用導線を壊す明白な wiring 不整合の補修

ここでいう「block 間接着不良」には、B1〜B5B の責務境界を崩さない範囲で、

- 入力導線
- 解析導線
- 保存導線
- settings save 導線
- close 導線
- recent 導線

に存在する最小の接続不良修正を含めてよい。

したがって、修正対象は `main_frame.py` 等の代表ファイルに機械的に限定されず、  
**B6 の closeout 達成に不可欠な直接関連ファイルに限って最小範囲で許容**する。  
ただし、新機能追加や責務再設計に拡張してはならない。

### 3.3 B6 で行わないこと
以下は B6 に流入させない。

- 新しい UI 機能追加
- 波形描画の本格実装
- Preview 描画の本格実装
- playback / zoom / pan / shared viewport
- settings system の全面刷新
- migration / 新形式 settings 導入
- Whisper backend の差し替え
- hard cancel / subprocess kill
- MS15 の先取り実装
- UI polish を目的とした見た目改修

### 3.4 closeout の基準
B6 の closeout は、以下 4 系統を揃えることを基準とする。

1. **実行導線整合**
2. **状態遷移整合**
3. **依存 / packaging 整合**
4. **README / docs 整合**

### 3.5 既存仕様の尊重
B6 では、以下の既存 block 決定事項を崩さない。

- B5 の merge-save / coalesced save / pending flush / failure policy
- B5 の VMD 保存失敗は毎回 warning
- B5 の closeEvent failure は non-blocking
- B5B の soft cancel
- B5B の timeout 150 sec 固定
- B5B の timeout warning は 1 回のみ
- B5B の warning は処理中ダイアログ内表示
- B5B の busy 中 close → 中止して終了 → 再起動 の脱出導線
- B5B の worker daemon thread 前提
- B5B の UI 更新 main thread 限定

### 3.6 MS15 への境界維持
B6 の完了後も、以下は未実装のままでよい。

- 波形実描画
- Preview 実描画
- 再生位置同期
- オートスクロール
- 再生時 GUI 滑らか化

これらは MS15 の責務とする。

### 3.7 最小修正で閉じられない場合の扱い
B6 は救済 block ではない。  
したがって、以下のいずれかが発覚した場合は、B6 内で吸収せず **差し戻し / 別 block 化 / 仕様再整理候補** として扱う。

- 最小修正では解決できない構造的競合
- block 境界を跨ぐ責務再設計が必要な不整合
- B5 または B5B の既存固定仕様を変更しないと整合しない問題
- MS15 領域を前倒し実装しないと closeout できない問題
- 複数モジュール横断の大規模再配線が必要な問題

この場合、B6 では「問題を発見し、closeout 対象外として明示する」ことまでを責務とする。

### 3.8 軽量統合チェックの技術的境界
B6 における「軽量統合チェック」は、以下の境界で固定する。

- 実 GUI 自動操作の重量 E2E テストにはしない
- 長時間 Whisper 実処理や重い音声処理を前提にしない
- package / import / entry / hook / state 遷移 / settings flush / callback discard の接着確認に限定する
- widget の細かな見た目・体感・UX は主対象にしない
- 手動確認が妥当な導線は手動確認として明示する

### 3.9 軽量統合チェックにおけるモック / スタブ方針
B6 の自動化対象に含まれる `解析実行成功`、`soft cancel 後結果不採用`、`timeout warning 発火条件` は、  
**実 Whisper 実行や 150 秒実待機で確認しない**。

自動テストでは以下のいずれかの軽量置換を前提としてよい。

- fake worker
- stub callback
- fake timer
- mock pipeline result
- 短縮 timeout / 疑似 timeout 発火

すなわち、自動テストの目的は **接着確認と状態遷移確認** であり、  
Whisper 実処理や長時間待機の実測確認ではない。

---

## 4. Goal

本節の項目群を、**MS14-B6 の canonical completion criteria** とする。  
後続の `13. Acceptance Criteria` および `16. Definition of Done` は、本節を**意味差なしで再掲**する。

1. B1〜B5B の統合状態に明白な破綻がない
2. wx 主系で TEXT → WAV → 解析 → VMD保存 の最小導線が通る
3. recent / settings save / last output dir が B5 契約どおり壊れていない
4. cancel / timeout warning / busy 中 close が B5B 契約どおり壊れていない
5. old job 遅着 callback の UI 反映が防止されている
6. input change / analysis failure に対する invalidate が壊れていない
7. action state 再評価と status 表示が最低限整合している
8. `requirements.txt` と `pyproject.toml` と package 定義の最小整合が取れている
9. wx 主系 package / entry / build 対象の漏れが最低限整理されている
10. README の記述が MS14 現在地と矛盾しない
11. docs の現在地が MS14 block 定義と矛盾しない
12. MS15 へ送る未実装事項が整理されている
13. B6 で新機能追加や MS15 先取りを行っていない

---

## 5. In Scope

MS14-B6 に含めるものは以下とする。

- B1〜B5B の統合確認
- 最小の手動導線確認観点整理
- 軽量統合チェックの追加または更新
- requirements / pyproject / package discovery / entry point の最小整合
- README の現在地同期
- docs の現在地同期
- MS15 handoff note の整理
- 接着不良に対する最小修正
- 最小修正で閉じられない問題の差し戻し判断

---

## 6. Out of Scope

MS14-B6 では以下を行わない。

- 波形 / Preview / playback 実装
- 新しい設定画面の導入
- settings migration
- i18n 本格対応
- 大規模リファクタ
- MVC 再編
- worker 基盤の全面再設計
- Whisper 内部ロジック改変
- UI テーマ再構築
- 再生 UX 改善
- mp3 対応
- 音声のみ入力対応
- same-vowel smoothing 改良
- slope parameter 導入

---

## 7. Expected Functional Boundary

B6 は「新たな機能を足す block」ではなく、**MS14 を壊さず閉じる block** である。

責務分離は以下のとおり。

- **B1:** 実用 UI 骨格拡張
- **B2:** 状態管理と action state 回復
- **B3:** 入力導線 parity 回復
- **B4:** 解析実行 parity 回復
- **B5:** 出力・履歴・settings save parity 回復
- **B5B:** Whisper 解析可用性 hardening と処理中 UI 補強
- **B6:** 統合整理と parity closeout

したがって B6 では、

- B5 の保存仕様を作り替えない
- B5B の cancel / timeout / close 契約を作り替えない
- MS15 の表示系を先取りしない

ことを前提とする。

---

## 8. Current Recognition for B6 Entry

現時点の B6 着手前認識は以下とする。

### 8.1 実装側
- wx 主系メインフレームは存在する
- TEXT / WAV 読込導線は実装済み前提
- 非同期解析 worker は実装済み前提
- 処理中ダイアログ、phase 表示、warning 領域、分析中止導線は実装済み前提
- VMD 保存、recent、settings save は実装済み前提

### 8.2 B6 で再確認すべき closeout 領域
- README の現在地整合
- requirements の GUI 依存整合
- pyproject の dependencies / package include / entry 整合
- wx 主系 package が build / packaging 対象から漏れていないか
- docs の block 境界表記と現実装の齟齬有無

### 8.3 B6 の主眼
B6 の主眼は、**MS14 は終わったか** を block 単位ではなく全体として確認することにある。

---

## 9. Closeout Axes

### 9.1 Workflow Closeout
確認対象:

- TEXT 読込
- WAV 読込
- 解析実行
- VMD 保存
- recent TEXT / WAV
- last output dir
- settings save
- closeEvent final save
- soft cancel
- timeout warning
- busy 中 close

### 9.2 State Closeout
確認対象:

- busy 開始 / busy 終了
- 二重実行防止
- 入力変更後 invalidate
- 解析成功時 `current_timing_plan` 保持
- 解析失敗時 invalidate
- soft cancel 要求後の状態遷移
- 中止後結果不採用
- old job 遅着 callback の無効化
- action state 再評価
- status 表示の最低限整合

### 9.3 Dependency / Packaging Closeout
確認対象:

- `requirements.txt`
- `pyproject.toml`
- setuptools package discovery
- wx 主系 package inclusion
- script / entry point
- fresh 環境想定の import / 起動整合

### 9.4 Documentation Closeout
確認対象:

- `README.md`
- `docs/MS14_Block_Breakdown.md`
- `docs/MS14_onward_Roadmap_Overview.md`
- `docs/MS14-B1_Implementation_Plan.md`
- `docs/MS14-B2_Implementation_Plan.md`
- `docs/MS14-B3_Implementation_Plan.md`
- `docs/MS14-B4_Implementation_Plan.md`
- `docs/MS14-B5_Implementation_Plan.md`
- `docs/MS14-B5B_Implementation_Plan.md`
- 新規 `docs/MS14-B6_Implementation_Plan.md`

ただし、B1〜B4 計画書は B6 時点で全面改訂対象ではなく、  
**B6 の closeout 観点から明白な責務齟齬や現在地矛盾が見つかった場合のみ最小同期対象** とする。  
B5 / B5B / B6 は closeout 直結 block のため、明示的な同期確認対象とする。

---

## 10. Execution Policy

### 10.1 まず確認、次に最小修正
B6 では、先に closeout 観点で現状確認を行い、  
その結果として必要な最小修正だけを行う。

### 10.2 「壊れていない」ことを優先
改善余地があっても、MS14 範囲外なら B6 では吸収しない。  
B6 は理想化よりも **境界維持付き closeout** を優先する。

### 10.3 README と docs の誇張禁止
未実装の waveform / preview / playback を、README で実装済みのように書かない。  
MS14 現在地として、placeholder / 未実装 / MS15 予定の区別を明示する。

### 10.4 dependency の最小一致
GUI 主系が wx であるなら、その前提に沿って依存定義と package 定義を揃える。  
ただし Qt 凍結領域を repo に残すこと自体は妨げない。

### 10.5 block 既存仕様の再変更禁止
B5 / B5B の仕様は closeout のために読み替えない。  
不具合があるなら「仕様変更」ではなく「仕様どおりに戻す最小補修」を優先する。

### 10.6 修正後の再確認を必須化する
B6 では、最小修正を入れたあとに **起動 / workflow / state / dependency / docs** の確認観点を再走査する。  
これにより、「修正のための修正」で別の closeout 領域を壊していないことを確認する。

### 10.7 テスト更新の再判定を必須化する
B6 では、Step 6 の最小修正後に **既存テスト / 追加テストの有効性を再判定** する。  
修正によってテスト前提、hook 条件、callback 期待値、疑似 timer 条件が変わる場合は、  
必要最小限のテスト更新を行ってから再確認へ進む。

---

## 11. Step Breakdown

### Step 1. Confirm B1〜B5B Integrated State

- main frame
- input flow
- analysis flow
- save flow
- settings save flow
- cancel / timeout / close flow

を横断し、明白な接着不良を洗い出す。

#### Exit Condition
- B6 で直すべきものと、MS15 以降へ送るものが分離されている
- 最小修正で閉じられない問題の候補が識別されている

---

### Step 2. Re-check Core Workflow

以下の最小導線を確認する。

1. TEXT 読込
2. WAV 読込
3. 解析実行
4. 解析完了
5. VMD 保存
6. recent / settings 反映
7. 再起動後の基本復元

加えて異常系として以下を確認する。

- 解析失敗
- 分析中止
- timeout warning
- busy 中 close
- 遅着 callback 無効化

#### Exit Condition
- workflow 上の closeout 観点が明確になっている
- 最小手動確認対象と自動化候補が切り分けられている

---

### Step 3. Tighten Lightweight Integration Tests

以下を対象に、必要なら軽量統合テストを追加または更新する。

#### 自動化対象（軽量統合テストで担保するもの）
- entry 起動
- input → analyze → save の最小シナリオ
- busy / action state
- input change による invalidate
- analysis failure 時の invalidate
- settings save flush
- old job 遅着 callback discard
- cancel 要求後の結果不採用
- timeout warning 発火条件の最小確認
- close safety のうち state / callback 保護部分

#### 自動化手法の前提
- `解析実行成功` は mock / stub / fake worker / fake pipeline result により成立させてよい
- `timeout warning 発火条件` は fake timer または短縮 timeout により確認してよい
- 実 Whisper 実行や長時間待機をテスト前提にしない

#### 手動確認対象
- busy 中 close のダイアログ導線
- soft cancel ボタン操作からの体感導線
- timeout warning の実表示位置と phase/warning 領域分離
- README 記載と実アプリの見え方の整合
- fresh 環境想定での run/build 導線の最終確認

ここでは重い E2E を作らず、  
state 遷移と wiring の破綻検知に絞る。

#### Exit Condition
- MS14 の出口を壊しやすい接着点が最小限テストで担保されている
- 自動化対象と手動確認対象の境界が明確である
- 自動化対象に対する mock / stub / fake 方針が明示されている

---

### Step 4. Close Dependency / Packaging Gaps

以下を点検し、必要最小限の整合を取る。

- `requirements.txt`
- `pyproject.toml`
- `tool.setuptools.packages.find`
- script / entry point
- `src/gui_wx/` の packaging 対象性

確認観点:

- wx 主系起動に必要な依存が requirements にあるか
- pyproject 側 dependency と requirements の方針が大きく矛盾していないか
- `gui_wx` が package discovery から漏れていないか
- main entry が現行起動方式と噛み合っているか

#### Exit Condition
- fresh 環境で wx 主系起動を妨げる明白な package 定義漏れが整理されている

---

### Step 5. Sync README and Docs

README では少なくとも以下を現在地へ合わせる。

- GUI 主系
- 実装済み機能
- 未実装 / MS15 予定事項
- 使い方の説明
- build / run 前提

docs では少なくとも以下を一致させる。

- B5B が B5 と B6 の間の補助 block であること
- B6 の責務
- MS14 Done 条件
- MS15 handoff 事項

#### Exit Condition
- README / docs が MS14 現在地と矛盾しない

---

### Step 6. Apply Minimal Glue Fixes

Step 1〜5 の確認結果から、closeout に不可欠な接着不良だけを最小修正する。

修正対象は以下に限定する。

- workflow を壊す wiring 不整合
- state / action / callback の明白な接着不良
- dependency / package discovery / entry の明白な漏れ
- README / docs の現在地齟齬

#### Exit Condition
- 修正内容が B6 の責務境界内に収まっている
- 仕様変更ではなく closeout 修正になっている

---

### Step 7. Re-evaluate Test Validity After Fixes

Step 6 の修正後、Step 3 で追加 / 更新したテストの有効性を再判定する。

再判定対象:

- callback シグネチャ前提
- worker / timer の fake 条件
- state 遷移の期待値
- invalidate / status / action state の期待値
- settings save flush の期待値
- close safety に関する guard 条件

必要があれば、**テストを最小更新してから** 次の再確認へ進む。

#### Exit Condition
- 修正後コードに対してテスト前提が破綻していない
- 必要なテスト更新が最小限で反映されている

---

### Step 8. Re-run Closeout Confirmation After Fixes

Step 6〜7 の後、以下を再確認する。

- 起動が壊れていないか
- TEXT → WAV → 解析 → 保存 の最小導線が壊れていないか
- invalidate / action state / status の整合が壊れていないか
- cancel / timeout / close の安全化が壊れていないか
- settings save / recent / pending flush が壊れていないか
- dependency / packaging / docs の整合が壊れていないか

#### Exit Condition
- 修正が Step 2〜5 の前提を破壊していないことが確認できている
- 修正後のテスト前提も含めて closeout 判定に進める状態である

---

### Step 9. Decide Closeout vs Escalation

再確認の結果、問題が残る場合は以下のいずれかで判断する。

- **B6 で閉じる**  
  最小修正で closeout 条件を満たせる場合
- **差し戻し / 別整理へ送る**  
  構造的競合、責務再設計、MS15 侵食が必要な場合

#### Exit Condition
- 「B6 で閉じた問題」と「B6 範囲外として送る問題」が明示されている

---

### Step 10. Summarize MS15 Handoff Items

B6 完了時点で、MS15 へ送る事項を明確化する。

対象例:

- waveform 実描画
- preview 実描画
- playback
- shared viewport / zoom / pan
- 再生 UX 改善
- 表示同期の再構築

B6 では実装せず、送り事項として閉じる。

#### Exit Condition
- B6 と MS15 の境界が文書上も実装上も明確

---

## 12. Candidate File Touch Areas

B6 で変更対象になり得るファイルは、以下を **主候補** とする。

### コード
- `src/gui_wx/main_frame.py`
- `src/gui_wx/analysis_worker.py`
- `src/main.py`

### 設定・依存・package 定義
- `requirements.txt`
- `pyproject.toml`

### 文書
- `README.md`
- `docs/MS14_Block_Breakdown.md`
- `docs/MS14_onward_Roadmap_Overview.md`
- `docs/MS14-B5_Implementation_Plan.md`
- `docs/MS14-B5B_Implementation_Plan.md`
- `docs/MS14-B6_Implementation_Plan.md`

### 条件付き文書同期対象
- `docs/MS14-B1_Implementation_Plan.md`
- `docs/MS14-B2_Implementation_Plan.md`
- `docs/MS14-B3_Implementation_Plan.md`
- `docs/MS14-B4_Implementation_Plan.md`

上記 B1〜B4 計画書は、Section 9.4 の定義どおり、  
**B6 の closeout 観点から明白な責務齟齬や現在地矛盾が見つかった場合のみ最小同期対象** とする。

### テスト
- 関連する軽量統合テスト

ただし、B6 で block 間接着不良が発見され、その修正に  
B3 / B5 系の直接関連ファイルが不可欠な場合は、  
**責務境界を崩さない範囲で最小限の追加変更を許容**する。

B6 では `core/` の意味変更は原則行わない。  
`pipeline.py` 変更は、接着不良修正に不可避な場合のみ最小限とする。

---

## 13. Acceptance Criteria

本節は、**Section 4 の canonical completion criteria を意味差なしで再掲**する。

1. B1〜B5B の統合状態に明白な破綻がない
2. wx 主系で TEXT → WAV → 解析 → VMD保存 の最小導線が通る
3. recent / settings save / last output dir が B5 契約どおり壊れていない
4. cancel / timeout warning / busy 中 close が B5B 契約どおり壊れていない
5. old job 遅着 callback の UI 反映が防止されている
6. input change / analysis failure に対する invalidate が壊れていない
7. action state 再評価と status 表示が最低限整合している
8. `requirements.txt` と `pyproject.toml` と package 定義の最小整合が取れている
9. wx 主系 package / entry / build 対象の漏れが最低限整理されている
10. README の記述が MS14 現在地と矛盾しない
11. docs の現在地が MS14 block 定義と矛盾しない
12. MS15 へ送る未実装事項が整理されている
13. B6 で新機能追加や MS15 先取りを行っていない

---

## 14. Verification Plan

本節では、**実行テスト** と **レビュー / 監査確認** を分離して定義する。

### 14.1 Runtime / Integration Tests

#### 14.1.1 Startup / Entry
**自動化対象**
- wx 主系で起動できる
- 起動直後に frame が成立する
- package / import 漏れがない

**手動確認対象**
- 実行手順が README 記載と矛盾しない

#### 14.1.2 Core Workflow
**自動化対象**
- TEXT 読込成功
- WAV 読込成功
- 解析実行成功
- VMD 保存成功
- recent / last output dir 反映
- settings save 反映

**自動化手法の前提**
- `解析実行成功` は実 Whisper 実行ではなく、mock / stub / fake worker / fake pipeline result により確認してよい

**手動確認対象**
- 実操作順に沿った最小導線の確認

#### 14.1.3 Analysis Safety
**自動化対象**
- busy 中二重実行防止
- soft cancel 要求後の結果不採用
- old job 遅着 callback discard
- timeout warning 発火条件の最小確認
- close 後 callback 無効化

**自動化手法の前提**
- `timeout warning 発火条件` は fake timer または短縮 timeout で確認してよい
- 150 秒実待機や長時間実解析を前提にしない

**手動確認対象**
- soft cancel ボタン操作の導線
- 中止要求中表示
- 中止後の再実行禁止状態
- busy 中 close の確認ダイアログ導線
- timeout warning の実表示位置と phase/warning 領域分離

#### 14.1.4 State / Invalidate / Status
**自動化対象**
- input change による invalidate
- analysis failure 時の invalidate
- action state 再評価
- status 表示の最低限整合

**手動確認対象**
- invalidate 後の見え方が不自然でない
- status 文言と実状態の乖離がない

#### 14.1.5 Save / Persistence
**自動化対象**
- merge-save が継続して壊れていない
- pending save flush が壊れていない
- closeEvent final save が非ブロッキング
- VMD 保存失敗 warning が毎回出る
- settings save failure policy が壊れていない

**手動確認対象**
- recent / 保存先再利用 / 終了時保存の体感導線

### 14.2 Review / Audit Checks

#### 14.2.1 Docs / Dependency Review
**レビュー対象**
- `gui_wx` package が package discovery から漏れていない
- requirements と pyproject の明白な依存矛盾がない
- README の GUI 記述が現状一致
- README の「できること」に未実装項目が混入していない
- docs の責務境界記述が現状と矛盾しない

#### 14.2.2 Scope Guard Review
**レビュー対象**
- settings migration が流入していない
- waveform / preview / playback 実装が流入していない
- MS15 内容の前倒しが起きていない
- B5 / B5B の固定仕様変更が紛れ込んでいない
- 大規模リファクタや責務再編が流入していない

---

## 15. Risks and Control

### Risk 1. B6 Slipping into MS15
closeout の名目で waveform / preview / playback を触り始める危険がある。  
**Control:** 未実装の明記と handoff 整理に留める。

### Risk 2. README Overclaim
README が旧 Qt 前提や将来機能を実装済みのように記載し続ける危険がある。  
**Control:** MS14 現在地基準へ明示的に同期する。

### Risk 3. Dependency Drift
requirements と pyproject と package discovery が分裂し、fresh 環境で起動不能になる危険がある。  
**Control:** B6 で GUI 主系起動前提の最小一致を取る。

### Risk 4. Reopening B5 / B5B Specs
closeout 中に B5 / B5B の仕様自体を再議論し始める危険がある。  
**Control:** 既存決定事項を固定し、必要なら実装補修に留める。

### Risk 5. Lightweight Check Expanding into Heavy GUI Testing
軽量統合チェックの名目で重い GUI 自動操作や長時間実処理テストへ拡張する危険がある。  
**Control:** 軽量統合チェックの境界を以下で固定する。
- 実 GUI 自動操作の重量 E2E にしない
- 長時間 Whisper 実処理を前提にしない
- 接着確認に必要な import / entry / state / hook / save flush / callback discard に限定する
- 見た目確認や体感導線は手動確認へ分離する

### Risk 6. Minimal Fix Breaking Other Closeout Areas
接着修正が別の workflow / state / docs 領域を壊す危険がある。  
**Control:** Step 8 で修正後再確認を必須化する。

### Risk 7. Structural Conflict Being Silently Absorbed
B6 では閉じられない構造的競合を、そのまま場当たり補修で吸収してしまう危険がある。  
**Control:** Step 9 で closeout と差し戻しの分岐判断を明示する。

### Risk 8. Fixes Invalidating Tests Without Re-evaluation
最小修正により、先に追加 / 更新した軽量統合テストの前提が壊れる危険がある。  
**Control:** Step 7 でテスト有効性の再判定と必要最小限の再更新を必須化する。

---

## 16. Definition of Done

本節は、**Section 4 の canonical completion criteria を意味差なしで再掲**する。

1. B1〜B5B の統合状態に明白な破綻がない
2. wx 主系で TEXT → WAV → 解析 → VMD保存 の最小導線が通る
3. recent / settings save / last output dir が B5 契約どおり壊れていない
4. cancel / timeout warning / busy 中 close が B5B 契約どおり壊れていない
5. old job 遅着 callback の UI 反映が防止されている
6. input change / analysis failure に対する invalidate が壊れていない
7. action state 再評価と status 表示が最低限整合している
8. `requirements.txt` と `pyproject.toml` と package 定義の最小整合が取れている
9. wx 主系 package / entry / build 対象の漏れが最低限整理されている
10. README の記述が MS14 現在地と矛盾しない
11. docs の現在地が MS14 block 定義と矛盾しない
12. MS15 へ送る未実装事項が整理されている
13. B6 で新機能追加や MS15 先取りを行っていない

---

## 17. Handoff Notes for Implementation

- B6 は closeout block であり、新規機能追加 block ではない
- まず統合確認を行い、接着不良だけを最小修正すること
- README / docs の誇張を避け、MS14 現在地へ同期すること
- requirements / pyproject / package discovery の最小整合を取ること
- `gui_wx` package 漏れや entry 不整合を放置しないこと
- B5 の保存仕様、B5B の cancel / timeout / close 仕様は変更しないこと
- waveform / Preview / playback は MS15 へ送ること
- 改善余地があっても MS14 範囲外なら handoff に残すこと
- 最小修正のあとに再確認ループを必ず通すこと
- 構造的競合が見つかった場合は B6 で救済せず、差し戻し判断を明示すること
- 自動化対象の `解析実行成功` や `timeout warning` は mock / stub / fake 条件で確認すること
- 修正後にテスト有効性を再判定し、必要なら最小限のテスト再更新を行うこと

---

## 18. Status Note

- **2026-04-17**: B6 plan redrafted.  
  B5B 完了後の closeout block として、workflow / state / dependency / packaging / README / docs の統合整理に限定して再改訂。  
  完了条件の正本を Section 4 に固定し、修正後再確認ループ、テスト有効性再判定、レビュー / テスト分離、差し戻し条件、軽量統合チェック境界、mock / stub 前提を明示した。
