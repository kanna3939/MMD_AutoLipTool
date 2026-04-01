# MS12-4 Implementation Plan

## 0. 文書目的

MS12-4 は、
**splash version display**
を導入するための最小実装タスクである。

本タスクの目的は、
起動時 splash に現在のアプリ version を表示し、
**Help の version 情報と矛盾しない単一正本の version 表示導線**
を整えることである。

ここで重視するのは version 表示の整合であり、

- splash 画像デザインの刷新
- packaging の変更
- dependency version 表示の再設計
- main window 側の情報ダイアログ全面改修

は対象外とする。

---

## 1. 現在の前提

MS12-4 着手時点で、repo には次の土台がある。

- `src/main.py`
  - splash 表示導線
  - splash の最小表示時間制御
- `src/gui/main_window.py`
  - Help の version 情報ダイアログ
  - `importlib.metadata.version(...)` による app version 解決
- `pyproject.toml`
  - project version の定義

また、現時点で確認できる事実は次のとおり。

- splash は画像のみで、version 表示はまだ無い
- Help の version 情報は `_resolve_installed_version(["mmd-autolip-tool"])` を使っている
- `pyproject.toml` の project version は `0.3.7.1` である
- 現行コードでは splash 表示用の version source helper は存在しない

したがって、MS12-4 の主題は
**splash に文字を足すことそのものより、version source をどこで 1 本化するか**
である。

---

## 2. このタスクの目標

MS12-4 の目標は次のとおり。

1. splash に current version を表示する
2. splash と Help ダイアログの app version source を揃える
3. version 未取得時にも安全な fallback 表示を維持する
4. splash timing 改修と衝突しない

完了像は、
**起動 splash と Help 表示で同じ version を見せつつ、version 解決ロジックが多重化しない状態**
である。

---

## 3. 壊さない前提

MS12-4 では、以下を壊さない前提を固定する。

- MS12-3 の splash timing 導線は維持する
- Help の dependency version 表示は維持する
- `pyproject.toml` の project version を変えない
- splash リソース未存在時の fallback 起動を維持する
- `main.py` を起動導線の司令塔のまま維持する

重要:

- version source は増やさず、既存 source をまとめる方向で進める
- splash 表示追加のために画像アセットを全面差し替えない
- dependency version まで splash に載せない

---

## 4. スコープ

### 4.1 対象

- `src/main.py`
- `src/gui/main_window.py`
- 必要なら最小の version helper
- 起動 / version 表示の最小テスト
- 関連文書

### 4.2 非対象

- splash timing の再調整
- splash 画像差し替え
- dependency version の splash 表示
- packaging / installer 改修

---

## 5. 現状コード上の整理

### 5.1 現在の version 表示

現状の app version は `main_window.py` の Help ダイアログ側で
`importlib.metadata.version(...)` を使って解決している。

この構造のまま splash 側にも同じ処理を書くと、
**version 解決ロジックが `main.py` と `main_window.py` に分散する**
。

### 5.2 現在の splash 表示

現状の splash は `main.py` 内で `QSplashScreen(QPixmap(...))` を使って表示している。

したがって、MS12-4 で version を出す自然な方法は次のどちらかである。

- splash 用 pixmap に文字を描き込む
- splash widget 上へ文字を描画する軽い helper を通す

MS12-4 では最小差分を優先するため、
**pixmap へ文字を重ねた splash を生成する方向**
が第一候補である。

---

## 6. 実装方針

### 6.1 基本方針

MS12-4 は、
**app version source を helper 化し、その値を splash と Help の両方から参照する**
方針で進める。

方針は次の順に固定する。

1. app version 解決 helper を 1 か所へ寄せる
2. splash 描画時に version 文字列を重ねる
3. Help ダイアログも同じ helper を参照する
4. version 未取得時の fallback 文言を維持する

### 6.2 設計原則

- app version の正本は 1 経路にする
- splash の追加描画は最小の文字重ねに留める
- 文字色・位置は視認性優先だが、デザイン改修には踏み込まない
- `main.py` と `main_window.py` で共通利用できる helper 位置を選ぶ

---

## 7. 想定実装ステップ

### Phase 1

version source 整理

- app version を返す helper を導入する
- `main_window.py` の Help ダイアログでその helper を使うよう整理する

### Phase 2

splash 描画拡張

- splash 用 pixmap に version 文字列を重ねる
- リソース無し / pixmap 無効時の fallback を維持する

### Phase 3

Help 表示整合

- splash と Help で同じ app version が見えることを確認する
- dependency version 表示は現状維持とする

### Phase 4

最小テスト / 確認観点追加

- version helper が app version を返す
- splash 描画に version 文字列が渡る
- Help ダイアログが同じ app version を使う

---

## 8. 実装候補

### 候補A: 共通 version helper を追加

例:

- `src/app_version.py`
- もしくは `src/resource_utils.py` 近傍の最小 helper

利点:

- `main.py` と `main_window.py` の両方から使いやすい
- version source の単一化が明確

現時点ではこの案を第一候補とする。

### 候補B: `main_window.py` の helper を流用して `main.py` からも使う

懸念:

- 起動導線が GUI 実装へ依存しやすくなる

このため、MS12-4 では第一候補にしない。

---

## 9. テスト方針

最低限、次を押さえる。

1. app version helper が version を返す
2. version 未取得時も fallback 文言が返る
3. splash 作成時に version 文字列が描画される
4. Help ダイアログ側が同じ app version source を使う

可能なら追加で押さえる。

- 実機で splash 上の視認性を確認する
- version 表示位置が splash timing と競合しないことを確認する

---

## 10. 保留課題

### 保留1

version 表記形式

現時点の確定方針:

- **`Ver. x.y.z` 形式** とする

### 保留2

version 表示位置

現時点の確定方針:

- 添付イメージで指定された、
  **ロゴ下の中央下寄り空白帯（赤丸位置）**
  に表示する

### 保留3

version 未取得時の fallback を `Not installed` 系で出すか、version 非表示にするか

現時点の仮置き:

- Help と整合を取るため、
  **既存 fallback 文言を再利用**
  する方向を第一候補とする

---

## 11. 完了条件

- splash に current version が表示される
- splash 上では `Ver. x.y.z` 形式で表示される
- 表示位置はロゴ下の中央下寄り空白帯に収まる
- Help ダイアログの app version と同じ値になる
- version source が単一である
- splash timing と衝突しない
- version 未取得時も安全動作が維持される

---

## 12. リスク

### リスク1

version source を複数箇所で持ち続け、表示不一致が起きる

対策:

- app version helper を単一化する

### リスク2

splash 文字重ねで視認性が悪くなる

対策:

- 位置と文字サイズは最小変更に留める
- 実機確認で視認性を見る

### リスク3

MS12-3 の splash timing 導線を崩す

対策:

- splash 作成 helper の責務を拡張するだけに留める
- finish / timer 制御は触らない

---

## 13. この段の出口

MS12-4 の出口は、
**splash と Help で同じ app version を表示し、起動導線と表示整合が取れた状態**
である。

ここまで完了した後に、
次段の `MS12-5: distribution dependency bundling cleanup`
へ進む。
