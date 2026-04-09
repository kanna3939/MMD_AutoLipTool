# MS11-10 Implementation Plan

## 0. 文書目的

MS11-10 は、MS11 系の最終整合フェーズとして、
**これまでの実装到達状態を版数・文書・参照導線へ同期し、MS12 へ渡せる状態を作る**
ための文書整備タスクである。

今回の基準版は **`Ver 0.3.8.0`** とする。

---

## 1. 前提

本タスク時点で、MS11 系では少なくとも次が workspace へ反映済みである。

- MS11-8 final-closing softness 系
- MS11-9 Preview / GUI / writer / observations 整合
- MS11-9D から MS11-9D-6 の speech-internal lip-motion 改善
- MS11-9E 系 same-vowel residual refinement
- MS11-9F 系 cross-vowel residual refinement
- MS11-9G top-end shaping residual refinement
- MS11-9FIX7 closing smoothing tail-contract realignment

また、MS11-9G は MMD 側確認込みで一旦クローズ扱いにでき、MS11-9FIX7 は
`Test11_9S1.vmd` / `S2` / `S3` / `S4` の差分確認まで完了している状態とする。

---

## 2. 目的

MS11-10 の目的は次のとおり。

- `Ver 0.3.8.0` として主要文書の版数を同期する
- MS11 系の現在地を、実装済み / 保留 / 残課題に分けて整理する
- MS11-9 系の分岐文書を、横断要約と正本参照で見返しやすくする
- MS12 に持ち越すものと、MS11 内で継続するものを明示する
- FIX7 までの closing smoothing 再整理結果を、MS11 closeout 文書へ織り込む

---

## 3. 主対象文書

- `README.md`
- `pyproject.toml`
- `docs/Specification_Prompt_v3.md`
- `docs/MS11_MS12_Roadmap_and_Scope_Split.md`
- `docs/MS11-9_Remaining_Issues.md`
- `docs/MS11-9_Observation_Handoff_Contract_Memo.md`
- `docs/MS11-9_Summary_and_Handoff.md`
- `docs/repo_milestone.md`
- `docs/Version_Control.md`

必要なら次も追加対象とする。

- `docs/MS11-10_Implementation_Plan.md` 本書

---

## 4. 実施内容

### 4.1 版数同期

- `README.md` の版数を `Ver 0.3.8.0` へ更新
- `pyproject.toml` の version を `0.3.8.0` へ更新
- 主要仕様文書・roadmap の baseline version を `Ver 0.3.8.0` へ更新

### 4.2 MS11-9 系の整備

- same-vowel / cross-vowel / top-end shaping の現在地を再確認する
- `MS11-9_Summary_and_Handoff.md` を横断要約の入口として整える
- `Remaining_Issues` と契約メモは、残テーマだけが見える状態へ寄せる

### 4.3 closeout 記録

- `repo_milestone.md` に `Ver 0.3.8.0` 同期メモを追加
- `Version_Control.md` に MS11-10 文書整備エントリを追加
- FIX7 の確認結果を `MS11-10` 文書から参照できる状態へ揃える

---

## 5. 完了条件

- `Ver 0.3.8.0` が主要文書で一貫している
- MS11 系の現在地が `README / roadmap / specification / milestone / version log` で矛盾しない
- MS11-9 系は、個別計画書を残しつつ、横断要約から辿れる
- FIX7 の現在地が、短縮バグ修正ではなく tail post-process 契約整理として読める
- コミット前確認として、変更対象一覧と主要版数参照が見える状態になっている

---

## 6. スコープ外

- 新規コード実装
- RMS 定数の再調整
- MS12 GUI responsiveness / splash / packaging
- same-vowel 微調整の追加実装
- observation-layer の再設計本体

---

## 7. 今回の整理方針

- コード実装そのものは増やさない
- 既存の Implementation Plan 群は保持する
- ただし、見返し用の入口は `MS11-9_Summary_and_Handoff.md` へ寄せる
- MS11-9G は「クローズ済みだが再オープン余地あり」の扱いで文書化する
- MS11-9FIX7 は「短縮バグは実出力差分上で解消済み、今後は自然さ確認が主題」の扱いで文書化する

---

## 8. 要約

MS11-10 は、
**MS11 系の最終整合を `Ver 0.3.8.0` として文書へ反映し、FIX7 まで含めた closeout 状態を MS12 へ渡せる形に整えるための sync タスク**
である。
