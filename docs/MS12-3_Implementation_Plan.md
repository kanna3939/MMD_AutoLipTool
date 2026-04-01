# MS12-3 Implementation Plan

## 0. 文書目的

MS12-3 は、
**splash timing improvement**
を導入するための最小実装タスクである。

本タスクの目的は、
アプリ起動時に splash をより早く、より自然に見せることで、
**main window 構築待ちの体感を改善すること**
である。

ここで重視するのは起動導線の見え方であり、

- splash 画像デザインの刷新
- splash への version 表示
- packaging の変更
- settings schema の変更

は対象外とする。

---

## 1. 現在の前提

MS12-3 着手時点で、repo には次の土台がある。

- `src/main.py`
  - `QApplication` 生成
  - アプリアイコン設定
  - splash 画像読込と表示
  - settings 読込
  - `MainWindow` 構築
  - splash finish
- `src/gui/settings_store.py`
  - startup settings のロード元
- `assets/MMD_AutoLipTool_splash.png`
  - 現行 splash 画像

また、現時点で確認できる事実は次のとおり。

- splash はすでに実装済みである
- `main()` では `QApplication` 作成後、icon 設定の後に splash を表示している
- splash 表示後に `app.processEvents()` を 1 回呼んでいる
- splash 表示後に `SettingsStore.load()` と `MainWindow(...)` 構築が続いている
- 現状の splash は画像表示のみで、進捗文言や version 表示は持たない

したがって、現状の論点は「splash が存在しない」ことではなく、
**起動待ちのどの時間帯を splash で覆えているか、finish タイミングが自然か**
である。

---

## 2. このタスクの目標

MS12-3 の目標は次のとおり。

1. splash を起動導線の中でより早い段階に安定表示する
2. settings 読込や main window 構築待ちを splash 中に吸収する
3. splash finish のタイミングを main window 表示と自然につなぐ
4. splash リソースが無い場合も安全動作を維持する
5. 起動が速い環境でも splash が一瞬で消えないよう、最小表示時間を持てる構成にする

完了像は、
**起動待ちがゼロになることではなく、待ち時間が「固まっている」より「起動中である」と見える状態**
である。

---

## 3. 壊さない前提

MS12-3 では、以下を壊さない前提を固定する。

- `MainWindow` の startup settings 適用契約は変えない
- settings load の内容や schema は変えない
- splash リソース未存在時の fallback 起動は維持する
- アプリアイコン設定は維持する
- `main.py` を起動司令塔のまま維持する
- MS12-4 で扱う version 表示は先取りしない

重要:

- splash timing 改善のために、起動時設定の意味やロード内容を変更しない
- splash 側に別の重処理を載せない
- 目標は「早く見せること」を優先しつつ、速い環境では一瞬でも splash が認識できることを両立する

---

## 4. スコープ

### 4.1 対象

- `src/main.py`
- 必要なら最小の splash helper
- 起動導線の最小テストまたはスモーク観点
- 関連文書

### 4.2 非対象

- splash 画像差し替え
- splash version overlay
- setup / installer / packaging
- GUI 本体のレイアウト変更

---

## 5. 現状コード上の整理

### 5.1 現在の起動順

現状の `main()` は概ね次の順で動いている。

1. Windows App User Model ID 設定
2. `QApplication` 生成
3. app icon 設定
4. splash 画像読込と表示
5. `app.processEvents()`
6. `SettingsStore()` 生成
7. settings load
8. `MainWindow(...)` 構築
9. `window.show()`
10. `splash.finish(window)`
11. `app.exec()`

このため、改善余地として自然なのは次の 2 点である。

- splash 準備と表示を main window 構築待ちの前で確実化すること
- finish タイミングを「window は出たがまだ見切れている」状態と競合させないこと

### 5.2 現状の制約

- `QApplication` 作成前に `QPixmap` / `QSplashScreen` は扱えない
- settings load は `MainWindow` 初期表示前に必要である
- main window 構築自体は一定コストを持つ

したがって、MS12-3 では
**起動順の再整理で吸収できる範囲に限定する**
のが自然である。

---

## 6. 実装方針

### 6.1 基本方針

MS12-3 は、
**splash の生成・表示・finish を小さな helper へ整理し、起動順の見通しを上げる**
方針で進める。

方針は次の順に固定する。

1. splash 準備と表示を helper 化する
2. startup settings 解決より前に、表示可能ならすぐ出す
3. main window の初回 show と finish の順を自然に保つ
4. splash 非存在時の fallback を維持する

### 6.2 設計原則

- `main.py` の責務は「起動順の制御」に留める
- splash の存在判定は現行どおり resource path ベースで行う
- 設定読込は引き続き main window 構築前に行う
- finish は main window が表示可能になってから呼ぶ
- 将来の MS12-4 を見越しても、version 表示ロジックはまだ混ぜない

---

## 7. 想定実装ステップ

### Phase 1

現行起動順の整理

- splash 作成と表示を helper 化する
- startup 処理と splash 処理の責務境界を明確化する

### Phase 2

表示順の最小整理

- `QApplication` 作成直後に表示可能なら splash を出す
- settings load と `MainWindow(...)` 構築を splash 表示中に行う

### Phase 3

finish タイミング整合

- `window.show()` と `splash.finish(window)` の順を見直す
- 最小表示時間を考慮した finish 条件を整理する

### Phase 4

fallback と安全動作確認

- splash 画像が無い場合でも起動できることを確認する
- icon / language / settings load の既存動作が崩れないことを確認する

### Phase 5

最小確認観点整理

- splash が起動直後に見えること
- splash が main window 表示へ自然につながること
- splash 無しでも起動できること

---

## 8. 実装候補

### 候補A: `main.py` 内の最小 helper 化

例:

- `_create_and_show_splash(app) -> QSplashScreen | None`
- `_finish_splash_when_ready(splash, window)`

利点:

- 差分が最小
- 起動順が読みやすくなる

現時点ではこの案を第一候補とする。

### 候補B: 専用 splash helper module 追加

利点:

- 将来の splash version 表示や文言更新をまとめやすい

懸念:

- MS12-3 単体では責務がまだ小さく、過剰分割になりやすい

このため、MS12-3 では第一候補にしない。

---

## 9. テスト方針

最低限、次を押さえる。

1. splash 画像が存在する場合に `QSplashScreen.show()` が呼ばれる
2. splash 画像が存在しない場合でも `MainWindow` 起動が継続する
3. `window.show()` 後に `splash.finish(window)` が呼ばれる
4. startup settings load の流れが維持される

可能なら追加で押さえる。

- 起動スモークで splash が可視になることの手動確認
- finish タイミングが体感上早すぎず遅すぎないことの実機確認

---

## 10. 保留課題

### 保留1

`splash.finish(window)` を即時で呼ぶか、1 event loop turn 後へ送るか

論点:

- 即時 finish は単純
- 遅延 finish は初回描画競合を減らせる可能性がある

現時点の仮置き:

- まずは **即時 finish を基本とし、必要時のみ最小遅延導線を検討** する

### 保留2

splash 上に status 文言を出すか

現時点の仮置き:

- MS12-3 では扱わない
- 文言追加は version 表示と同じく後段テーマとする

### 保留3

最小表示時間を何ミリ秒程度に置くか

現時点の確定方針:

- 起動が速い環境でも splash を一瞬だけでも表示させる方向で進める

現時点の仮置き:

- 実装時は **短めの最小表示時間** を第一候補とし、
  体感確認を前提に最小限の値へ寄せる

---

## 11. 完了条件

- splash が起動導線の早い段階で表示される
- settings load と main window 構築待ちを splash 中に吸収できる
- splash finish が main window 表示と自然につながる
- 起動が速い環境でも splash が一瞬で消えず、認識できる
- splash リソース未存在時でも安全起動が維持される
- MS12-4 の version 表示導線と衝突しない

---

## 12. リスク

### リスク1

起動順整理のつもりで settings load や startup language の意味を変えてしまう

対策:

- settings 解決の中身は変えず、順序整理だけに留める

### リスク2

finish タイミング変更で splash が残り続ける、または一瞬で消える

対策:

- finish 経路を 1 か所に寄せる
- 実機確認で体感を確認する

### リスク3

splash helper 分離で起動コードの見通しが逆に悪くなる

対策:

- helper は最小に留める
- `main.py` 1 ファイル内で完結できる範囲を優先する

---

## 13. この段の出口

MS12-3 の出口は、
**起動時に splash がより自然に表示され、main window 構築待ちの体感が改善した状態**
である。

ここまで完了した後に、
次段の `MS12-4: splash version display`
へ進む。
