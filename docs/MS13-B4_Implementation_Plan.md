# MS13-B4 Implementation Plan

## 1. Document Control

- Document Name: `MS13-B4_Implementation_Plan.md`
- Milestone: `MS13`
- Block: `MS13-B4`
- Title: `settings load 接続と起動時適用`
- Target Series: `Ver 0.4.x`
- Project: `MMD_AutoLipTool`

---

## 2. Purpose

MS13-B4 では、wxPython 主系 GUI に対して、既存設定ファイルの読み込みを接続し、起動時に B3 までで存在している wx 側 UI にのみ設定を適用できる状態を作る。

本 block の目的は、**Ver0.3 系で使っていた設定資産を大きく壊さずに、Ver0.4 系 wx GUI の起動時初期化へ接続すること**である。

---

## 3. Fixed Decisions

本 block では、以下の前提を固定とする。

### 3.1 Settings Source
- 現行 0.3 系と同じ設定ファイルをそのまま読む
- 既存 ini / key 構造は可能な限り維持する

### 3.2 Apply Scope
- 起動時適用の対象は、**B3 までに実在する wx 側 UI 部品に対応する設定のみ**とする
- 未実装領域、未配置領域、将来用 UI への仮適用は行わない

### 3.3 Apply Timing
- Frame および必要な control の生成完了後に、一括で settings を適用する

### 3.4 Failure Handling
- 設定ファイルが欠損・破損していても、既定値で継続する
- 必要に応じて status / log にのみ記録し、起動停止や警告ダイアログは行わない

### 3.5 Save Behavior
- B4 では保存処理を含めない
- load / apply のみを対象とする

### 3.6 Unused Keys
- 現時点で未使用の既存 key は、設定モデル上では保持してよい
- ただし、wx 側へ未実装のまま適用はしない
- 新キーへの積極変換は行わない

---

## 4. Goal

MS13-B4 の完了条件は、以下を満たすこととする。

1. wx 主系アプリが起動する
2. 起動過程で既存設定ファイルを読み込める
3. 読み込んだ設定のうち、B3 までに存在する wx UI に対応する値だけを適用できる
4. 設定ファイルがなくても既定値で起動継続できる
5. 設定ファイルが破損していてもクラッシュせず既定値で起動継続できる
6. 保存や migration を混入させず、B4 の責務を load / apply に限定できている

---

## 5. In Scope

MS13-B4 に含めるものは以下とする。

- 既存設定ファイルの読み込み接続
- wx 主系起動シーケンスへの settings load 組み込み
- B3 までに存在する wx UI への起動時設定適用
- 欠損・破損時の既定値フォールバック
- 将来 block で拡張しやすい最小の settings apply 導線整理

---

## 6. Out of Scope

MS13-B4 では以下を行わない。

- 設定保存
- 設定 migration
- 新しい設定ファイル形式の導入
- Qt 側 GUI への追加対応
- B3 以降で登場する UI への先行適用
- 実ファイル選択、再生、解析、保存などの本実装
- worker / thread 実運用
- MS14 以降の parity 調整

---

## 7. Expected Functional Boundary

B4 は「設定の読み込みと起動時初期反映」だけを担当する。

責務の境界は以下のように切る。

- B1: wx 主系入口
- B2: 最小 frame 骨格
- B3: メニュー / 基本操作列 / ステータス最小配置
- **B4: settings load / apply**
- B5: 将来拡張の接続点整理
- B6: MS13 統合整理

したがって、B4 では UI の新規機能追加よりも、**既に存在する wx UI を settings で初期化できる状態を作ること**を優先する。

---

## 8. Design Policy

## 8.1 Reuse First
既存 repo に settings 読み込み機構がある場合は、可能な限り再利用する。  
ただし、wx 側適用に必要な最小限の橋渡し層は追加してよい。

## 8.2 Apply Only to Existing wx UI
設定値は、「B3 までで既に存在している部品」にだけ適用する。  
存在しない control に対する適用コード、将来のための仮配線、Qt 資産への依存は増やさない。

## 8.3 Default Safe Startup
設定が読めなくても起動できることを優先する。  
設定は利便性の層であり、起動必須要件にはしない。

## 8.4 Keep Old Key Shape
B4 では key の整理や再設計はしない。  
既存 key 構造を維持したまま、wx 側に必要な範囲だけ読む。

## 8.5 Separate Read and Apply
「読む処理」と「UI に適用する処理」は概念上分ける。  
これにより、将来 B5 / MS14 で適用対象が増えても拡張しやすくする。

---

## 9. Assumed Apply Targets

B4 で実際に適用対象とする候補は、**B3 完了時点で存在しているものだけ**とする。  
実際の repo 構成に合わせて、以下から存在するもののみ採用する。

### 9.1 Window-Level Settings
- window size
- window position
- 必要なら maximize 状態

### 9.2 Basic UI State
- B3 までに配置済みのラベル・初期表示文言
- B3 までに配置済みの操作列で、設定で初期値を持つもの
- B3 までに可視化済みの最小 UI 状態

### 9.3 Non-Applicable Yet
以下は B4 時点では原則適用しない。

- まだ存在しない preview 関連設定
- まだ存在しない waveform 関連設定
- 再生機能の内部状態
- ファイルダイアログ履歴の保存反映
- 後続 block で導入される詳細設定

---

## 10. Implementation Strategy

## 10.1 Reading Phase
- アプリ起動時に既存設定ファイルを読み込む
- 設定ファイルが存在しない場合は、空または既定設定として扱う
- 読み込みに失敗した場合も例外で停止させず、既定値へフォールバックする

## 10.2 Normalization Phase
- 読み込んだ設定を、wx 側で扱いやすい最小構造へまとめる
- ただし、この段階で key 名を大きく変更しない
- 必要最小限の型変換や存在確認だけ行う

## 10.3 Apply Phase
- main frame と B3 までの UI 構築後に apply を呼ぶ
- apply は UI の存在確認を行い、存在する部品にだけ反映する
- 未対応 key は保持してよいが、未適用のままとする

## 10.4 Error Handling Phase
- 欠損: 既定値で継続
- 破損: 既定値で継続
- 不正値: 個別に無視し、該当箇所だけ既定値に倒す
- status / log が使える場合のみ、簡潔に記録する

---

## 11. Recommended Internal Structure

実ファイル名は repo の現状に合わせて決めるが、概念上は以下の分離を推奨する。

### 11.1 Settings Reader
責務:
- 既存設定ファイルを読む
- 例外を吸収し、既定値に倒す
- 既存 key を保持した最小設定データを返す

### 11.2 Settings Apply Helper
責務:
- wx frame / panel / control に対して設定を反映する
- 反映対象の存在確認を行う
- 未配置 control は無視する

### 11.3 Startup Integration Point
責務:
- app 起動後、frame 構築後の適切なタイミングで load → apply を呼ぶ
- B4 の導線を 1 か所にまとめる

---

## 12. Step Breakdown

## Step 1. Existing Settings Path / Reader Confirmation
- 既存 repo の設定読込経路を確認する
- 既存設定形式を変えずに流用できるか確認する
- 既存実装が再利用可能ならそのまま利用する
- 再利用困難なら wx 用の最小 adapter を追加する

### Exit Condition
- 既存設定ファイルを読める最小経路が定まっている

---

## Step 2. Define Minimal Default Values
- B3 までの wx UI に必要な既定値を定義する
- 既定値は「起動可能であること」を優先する
- 保存前提の完全性ではなく、起動時適用の安全性を優先する

### Exit Condition
- 設定欠損時でもアプリが起動継続できる

---

## Step 3. Add Load Hook to wx Startup Flow
- wx 主系起動フローに settings load を接続する
- 読み込みの責務と UI 構築責務を混在させすぎない
- Frame 生成後に apply を呼べる位置を確定する

### Exit Condition
- 起動時に settings load が 1 回だけ呼ばれる

---

## Step 4. Implement Apply to Existing wx UI
- B3 までに存在する UI に対してのみ apply を実装する
- window geometry が存在するなら最優先で反映する
- そのほかの部品は、B3 の実在範囲に合わせて限定的に反映する

### Exit Condition
- 少なくとも window-level settings と、存在する最小 UI 状態が反映される

---

## Step 5. Failure Safe Handling
- 設定ファイル欠損ケースを確認する
- 破損ケースを確認する
- 不正値ケースを確認する
- いずれもクラッシュしないことを確認する

### Exit Condition
- 欠損 / 破損 / 不正値のいずれでも既定値起動できる

---

## Step 6. Boundary Cleanup
- save 処理が混入していないか確認する
- migration が混入していないか確認する
- B5 以降向けの過剰設計が入っていないか確認する
- apply 対象が B3 までに限定されているか確認する

### Exit Condition
- B4 の責務が load / apply に限定されている

---

## 13. Candidate File Touch Areas

repo 実態に応じて調整するが、変更対象は概ね以下の範囲に留める。

- `src/main.py`
  - wx 主系起動導線側の settings load 呼び出し接続
- `src/gui_wx/`
  - frame 構築後の apply 接続
  - settings apply helper の追加または接続
- 既存 settings module
  - 可能なら再利用
  - 必要なら最小 adapter のみ追加

B4 では、設定保存用の新規大規模モジュール追加は避ける。

---

## 14. Acceptance Criteria

以下をすべて満たしたら B4 完了とみなす。

1. 既存設定ファイルを読み込める
2. wx 主系起動時に settings load が接続されている
3. B3 までに存在する wx UI にのみ設定が適用される
4. 設定ファイルがない場合でも既定値で起動する
5. 設定ファイルが破損していてもクラッシュしない
6. 保存処理を追加していない
7. migration を追加していない
8. B5 / MS14 以降の機能を先行流入させていない

---

## 15. Test Plan

## 15.1 Startup with Valid Settings
- 既存設定ファイルが正常な状態で起動
- 想定した window size / position が反映されるか確認
- B3 までの実在 UI に対応する設定だけが反映されるか確認

## 15.2 Startup without Settings File
- 設定ファイルを一時的に欠損させて起動
- クラッシュせず既定値で起動するか確認

## 15.3 Startup with Corrupted Settings File
- ini 破損、欠落、型不正などを与えて起動
- クラッシュせず継続するか確認
- 問題箇所だけ既定値へフォールバックできるか確認

## 15.4 Non-Existing UI Apply Guard
- B3 までに存在しない control に対する apply が走らないことを確認
- 将来機能向け設定があっても起動失敗しないことを確認

## 15.5 No Save Side Effect
- 起動時に設定ファイルを書き換えていないことを確認
- 欠損キー補完保存や migration 保存が混入していないことを確認

---

## 16. Risks and Control

## Risk 1. Existing Settings Format Dependency
既存設定実装の依存が強い場合、wx 側接続で破綻する可能性がある。  
**Control:** 既存 reader 再利用を優先しつつ、最小 adapter のみに留める。

## Risk 2. Apply Scope Expansion
「ついでに他の設定も反映する」ことで B4 が肥大化する可能性がある。  
**Control:** B3 までの実在 UI のみ適用対象とする。

## Risk 3. Save Logic Leakage
load のついでに保存補完を入れたくなる可能性がある。  
**Control:** 保存は明示的に out of scope とし、レビュー観点にも入れる。

## Risk 4. UI Construction Order Issues
UI 構築前に適用して null / missing が起きる可能性がある。  
**Control:** frame / control 生成後に一括 apply とする。

---

## 17. Definition of Done

MS13-B4 は、以下の状態になった時点で完了とする。

- wx 主系で settings load が起動フローに組み込まれている
- B3 までの wx UI に対して起動時設定が反映される
- 欠損 / 破損 settings でも既定値で起動継続できる
- 保存や migration を含まず、責務が明確に B4 に閉じている

---

## 18. Handoff Notes for Implementation

- 既存設定 reader が使えるなら極力再利用すること
- B4 では settings の再設計を始めないこと
- apply 対象は「B3 までに実在する wx UI」に限定すること
- save / migration / parity 回復を混入させないこと
- 実装時は block boundary を厳守すること
