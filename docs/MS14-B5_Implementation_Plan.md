# MS14-B5 Implementation Plan

## 1. Document Control

- Document Name: `MS14-B5_Implementation_Plan.md`
- Milestone: `MS14`
- Block: `MS14-B5`
- Title: `出力・履歴・settings save parity 回復`
- Target Series: `Ver 0.4.x`
- Project: `MMD_AutoLipTool`

---

## 2. Purpose

MS14-B5 では、MS14-B1 で整えた実用 UI 骨格、MS14-B2 で整理した state / action state 契約、MS14-B3 で回復した入力導線、MS14-B4 で回復した解析実行導線の上に、**wx 側での VMD 保存・recent 履歴運用・settings save を実用レベルで成立させる**。

本 block の目的は、以下を wx 主系で閉じることにある。

- VMD 保存ダイアログからの保存実行
- overwrite confirm
- 保存成功 / 失敗に応じた state / status 整合
- recent TEXT / WAV の実用運用
- invalid recent の除去
- `last_vmd_output_dir` の運用
- 実用設定の save / close 時保存
- 既存 ini の unknown key / unknown section を壊さない merge-save

本 block は、**MS14 の「使える wx 主系」としての出口を成立させる block** である。  
ただし、settings dialog、新形式 migration、MS15 以降の波形 / Preview / playback / UX 再構築には踏み込まない。

---

## 3. Fixed Decisions

### 3.1 settings save の保存対象

B5 で save 対象に含めるのは、少なくとも以下とする。

- `recent_text_files`
- `recent_wav_files`
- `last_vmd_output_dir`
- `last_text_dialog_dir`
- `last_wav_dialog_dir`
- `morph_upper_limit`
- `closing_hold_frames`
- `closing_softness_frames`

必要に応じて、B2 / B3 / B4 で既に実用状態として扱っている**同種の最小追加項目**は含めてよい。  
ただし、MS15 以降で意味が変わる UI 状態や未導入機能の設定は保存対象へ広げない。

### 3.2 save dispatch の基本方式

settings save は、**イベントごとの即時実行を無制限に許可せず、coalesced save として扱う**。

- 同一タイミングで複数の save トリガーが発生した場合、保存要求は 1 回にまとめてよい
- 短時間に連続発火する変更は、**single-shot の遅延保存または同等の debounce / batching** にまとめてよい
- 保存対象の state は、保存直前の最新値を採用する

この方針は、I/O の多重実行と save failure notification のスパム化を防ぐための前提である。

### 3.3 settings save の実行タイミング

- 一部は **成功イベントごとに coalesced save を要求** する
- さらに **closeEvent 時にも最終保存** を行う

coalesced save 要求の対象は少なくとも以下とする。

- recent TEXT / WAV 更新後
- invalid recent を除去して recent リストが変化した後
- VMD 保存成功後
- TEXT 読込成功により `last_text_dialog_dir` が更新された後
- WAV 読込成功により `last_wav_dialog_dir` が更新された後
- main frame 上の以下のパラメータ変更確定後
  - `morph_upper_limit`
  - `closing_hold_frames`
  - `closing_softness_frames`

ここでいう「パラメータ変更確定後」は、**main frame 上の入力コントロールについて、値が確定したとみなせる時点** を指す。  
値変更イベントの全発火ごとに即保存することは前提としない。

### 3.4 busy 中の save 要求

B5 で参照する `busy` 判定の正本は、**B2 で定義され B4 で実運用へ載せた state holder 上の `is_busy`（または同等の正式 busy state）** とする。

- `is_busy == true` の間は settings save をその場で書き込まなくてよい
- その場合、save 要求は **破棄せず pending / dirty として保持** し、最初の安全な save 機会で flush する
- 最初の安全な save 機会とは、少なくとも
  - `is_busy` が false へ戻った直後の coalesced save
  - または closeEvent 時最終保存
  のいずれかである

### 3.5 unknown key / unknown section の保持

- ini 保存は **merge-save** とする
- wx 側が使う既知 key だけを書き換え、その他の key / section は可能な限り保持する
- 既知 key だけで ini 全体を再構成しない

### 3.6 merge-save の前提データ

merge-save を成立させるため、settings save 実装は **unknown key / unknown section を含む merge base** を参照できなければならない。

許容する実現方法は以下のいずれかとする。

1. 起動時 load 時に、raw ini 構造またはそれと等価な merge base をメモリ保持する  
2. save 直前に現在の ini を再読込し、そこを merge base にする

どちらを採るかは実装判断に委ねるが、**unknown 保持を write 側だけで仮定しない**ことを必須要件とする。

### 3.7 recent menu の不正パス

- invalid recent は、**メニュー再構築時または実行時に除去**してよい
- 壊れた履歴を残し続けない
- invalid recent の除去によって recent リストが変化した場合、それは **recent 更新** とみなし save 対象に含める
- ただし、起動直後から過剰な warning を連発しない

### 3.8 recent 実行時の warning 境界

recent 実行時の warning 責務は以下のように切り分ける。

- **B5 側**は、recent エントリの明白な invalidity を pre-check して、必要なら prune する
- この pre-check で invalid と確定した場合、B5 側で最小 warning を出してよい
- この場合、**B3 の通常読込フローは呼ばない**
- pre-check を通過した場合のみ、B3 の通常読込フローへ委譲し、その先の読込失敗 warning は B3 側責務とする

これにより、同一の recent 実行失敗で warning を二重表示しない。

### 3.9 VMD 保存時の overwrite confirm

- B5 に含める
- 既存ファイルへ保存する場合は overwrite confirm を出す
- 確認後に保存を続行または中止する

### 3.10 VMD 保存成功時の更新範囲

- `last_vmd_output_dir` を更新する
- 保存成功 status を更新する
- 必要最小限の保存成功情報を UI に反映してよい
- TEXT / WAV recent とは別管理とし、VMD recent は新設しない

### 3.11 settings save 失敗時の扱い

- **自動的に走る settings save** については、**通常動作中の初回失敗時だけ warning**
- 以後の連続失敗は status / log 相当の最小通知に留める
- 毎回 modal warning を出し続けない

### 3.12 first failure 状態の解除条件

settings save failure policy における「初回失敗済み」状態は、**その後に settings save が 1 回でも成功した時点で解除してよい**。

したがって、

- failure → failure → failure  
  では最初の 1 回だけ warning
- failure → success → failure  
  では後半の failure は再び「初回 failure」として warning 対象

とする。

### 3.13 closeEvent への保存接続

- B5 に含める
- 終了時に最終保存を接続する
- ただし、大規模な終了処理や終了確認ダイアログ化には広げない

---

## 4. Goal

本節の項目群を、**MS14-B5 の canonical completion criteria** とする。  
セクション 16 とセクション 19 は、本節と同一の要件集合を再掲するものであり、意味差を持たない。

1. wx 側で VMD 保存ダイアログから保存できる
2. overwrite confirm が動作する
3. 保存成功時に `last_vmd_output_dir` が更新される
4. 保存成功 / 失敗に応じて status が整合する
5. recent TEXT / WAV が実用的に扱える
6. invalid recent が適切に除去される
7. invalid recent 除去による recent 変化が save 対象として扱われる
8. `last_text_dialog_dir` / `last_wav_dialog_dir` の更新が save 対象として扱われる
9. settings save が実行できる
10. settings save は merge-save で unknown key / section を壊さない
11. settings save failure は通常動作中の初回のみ warning、それ以降は抑制できる
12. save 要求の重複・連鎖発火は coalesced save として扱える
13. busy 中に発生した save 要求は pending として保持され、最初の安全な save 機会で flush できる
14. closeEvent 時の最終保存がある
15. closeEvent failure は終了をブロックしない
16. settings dialog / migration / MS15 内容が流入していない

---

## 5. In Scope

MS14-B5 に含めるものは以下とする。

- VMD save dialog
- `.vmd` 拡張子補完
- 出力先 path 妥当性確認
- overwrite confirm
- `generate_vmd_from_text_wav(...)` の実行
- 保存成功 / 失敗時の state / status 更新
- `last_vmd_output_dir` 更新
- recent TEXT / WAV の実用運用
- recent menu 再構築
- invalid recent の除去
- settings save 実装
- merge-save 実装
- save request の coalescing / debounce / pending flush の最小実装
- 初回失敗時のみ warning の settings save failure policy
- closeEvent 時の最終保存
- B5 対象の軽量テスト

---

## 6. Out of Scope

MS14-B5 では以下を行わない。

- settings dialog
- settings migration / 新形式 ini 導入
- VMD recent 新設
- waveform 実描画
- Preview 実描画
- playback 実装
- Zoom / Pan / shared viewport
- language / theme の本格保存活用拡張
- 大規模な close lifecycle 再設計
- autosave 基盤の全面実装
- export queue / batch export
- MS15 以降の UX 改善

---

## 7. Expected Functional Boundary

B5 は **保存・履歴・永続化を閉じる block** である。  
ここでやるべきことは、「B3 / B4 までで成立した入力・解析結果を、実用的に保存し、次回起動へ必要な設定を残せるようにする」ことである。

責務の切り分けは以下のとおり。

- **B1:** 実用 UI 骨格拡張
- **B2:** 状態管理と action state 回復
- **B3:** 入力導線 parity 回復
- **B4:** 解析実行 parity 回復
- **B5:** 出力・履歴・settings save parity 回復
- **B6:** 統合整理と parity closeout

したがって B5 では、MS15 の表示再構築や大規模 settings 体系整理を持ち込まない。

---

## 8. VMD Output Policy

### 8.1 保存前提条件

VMD 保存開始前に、最低限以下を確認する。

- TEXT が有効に読込済みである
- WAV が有効に読込済みである
- `current_timing_plan` が有効である
- **B2/B4 の正式 busy state が false である**
- 出力先 path が妥当である

条件不足時は保存を実行しない。

### 8.2 保存導線

B5 の保存導線は以下を基本とする。

1. save dialog を開く
2. path を受け取る
3. 必要なら `.vmd` を補完する
4. path 妥当性を確認する
5. 既存ファイルなら overwrite confirm を出す
6. `generate_vmd_from_text_wav(...)` を呼ぶ
7. 成功 / 失敗を UI / state へ反映する

### 8.3 保存成功時

保存成功時は、以下を行う。

- `last_vmd_output_dir` を更新する
- status を成功側へ更新する
- 必要最小限の保存成功情報を反映する
- settings save の coalesced save 要求を立てる

### 8.4 保存失敗時

保存失敗時は、以下を行う。

- **毎回 warning を表示する**
- status を失敗側へ更新する
- `current_timing_plan` は原則保持する
- 入力状態は保持する
- 再試行可能性を維持する

### 8.5 settings save failure policy との区別

B5 で規定する「通常動作中は初回失敗時のみ warning、以後抑制」は、**自動的に走る settings save** にのみ適用する。  
**ユーザーの明示的操作である VMD 保存失敗には適用しない。**

---

## 9. Recent Files Policy

### 9.1 recent TEXT / WAV の位置づけ

recent TEXT / WAV は、B3 でメモリ上更新済みの前提を受け、B5 で

- 実用 menu として扱えること
- invalid entry を整理できること
- settings save で次回起動へ残せること

を成立させる。

### 9.2 invalid recent の扱い

invalid recent は、以下のいずれかのタイミングで除去してよい。

- メニュー再構築時
- 実行時

判定対象:

- 空文字
- 非存在
- ディレクトリ
- 拡張子不一致
- 破損により利用不能な path

### 9.3 invalid recent 除去後の保存

invalid recent の除去によって recent リストが変化した場合は、**recent 更新と同じ扱い** とし、save 対象に含める。

- **通常動作中**のメニュー再構築または実行時に prune された場合は、coalesced save 要求を立ててよい
- **起動直後の初期整合処理中**に prune された場合は、即時書込を必須とせず、
  - そのセッションの最初の安全な save 機会
  - または closeEvent 時最終保存
  のいずれかで反映してよい

この起動時例外は、セクション 3.2 および 10.3 の一般規則に対する明示的例外である。

### 9.4 warning 方針

invalid recent の除去時に、毎回重い warning を出す必要はない。  
ただし、ユーザーが明示的にその履歴を開こうとして失敗した場合は、B5 側 pre-check での failure に限り最小 warning を出してよい。

---

## 10. Settings Save Policy

### 10.1 保存対象

B5 の settings save 対象は以下とする。

- `recent_text_files`
- `recent_wav_files`
- `last_vmd_output_dir`
- `last_text_dialog_dir`
- `last_wav_dialog_dir`
- `morph_upper_limit`
- `closing_hold_frames`
- `closing_softness_frames`

必要に応じて、B2 / B3 / B4 で既に実用状態として扱っている**同種の最小追加項目**は含めてよい。  
ただし、MS15 以降で意味が変わる UI 状態や未導入機能の設定は保存対象へ広げない。

### 10.2 保存方式

- merge-save を採用する
- wx 側既知 key だけを更新する
- unknown key / unknown section は可能な限り保持する
- この保持を成立させるため、save 実装は raw ini または等価な merge base を参照できなければならない

### 10.3 保存契約

settings save は、以下の 2 系統を持ってよい。

#### coalesced save 要求

- recent 更新後
- invalid recent 除去により recent リストが変化した後
- VMD 保存成功後
- TEXT 読込成功により `last_text_dialog_dir` が更新された後
- WAV 読込成功により `last_wav_dialog_dir` が更新された後
- main frame 上の以下のパラメータ変更確定後
  - `morph_upper_limit`
  - `closing_hold_frames`
  - `closing_softness_frames`

#### 最終保存

- closeEvent 時

### 10.4 dialog dir 更新と保存の関係

`last_text_dialog_dir` および `last_wav_dialog_dir` は保存対象であり、**対応する読込成功によって値が更新された時点で coalesced save 要求対象** とする。  
これらは recent 更新に従属するだけの暗黙値ではなく、**独立に保存価値を持つ path state** として扱う。

### 10.5 パラメータ変更時の保存粒度

main frame 上のパラメータ変更は、**値変更イベントの全発火ごとに即書込しない**。  
少なくとも以下のいずれかの粒度で扱う。

- 編集確定時
- フォーカスアウト時
- debounce 後の最終値
- その他、実質的に「値が確定した」とみなせる時点

目的は、連続入力による I/O スパムと warning スパムを防ぐことにある。

### 10.6 通知ポリシー

ここで定義する save failure policy は、**settings save** にのみ適用する。

- 通常動作中の自動保存 / coalesced save failure
- closeEvent 時の最終保存失敗

が対象である。  
VMD 保存失敗には適用しない。

---

## 11. Save Dispatch and Coalescing Policy

### 11.1 基本方針

複数の save トリガーが同時または短時間に連続発火した場合、settings save は **1 回の coalesced save** にまとめてよい。

### 11.2 対象例

たとえば TEXT 読込成功では、以下がほぼ同時に発生し得る。

- `last_text_dialog_dir` 更新
- recent TEXT 更新
- invalid recent prune
- それらに伴う save 対象変化

この場合、各イベントごとに個別書込することは必須ではなく、**最新 state を 1 回の save へまとめてよい**。

### 11.3 busy 中の扱い

`is_busy == true` の間に save 要求が発生した場合は、

- その save を破棄しない
- pending / dirty として記録する
- `is_busy == false` へ戻った最初の安全な save 機会で flush する

### 11.4 closeEvent との関係

pending save が残っている場合でも、closeEvent 時最終保存で取り込んでよい。  
ただし、closeEvent failure でも終了はブロックしない。

---

## 12. Settings Save Failure Policy

### 12.1 適用対象

本節の failure policy は、**settings save** に対してのみ適用する。

適用対象:

- recent 更新後の save
- invalid recent 除去後の save
- VMD 保存成功後の save
- dialog dir 更新後の save
- パラメータ変更確定後の save
- closeEvent 時の最終 save

適用対象外:

- ユーザーが明示的に実行した VMD 保存失敗

### 12.2 通常動作中の初回失敗

通常動作中の自動保存 / coalesced save において、セッション内で最初の failure が発生した場合は、

- modal warning を 1 回だけ出してよい
- status / 内部フラグに失敗状態を残してよい

### 12.3 通常動作中の以後の失敗

同一セッション中の以後の failure では、

- modal warning を毎回出さない
- status / log 相当の最小記録へ留める

### 12.4 解除条件

通常動作中の settings save が **1 回でも成功した場合**、そのセッションにおける「初回失敗済み」状態は解除してよい。  
その後に再度 failure が発生した場合は、新たな初回 failure として warning 対象に戻る。

### 12.5 closeEvent 時の失敗

closeEvent 時の final save failure は、

- セッション内初回 failure であっても modal warning を出さない
- 終了処理を優先する
- 必要最小限の内部記録または非ブロッキング通知に留める

### 12.6 意図

保存不能状態で UI が連続して modal warning を出し続けたり、終了時に warning によって閉じられなくなる UX 崩壊を防ぐ。

---

## 13. Close Lifecycle Policy

### 13.1 closeEvent での保存

- closeEvent 時に最終保存を行う
- 既に coalesced save 済みでも、最後の state を反映する意味で最終保存を許可する

### 13.2 closeEvent でやらないこと

- 終了確認ダイアログの追加
- 保存失敗時に終了をブロックする高度制御
- 長いシャットダウン処理
- 大規模 cleanup 再編

B5 の closeEvent 接続は、**最小の final save** に限定する。

### 13.3 closeEvent 時の保存失敗

closeEvent 時の最終保存で failure が起きた場合でも、**終了処理は優先し、終了をブロックしない**。  
このとき、

- modal warning によって終了を実質停止させない
- status / log / 内部フラグ相当の最小通知に留める

とする。

---

## 14. Design Policy

### 14.1 Close Practical Workflow, Not Configuration System

B5 の目的は、実用 workflow の出口を閉じることであり、設定システム全体を作り直すことではない。

### 14.2 Preserve Existing Settings Assets

merge-save により、既存 0.3 系や後続 block の設定資産を壊さないことを優先する。

### 14.3 Keep Save Failure Non-Spammy

settings save 失敗時の通知は必要だが、modal warning の連打は避ける。  
ただし、VMD 保存失敗は明示操作なので毎回明確に通知する。

### 14.4 Treat Recent as User-Facing, Not Raw Cache

recent は単なる配列ではなく、実用 menu として壊れた entry を残しにくい状態にする。

### 14.5 Preserve Retryability After Export Failure

保存失敗で `current_timing_plan` や入力状態まで壊さない。

---

## 15. Step Breakdown

### Step 1. Confirm B3/B4 Output Preconditions and Save Targets

- B3 の recent / dialog dir メモリ更新状態を確認する
- B4 の `current_timing_plan` 正本性を確認する
- B5 で保存すべき settings key を整理する

#### Exit Condition

- B5 の保存対象と export 前提条件が明確になっている

---

### Step 2. Build VMD Save Entry

- save dialog を接続する
- path を受け取る
- `.vmd` 補完を行う
- path 妥当性確認を行う

#### Exit Condition

- export 入口が UI から安全に到達可能である

---

### Step 3. Build Overwrite Confirm

- 既存ファイルへの保存時に overwrite confirm を出す
- confirm 結果に応じて続行 / 中止する

#### Exit Condition

- 既存ファイルの上書きが無確認で発生しない

---

### Step 4. Build Export Success / Failure Reflection

- `generate_vmd_from_text_wav(...)` 実行を接続する
- 成功時:
  - `last_vmd_output_dir` 更新
  - status 更新
  - 必要最小限の成功情報反映
- 失敗時:
  - 毎回 warning
  - **status を失敗側へ更新**
  - 入力 / 解析結果保持

#### Exit Condition

- export の成功 / 失敗が state / UI へ整合して戻る

---

### Step 5. Build Recent Menu Practical Handling

- recent TEXT / WAV menu 再構築
- invalid recent の除去
- recent 実行時の pre-check 境界整理
- prune 後の save トリガーを整理する

#### Exit Condition

- recent menu が壊れた entry を引きずりにくい
- B3 と B5 の warning 境界が明確である
- prune 後の永続化タイミングが明確である

---

### Step 6. Build Merge-Save Settings Writer

- known key 更新
- unknown key / section 保持
- merge base 参照方式を決める
- settings save helper を整備する

#### Exit Condition

- ini を壊しにくい save 契約が成立している

---

### Step 7. Build Save Dispatch and Timing Hooks

- coalesced save 要求を必要箇所へ接続する
- pending / dirty flush を整理する
- closeEvent 時最終保存を接続する

coalesced save フック対象は少なくとも以下とする。

- recent TEXT / WAV 更新後
- invalid recent 除去で recent リストが変化した後
- VMD 保存成功後
- TEXT 読込成功により `last_text_dialog_dir` が更新された後
- WAV 読込成功により `last_wav_dialog_dir` が更新された後
- main frame 上の以下のパラメータ変更確定後
  - `morph_upper_limit`
  - `closing_hold_frames`
  - `closing_softness_frames`

#### Exit Condition

- settings save の dispatch / coalescing / busy 競合処理が実用的に閉じている

---

### Step 8. Build Save Failure Notification Policy

- settings save について、通常動作中は初回失敗だけ warning
- 以後は抑制
- success 後の failure-state reset を整理する
- closeEvent 時 failure は終了優先で非ブロッキング化

#### Exit Condition

- save failure の通知が非スパムかつ close-safe になっている

---

### Step 9. Add Light Tests

- export success / failure
- overwrite confirm
- recent invalid removal
- merge-save
- first-failure-only settings warning
- success による failure-state reset
- dialog dir update save trigger
- busy 中 pending save flush
- coalesced save
- closeEvent final save

の軽量テストを追加または更新する

#### Exit Condition

- B5 の保存・履歴・永続化契約が最小限テストで担保されている

---

## 16. Acceptance Criteria

本節は、セクション 4 の canonical completion criteria をそのまま再掲する。

1. wx 側で VMD 保存ダイアログから保存できる
2. overwrite confirm が動作する
3. 保存成功時に `last_vmd_output_dir` が更新される
4. 保存成功 / 失敗に応じて status が整合する
5. recent TEXT / WAV が実用的に扱える
6. invalid recent が適切に除去される
7. invalid recent 除去による recent 変化が save 対象として扱われる
8. `last_text_dialog_dir` / `last_wav_dialog_dir` の更新が save 対象として扱われる
9. settings save が実行できる
10. settings save は merge-save で unknown key / section を壊さない
11. settings save failure は通常動作中の初回のみ warning、それ以降は抑制できる
12. save 要求の重複・連鎖発火は coalesced save として扱える
13. busy 中に発生した save 要求は pending として保持され、最初の安全な save 機会で flush できる
14. closeEvent 時の最終保存がある
15. closeEvent failure は終了をブロックしない
16. settings dialog / migration / MS15 内容が流入していない

---

## 17. Test Plan

### 17.1 Export Success

- `current_timing_plan` 有効時に保存開始できる
- `.vmd` 補完が働く
- 保存成功時に status が更新される
- `last_vmd_output_dir` が更新される

### 17.2 Export Failure

- path 妥当性エラー
- overwrite 中止
- 書込失敗
- 生成失敗

に対して、

- warning が表示される
- **status が失敗側へ更新される**
- 入力 / 解析結果が保持される

### 17.3 Overwrite Confirm

- 既存ファイル保存時に confirm が出る
- Yes で続行
- No で中止

### 17.4 Recent Practical Handling

- recent menu が構築される
- invalid entry が除去される
- recent 実行時に不正 path を残し続けない
- prune 後の save トリガーが機能する
- B5 pre-check failure と B3 load failure が二重 warning にならない

### 17.5 Merge-Save

- known key を更新できる
- unknown key / unknown section が保持される
- ini 全体を既知 key だけで再構成しない
- merge base を前提に unknown 保持が成立する

### 17.6 Settings Save Failure Policy

- 通常動作中の初回 settings save failure で warning
- 以後の同一セッション失敗で warning 抑制
- settings save success 後に failure-state が解除される
- VMD 保存失敗は毎回 warning
- closeEvent failure では modal warning を出さない

### 17.7 Dialog Dir Save Trigger

- TEXT 読込成功により `last_text_dialog_dir` が更新された時、save 対象になる
- WAV 読込成功により `last_wav_dialog_dir` が更新された時、save 対象になる

### 17.8 Save Dispatch / Coalescing

- 複数トリガーが短時間に発火しても save が多重実行されない
- 最新 state を 1 回の coalesced save で反映できる
- `is_busy == true` 中の save 要求が pending になり、busy 解消後に flush される

### 17.9 Close Final Save

- closeEvent 時に最終保存が走る
- closeEvent failure で終了がブロックされない
- 異常に重い終了処理にならない

---

## 18. Risks and Control

### Risk 1. B5 Slipping into Settings System Redesign

save を触るついでに設定体系を全面刷新したくなる。  
**Control:** merge-save の最小契約に留める。

### Risk 2. B5 Slipping into MS15

保存成功時に Preview / waveform を実表示したくなる。  
**Control:** status と最小情報反映に留める。

### Risk 3. Save Failure Spam

settings save できない環境で毎回 warning を出すと UX が崩壊する。  
**Control:** 通常動作中は初回失敗だけ warning、success 後に reset。closeEvent 時は非ブロッキング。

### Risk 4. Unknown Key Loss

既知 key だけで書き戻すと既存資産を壊す。  
**Control:** merge-save を必須化し、merge base 前提を明示する。

### Risk 5. Export Failure Resetting Too Much

保存失敗で `current_timing_plan` や入力状態まで壊すと再試行性が悪い。  
**Control:** 保存失敗時は入力 / 解析結果を原則保持する。

---

## 19. Definition of Done

本節は、セクション 4 の canonical completion criteria をそのまま再掲する。

1. wx 側で VMD 保存ダイアログから保存できる
2. overwrite confirm が動作する
3. 保存成功時に `last_vmd_output_dir` が更新される
4. 保存成功 / 失敗に応じて status が整合する
5. recent TEXT / WAV が実用的に扱える
6. invalid recent が適切に除去される
7. invalid recent 除去による recent 変化が save 対象として扱われる
8. `last_text_dialog_dir` / `last_wav_dialog_dir` の更新が save 対象として扱われる
9. settings save が実行できる
10. settings save は merge-save で unknown key / section を壊さない
11. settings save failure は通常動作中の初回のみ warning、それ以降は抑制できる
12. save 要求の重複・連鎖発火は coalesced save として扱える
13. busy 中に発生した save 要求は pending として保持され、最初の安全な save 機会で flush できる
14. closeEvent 時の最終保存がある
15. closeEvent failure は終了をブロックしない
16. settings dialog / migration / MS15 内容が流入していない

---

## 20. Handoff Notes for Implementation

- B5 は「保存・履歴・永続化を実用的に閉じる」block であり、設定システム再設計 block ではない
- known key だけ更新し、unknown key / section を保持すること
- merge-save は write 側だけでなく、merge base の read / memory 前提も満たすこと
- recent は user-facing menu として壊れた entry を整理すること
- invalid recent の除去は recent 更新とみなし、永続化対象として扱うこと
- `last_text_dialog_dir` / `last_wav_dialog_dir` は保存対象であり、読込成功後の save 対象として扱うこと
- save 要求は必要に応じて coalesce / debounce / pending 化し、多重書込を避けること
- busy 中に発生した save 要求を破棄しないこと
- VMD recent は増やさず、`last_vmd_output_dir` と status 反映に留めること
- settings save failure 通知は通常動作中のみ初回だけに抑制し、success 後は reset 可能とすること
- VMD 保存失敗は毎回明示的に通知すること
- closeEvent 時の最終保存は入れるが、失敗しても終了をブロックしないこと
- recent 実行時は B5 pre-check と B3 通常読込 warning を二重に出さないこと
- busy 判定は B2/B4 の正式 state を参照し、B5 独自定義を増やさないこと
- B6 が統合整理、MS15 が表示 / 再生再構築を受け取れるよう境界を守ること