# MS12-5 Implementation Plan

## 0. 文書目的

MS12-5 は、
**distribution dependency bundling cleanup**
を導入するための実装タスクである。

本タスクの目的は、
Windows 向け配布物の依存関係とライセンス同梱方針を整理し、
**再現可能な build / release 手順として固定すること**
である。

ここで重視するのは配布整備であり、

- GUI 機能追加
- pipeline / writer の仕様変更
- splash / startup の再改修

は対象外とする。

---

## 1. 現在の前提

MS12-5 着手時点で、repo には次の土台がある。

- `build.ps1`
  - Windows PowerShell 向け build 実行入口
- `MMD_AutoLipTool.spec`
  - PyInstaller `onedir` の build 正本
- `README.md`
  - エンドユーザー向けの実行 / build / license 案内
- `NOTICE`
  - 配布時 notice と平易な免責
- `THIRD_PARTY_LICENSES.md`
  - 主要依存の配布観点メモ

また、現時点で確認できる事実は次のとおり。

- 現行 build は PyInstaller `onedir` である
- `.spec` では `whisper` / `pyopenjtalk` / `tiktoken` 系の data / binary を収集している
- 現行 build 定義には FFmpeg の明示的同梱は存在しない
- `NOTICE` と `THIRD_PARTY_LICENSES.md` には、将来 FFmpeg を同梱する場合の注意書きだけがある
- README には build 手順と license 同梱対象の概略がある

したがって、MS12-5 の主題は
**実際に何を配布物へ同梱し、何をユーザー環境前提にするかを固定すること**
である。

---

## 2. このタスクの目標

MS12-5 の目標は次のとおり。

1. Windows 向け配布 build の依存解決方針を固定する
2. build / spec / README / notice / third-party docs の記述を揃える
3. 採用する外部バイナリがある場合は、入手元と同梱対象を明確化する
4. ライセンス同梱物を release 観点で整理する

完了像は、
**開発環境依存の暗黙前提を減らし、release 時に必要な build / 配布物 / 文書の整合が取れた状態**
である。

---

## 3. 壊さない前提

MS12-5 では、以下を壊さない前提を固定する。

- 現行の `onedir` build 方針は維持する
- `src/main.py` の起動導線は変えない
- GUI / pipeline / writer の仕様は変えない
- 既存の LICENSE / NOTICE / THIRD_PARTY_LICENSES の役割分担は維持する

重要:

- external binary を同梱する場合でも、無関係なツールまで bundling しない
- build スクリプトに環境依存の絶対パスを直書きしない
- 配布物の説明と実際の spec 内容を食い違わせない

---

## 4. スコープ

### 4.1 対象

- `build.ps1`
- `MMD_AutoLipTool.spec`
- `README.md`
- `NOTICE`
- `THIRD_PARTY_LICENSES.md`
- 必要なら release-side 補助文書

### 4.2 非対象

- GUI 実装
- splash / responsiveness 追加改修
- installer 作成
- GitHub Actions など CI 自動配布の導入

---

## 5. 現状コード上の整理

### 5.1 `build.ps1`

現状の `build.ps1` は、

- clean オプション
- PyInstaller 実行
- 生成物存在確認
- 任意の smoke launch

を担っている。

配布依存の制御はまだ薄く、
**どの外部バイナリをどこから build へ渡すか**
は規定されていない。

### 5.2 `MMD_AutoLipTool.spec`

現状の `.spec` は、

- Python side dependencies
- assets
- `pyopenjtalk` dynamic libs

を集めているが、
**FFmpeg や他の外部実行バイナリを扱う節は無い**
。

### 5.3 license / notice docs

現状の `NOTICE` と `THIRD_PARTY_LICENSES.md` は、
FFmpeg 同梱を前提にしていない。

このため、MS12-5 では
**採用時のみ FFmpeg 関連を明文化し、非採用なら現状前提を固定する**
のが自然である。

---

## 6. 実装方針

### 6.1 基本方針

MS12-5 は、
**FFmpeg bundling を採用する前提で、build / docs / license 同梱方針を同期する**
方針で進める。

方針は次の順に固定する。

1. FFmpeg の取得元と build 入力配置を決める
2. `.spec` と `build.ps1` をその方針に合わせる
3. README / NOTICE / THIRD_PARTY_LICENSES を同期する
4. release 時確認観点を最小チェックリスト化する

### 6.2 設計原則

- FFmpeg を採用するなら、取得元・格納位置・同梱対象・license 案内をセットで定義する
- build 手順は Windows ローカルで再現できる範囲に留める
- release-side 文書は「仮定」ではなく「採用方針」に合わせて書く

---

## 7. 想定実装ステップ

### Phase 1

FFmpeg bundling 方針の固定

- build 入力として扱う想定配置を定める
- 取得元と版数固定方法を定める

### Phase 2

build / spec 整理

- `.spec` の datas / binaries を必要範囲で更新する
- `build.ps1` に必要なら option や前提チェックを追加する

### Phase 3

配布文書同期

- README の build / 配布説明を更新する
- `NOTICE` に配布時同梱物と補足注意を書き足す
- `THIRD_PARTY_LICENSES.md` に採用した依存を明記する

### Phase 4

最小確認観点整理

- build 成功
- exe 起動
- 配布物に必要文書が含まれる
- 採用した外部バイナリが所定位置に入る

---

## 8. 実装候補

### 候補A: FFmpeg を build 入力として手動配置する

利点:

- repo に外部バイナリ本体を持ち込まない
- build 手順上の責任範囲を明確にしやすい

必要作業:

- 配置先を固定
- `build.ps1` で存在確認を入れる
- `.spec` で同梱対象を定義する
- docs / license を更新する

懸念:

- build 前提の手動準備が増える

現時点の確定方針:

- **この方式を採用する**

### 候補B: build 時に所定フォルダからコピーする

利点:

- ローカル運用を定型化しやすい

懸念:

- 環境依存パスの扱いを慎重にしないと再現性が落ちる

---

## 9. テスト / 確認方針

最低限、次を押さえる。

1. build 手順が README と一致している
2. `dist\MMD_AutoLipTool\` に想定ファイルが出力される
3. LICENSE / NOTICE / third-party 情報が release 観点で揃う
4. 採用した外部バイナリの有無が docs と一致する

可能なら追加で押さえる。

- smoke launch
- 配布物を別ディレクトリへ移して起動確認

---

## 10. 保留課題

### 保留1

FFmpeg の取得元と版数固定方法

例:

- ユーザー側で手動配置
- repo 外の既定フォルダからコピー
- release 作成時に別途取得

現時点の確定方針:

- build 時は **手動配置された FFmpeg 一式** を入力として扱う

残る論点:

- なし

追加の確定事項:

- 手動配置先は exe ルート下の **`FFmpeg`** フォルダとする
- 想定する配布物単位は **`bin` のみ** とする
- 版数記録は **関連ドキュメント全て** に反映する

### 保留2

配布物に third-party 個別 license テキストをどこまで同梱するか

現時点の仮置き:

- `LICENSE` / `NOTICE` / `THIRD_PARTY_LICENSES.md` は必須
- 追加の個別 license text は、実際の採用依存に応じて判断する

---

## 11. 完了条件

- 配布依存方針が明文化されている
- build / spec / README / notice / third-party docs が一致している
- release build の再現手順が明確である
- FFmpeg の取得元・版数・license 案内が整理されている

---

## 12. リスク

### リスク1

FFmpeg の取得元を曖昧なまま build だけ先行してしまう

対策:

- 先に取得元と配置方針を固定する

### リスク2

docs だけ更新されて build 実体とズレる

対策:

- `.spec` / `build.ps1` / README / notice を同時に確認する

### リスク3

license 同梱責務が過小整理になる

対策:

- 採用依存ごとに notice / third-party docs 反映要否を点検する

---

## 13. この段の出口

MS12-5 の出口は、
**Windows 向け配布 build と同梱物の方針が固定され、release 時に何を含めるべきかが明確な状態**
である。
