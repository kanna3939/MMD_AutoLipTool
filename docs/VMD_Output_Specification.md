# MMD_AutoLipTool VMD出力仕様書

## 1. 文書情報

- 文書名: `docs/VMD_Output_Specification.md`
- 対象プロジェクト: `MMD_AutoLipTool`
- 対象バージョン系: Ver0.4.x 以降
- 現行基準: MS15 closeout 後 / MS16 以降の拡張準備
- 対象出力: MikuMikuDance 用 VMD リップモーション
- 主対象モーフ: `あ / い / う / え / お`
- フレーム基準: 30fps
- 主実装領域: `src/vmd_writer/`
- 関連領域:
  - `src/core/pipeline.py`
  - `src/gui_wx/preview_panel.py`
  - `src/gui_wx/waveform_panel.py`
  - `docs/Specification_Prompt_v4.md`
  - `docs/Security_Safety_Specification.md`

---

## 2. 文書目的

本書は、`MMD_AutoLipTool` が生成する VMD ファイルの出力仕様を定義する。

本書が扱うのは、VMDフォーマット全体の完全解説ではなく、**本ツールが出力するリップモーションVMDの契約**である。

本書の目的は以下である。

- 本ツールが出力する VMD の対象範囲を明確にする
- 出力するデータと出力しないデータを明確にする
- 母音モーフ `あ / い / う / え / お` の出力規則を固定する
- Preview 表示と VMD 出力の関係を明確にする
- writer 変更時の禁止事項を明確にする
- MS17以降の wav/mp3/m4a対応 / MMD用WAV出力に進む前に、VMD単体の出力契約を固定する
- Codex による実装・修正・レビュー時の判断基準にする

---

## 3. 適用範囲

本書は、以下に適用する。

- VMDファイル出力
- VMDモーフキーフレーム生成
- 母音モーフの値生成
- フレーム番号変換
- キーフレーム正規化
- zero key の扱い
- closing hold / closing softness
- bridge / smoothing
- Preview 表示との整合
- VMD保存時の安全性
- writer 周辺のテスト観点

---

## 4. 非対象

本ツールは、以下を出力対象としない。

### 4.1 ボーン系

以下は出力しない。

- ボーンモーション
- センター移動
- 腕・足・頭・首などのボーン操作
- IK関連キー
- 補間曲線付きボーンキー
- 物理演算制御
- モデル姿勢制御

### 4.2 カメラ系

以下は出力しない。

- カメラモーション
- カメラ位置
- カメラ回転
- カメラ距離
- 視野角
- パースON/OFF
- カメラ補間曲線

### 4.3 照明系

以下は出力しない。

- 照明色
- 照明方向
- ライトモーション

### 4.4 セルフシャドウ・表示制御系

以下は出力しない。

- セルフシャドウ設定
- モデル表示 / 非表示
- IK ON/OFF
- 外部親設定
- アクセサリ制御

### 4.5 その他

以下も出力対象外とする。

- PMX / PMD ファイル
- VPD ポーズファイル
- 音声ファイルそのもの
- MMDプロジェクトファイル
- MME / エフェクト設定
- モデル改変データ
- 表情全般の自動生成

MS17以降で MMD用WAV出力を追加する場合でも、VMD側の出力対象は引き続き **モーフキーフレームのみ** とする。

---

## 5. VMD出力の基本方針

本ツールが出力する VMD は、MMDで読み込むためのリップモーションVMDである。

基本方針:

- 出力対象はモーフキーフレームのみ
- 対象モーフは `あ / い / う / え / お`
- フレーム基準は 30fps
- 入力TEXTと音声解析結果から母音イベント列を生成する
- 母音イベント列を VMD モーフキーフレームへ変換する
- 不正確な成功より、安全な失敗を優先する
- 出力前に重複フレームや不要キーを正規化する
- 出力失敗時に不完全なVMDを成功扱いしない

---

## 6. VMDコンテナ上の扱い

本ツールは、VMDファイルとしてMMDが読み込める形式で出力する。

ただし、本書では VMD バイナリフォーマット全体の完全な仕様解説は行わない。

本ツールの出力契約として重要な点は以下である。

- VMDファイルとして読み込み可能であること
- モーフキーフレームが正しく格納されること
- ボーン、カメラ、照明など、本ツールが出力しない要素を含めないこと
- 未使用セクションを出力する必要がある場合でも、内容は空またはゼロ件として扱うこと
- MMD側で「モーフモーション」として読み込めること

実装上、VMDフォーマットのヘッダ、モデル名欄、各セクション件数、バイナリ配置などは、既存 `vmd_writer` の実装を正とする。

本書は、主に **何を出力するか / 何を出力しないか / どのようなモーフキー列にするか** を定義する。

---

## 7. 出力対象モーフ

本ツールが出力するモーフは、選択中のモデルプロファイルが解決した5種類に固定する。
プロファイル未選択時は日本語セット、Latin組み込みプロファイル選択時はLatinセットを使用する。

```text
日本語: あ / い / う / え / お
Latin:   A / I / U / E / O
````

### 7.1 モーフ名

VMDに書き込むモーフ名は、MMDモデル側に存在する母音モーフ名と一致する必要がある。

本ツールの基本仕様では、以下の2つの組み込みセットを前提とする。母音の意味順とVMDの
30fps契約はセット間で変わらない。

| セット | a | i | u | e | o |
| -- | -- | -- | -- | -- | -- |
| 日本語（未選択時の既定） | `あ` | `い` | `う` | `え` | `お` |
| Latin（組み込みプロファイル） | `A` | `I` | `U` | `E` | `O` |

### 7.2 モーフ名の非対象

以下は現行仕様では非対象とする。

* `ワ / ん / 笑い / まばたき` などの追加表情
* モデルごとの独自モーフ名マッピング
* ユーザー定義モーフセット
* 複数モデル向けモーフ名プリセット

Latin `A / I / U / E / O` はMS23の組み込みセットとして対象内である。それ以外の
任意マッピングとユーザー定義セットは将来課題として扱う。

---

## 8. フレーム基準

### 8.1 基本フレームレート

本ツールのVMD出力は 30fps を基準とする。

```text
1秒 = 30フレーム
```

### 8.2 秒からフレームへの変換

内部処理では秒ベースの時刻を保持してよい。

VMD出力時には、秒ベース時刻を 30fps のフレーム番号へ変換する。

基本式:

```text
frame_no = round(time_sec * 30)
```

ただし、実装で既に一貫した丸め規則が存在する場合は、その実装に従う。

重要なのは、writer、Preview、テストでフレーム基準の意味が食い違わないことである。

### 8.3 フレーム番号の扱い

フレーム番号は整数とする。

以下を避ける。

* 負のフレーム番号
* 同一モーフ・同一フレームへの矛盾キー
* 入力音声範囲から大きく逸脱する不要キー
* 解析結果と対応しない古いキー

### 8.4 フレーム原点

フレーム原点は、入力音声の再生開始時刻を 0 秒 / 0 フレームとして扱う。

Preview表示、波形表示、VMD出力は、同じ時間原点を使う。

---

## 9. モーフ値仕様

### 9.1 値の範囲

モーフ値は、原則として以下の範囲に収める。

```text
0.0 <= value <= 1.0
```

### 9.2 値の意味

| 値 | 意味 |
| ------------------- | ------------------------- |
| `0.0` | 口形を閉じた状態、または当該モーフを無効にした状態 |
| `1.0` | 当該モーフの最大適用状態 |
| `0.0 < value < 1.0` | 中間的な開き具合 |

### 9.3 peak_value

各母音イベントの強度は、`peak_value` を基本として扱う。

`peak_value` は、音声のRMS評価やfallback方針により決定される。

writer は、event に付与された `peak_value` を尊重する。

### 9.4 morph upper limit

GUI上のモーフ上限値が設定されている場合、出力モーフ値はその上限に従う。

モーフ上限値を変更した場合、既存解析結果をそのまま保存可能状態にしてはならない。

変更後は再解析待ち、または出力無効状態に戻す。

### 9.5 zero peak

`peak_value == 0.0` 相当のイベントは、通常の発声shapeとは区別して扱う。

方針:

* zero-only shape を最終出力へ残さない
* zero peak イベントを不自然なclamp blockerとして扱わない
* zero peak により後続の有効shapeが不自然に短縮されないようにする
* ただし、閉口を表現するために必要な zero key は保持してよい

---

## 10. タイミングイベントからVMDキーへの変換

### 10.1 入力イベント

writer が受け取る主な情報は以下である。

* morph name
* time_sec
* start_sec
* end_sec
* duration_sec
* peak_value
* observation
* shape関連メタデータ
* closing hold / closing softness 関連設定

実装上のデータ構造名は、現行コードに従う。

### 10.2 変換方針

タイミングイベントは、VMDモーフキーフレーム列へ変換される。

基本方針:

* 発声開始前に必要な zero key を置く
* 発声区間内で peak_value に到達する
* 発声終了後に zero へ戻す
* 短区間ではfallback shapeを使う
* 長さが十分ある場合は台形系shapeを使う
* 同一母音の近接イベントでは bridge / smoothing を検討する
* cross-vowel の短い無音区間では transition bridge を検討する

### 10.3 time_sec の扱い

`time_sec` は、イベントの中心または代表時刻として扱われる。

shape生成時には、`start_sec` / `end_sec` / `duration_sec` / observation と合わせて解釈する。

`time_sec` のみを使って全shapeを決定してはならない。

### 10.4 start / end の扱い

発声区間の開始・終了は、解析結果および補正後 interval に基づく。

writer は、補正済み interval を尊重する。

---

## 11. shape生成仕様

### 11.1 基本方針

writer は、イベントの長さ・種類・近接関係・peak_value に応じて、適切なshapeを生成する。

shape は、VMDモーフキーフレーム列として表現される。

### 11.2 shape 種別

本ツールで扱う主なshapeは以下である。

* short fallback
* legacy triangle
* legacy symmetric trapezoid
* asymmetric trapezoid
* multi-point envelope
* closing hold
* closing softness
* same-vowel bridge
* cross-vowel transition bridge
* top-end shaping

### 11.3 asymmetric trapezoid

十分な長さがあるイベントでは、非対称台形shapeを使用してよい。

目的:

* 急な立ち上がりを避ける
* 発声中の口形を維持する
* 終了時に自然に閉じる
* PreviewとVMD出力の見え方を近づける

### 11.4 short fallback

短すぎるイベントでは、通常の台形shapeを成立させると不自然になる場合がある。

その場合は、short fallback を使ってよい。

方針:

* 無理に多点shapeへしない
* 必要最小限のキーで表現する
* zero-only shape を作らない
* 既存の短区間挙動を不用意に壊さない

### 11.5 multi-point envelope

同一母音が近接する場合など、単純な台形では不自然になるケースでは、multi-point envelope を使ってよい。

目的:

* 同一母音連続時の不自然な谷を軽減する
* 発声内部の短いゼロ区間を自然につなぐ
* Preview表示とVMD出力の意味を近づける

### 11.6 top-end shaping

発声上辺の終端側では、音量変化に応じた top-end shaping を行ってよい。

目的:

* 発声終端の不自然な維持を避ける
* peakからclosingへの移行を滑らかにする
* 音声実態に近い口形変化にする

---

## 12. closing hold / closing softness

### 12.1 closing hold

`closing_hold_frames` は、発声終了付近の口形維持を制御する。

方針:

* frame単位で扱う
* 発声終了直後の閉口を遅らせる
* 過剰なholdで口が開いたままにならないようにする
* 後続shapeと衝突する場合は安全にclampする

### 12.2 closing softness

`closing_softness_frames` は、発声終了後の閉口補間を制御する。

方針:

* frame単位で扱う
* final closing を滑らかにする
* peak_value や morph upper limit とは独立した制御とする
* 元のtailを不自然に短縮しない
* 後続shape開始直前でclampする

### 12.3 hold と softness の関係

closing hold と closing softness は、どちらも発声終了側の形状に影響する。

ただし、意味は異なる。

| 項目 | 目的 |
| ---------------- | ------------ |
| closing hold | 口形を一定時間維持する |
| closing softness | 閉じる動きを滑らかにする |

両者を混同してはならない。

### 12.4 単イベント明示編集時のcrossfade例外

自動解析結果とglobal `closing_hold_frames` / `closing_softness_frames` は、
後続shape開始直前でclampする保守的な規則を維持する。

一方、group末尾の単イベントに対し、次のいずれかを明示編集した場合は、
直後の非0・異母音shapeとのcrossfadeを許可する。

* 正方向の終了offset
* event別closing hold
* event別closing softness

対象は現在shapeのterminal下降区間と、直後shapeの開始zero後から最初のevent peakまでに
限定する。zero-only shapeはtarget検索時だけ飛ばしてデータ上は保持する。最初の非0
successorが同母音なら、それより後の異母音まで探索しない。3つ目の非0 shapeがある場合、
現在shapeはその開始frameより前に0へ戻す。

次shapeのevent、control point、peak valueは移動・clipしない。重複区間内の次母音の
明示control pointが0.95以上でも値はそのままVMDへ渡し、保存禁止にはしない。
automatic handoffだけで成立した重複は、この明示編集例外として扱わない。

### 12.5 Previewとの関係

Preview表示では、closing hold / closing softness の意味が視覚的に確認できることが望ましい。

PreviewとVMD保存は同じeffective shape planを使用し、単イベントcrossfadeを
別々に再計算してはならない。

---

## 13. bridge / smoothing の扱い

### 13.1 基本方針

bridge / smoothing は、発声内部の不自然な途切れや急変を抑えるために使う。

ただし、過剰な補間により、音声に存在しない口形維持を作ってはならない。

### 13.2 same-vowel bridge

同一母音が短い間隔で連続する場合、完全に閉じると不自然になることがある。

この場合、same-vowel bridge を適用してよい。

目的:

* 同一母音連続時の不自然な谷を抑える
* 発声の連続感を出す
* 短いゼロ区間を自然につなぐ

### 13.3 cross-vowel transition bridge

異なる母音間でも、短い無音区間や transition がある場合は、保守的な bridge を適用してよい。

ただし、異なる母音同士を過剰につなぎ、口形が曖昧にならないようにする。

### 13.4 short zero-run span

短いゼロ区間は、observation に基づいて bridge 対象として扱ってよい。

方針:

* 音声内部の短い断絶を補う
* 長い無音区間は無理につながない
* silence と speech-internal gap を区別する

### 13.5 禁止事項

bridge / smoothing では以下を避ける。

* 長い無音区間を発声継続扱いする
* 異なる母音を過剰に混ぜる
* 全体の開口状態を不自然に維持する
* zero peak を有効発声として扱う
* Previewだけ自然で、VMD出力が別挙動になる

---

## 14. zero key / zero-only shape の扱い

### 14.1 zero key の目的

zero key は、モーフを閉じるために必要である。

主な目的:

* 発声開始前に口形を閉じる
* 発声終了後に口形を閉じる
* 前後のイベントとの残留値を防ぐ
* MMD側で前のモーフ値が残るのを防ぐ

### 14.2 必要な zero key

以下のzero keyは必要に応じて保持する。

* 立ち上がり前 zero
* 終了 zero
* shape間の境界を明確にする zero
* 他母音との重なりを避けるための zero

### 14.3 zero-only shape

zero-only shape は、発声として意味を持たない。

方針:

* zero-only trapezoid を最終出力に残さない
* zero-only multi-point shape を最終出力に残さない
* peak_value == 0.0 由来の不要shapeを除去する
* ただし、閉口に必要な zero key は保持する

### 14.4 zero prune

不要な zero key は prune してよい。

ただし、以下を壊してはならない。

* 立ち上がり前 zero 保証
* 終了 zero 保証
* 母音切替時の残留防止
* MMD側での前値保持対策
* Previewとの意味的整合

---

## 15. 重複フレーム正規化

### 15.1 基本方針

同一 `morph_name` / 同一 `frame_no` に複数のキーが存在する場合、最終出力前に正規化する。

### 15.2 正規化単位

正規化単位:

```text
(morph_name, frame_no)
```

### 15.3 正規化規則

基本規則:

* 非ゼロ値を優先する
* 複数の非ゼロ値がある場合は最大値を採用する
* 全てゼロの場合はゼロ1件に統合する
* 正規shapeを破壊しない
* 必要な立ち上がり前 zero / 終了 zero を消しすぎない

### 15.4 禁止事項

以下は禁止する。

* 同一モーフ・同一フレームに矛盾する複数キーを残す
* 非ゼロ値を不要zeroで上書きする
* 正常なshort fallbackを不要shapeとして削除する
* 正常なmulti-point envelopeを単純化しすぎる
* PreviewとVMDで意味が変わる正規化を行う

---

## 16. キーフレーム並び順

### 16.1 基本方針

VMD出力時のキーフレームは、MMDが安定して読み込める順序にする。

基本方針:

* morph_name ごとに整理してよい
* frame_no 昇順で整理する
* 同一frameの重複は正規化する
* 出力直前に整合を確認する

### 16.2 ソート

出力前に、少なくとも以下の観点でソートされていることが望ましい。

1. morph_name
2. frame_no

実装上のソート順が異なる場合でも、MMD上の解釈が安定し、テストで確認されていればよい。

### 16.3 不正順序の回避

以下を避ける。

* frame_no が逆転したまま出力される
* 同一morph内で不要な重複が残る
* 古いイベント由来のキーが現在イベントより後に混入する
* 負のframeが混入する

---

## 17. 出力上限

### 17.1 キーフレーム総数上限

本ツールのVMD出力では、モーフキーフレーム総数の上限を以下とする。

| 項目 | 上限 |
| ----------- | ------ |
| モーフキーフレーム総数 | 22,000 |

### 17.2 上限超過時

上限を超える場合は、VMD出力を中止する。

以下は禁止する。

* 黙って一部キーを削除する
* 先頭または末尾を自動切り捨てする
* 警告のみで保存を続行する
* 不完全なVMDを成功扱いする

### 17.3 上限値の意味

この上限は、セキュリティ上の絶対限界ではなく、個人制作向けWindowsアプリとして応答性・安定性・MMD側での扱いやすさを守るための運用上限である。

---

## 18. 保存・上書き・失敗時の扱い

### 18.1 保存先

VMD保存時は、利用者が保存先を選択する。

最後に正常保存したフォルダを記憶し、次回保存時の初期フォルダとして使ってよい。

### 18.2 上書き確認

保存先に同名ファイルが存在する場合は、利用者確認を挟む。

方針:

* 黙って上書きしない
* 上書き拒否時は保存を中止する
* 上書き拒否はエラーではなくキャンセル扱いとしてよい
* ただし保存成功として扱わない

### 18.3 保存失敗

保存失敗時は、利用者へ明示通知する。

少なくとも以下を確認できるようにする。

* 保存に失敗したこと
* 対象ファイル
* エラー種別またはエラーメッセージ
* 再試行可能かどうか

### 18.4 不完全ファイル

出力途中で失敗した場合、不完全なVMDファイルを可能な限り残さない。

方針:

* 一時ファイルに書き出してから置換する方式を検討する
* 直接書き込みの場合も、失敗時の扱いを明確にする
* 既存の正常ファイルを破壊しない
* 失敗した保存を成功扱いしない

### 18.5 Busy状態

保存中または出力中にBusy状態を使う場合は、以下を守る。

* 多重保存を防ぐ
* 入力変更を防ぐ
* 失敗時にBusyを解除する
* キャンセル時にBusyを解除する
* UIを再実行可能状態へ戻す

---

## 19. Preview表示との関係

### 19.1 基本方針

Preview表示は、VMD出力の見え方を事前確認するための補助表示である。

ただし、最終出力の正本はVMDファイルである。

### 19.2 共有すべき情報

PreviewとVMD出力は、可能な限り以下を共有する。

* timing plan
* event timeline
* peak_value
* start / end
* shape_kind
* control points
* closing hold
* closing softness
* bridge / smoothing の判断結果

### 19.3 完全一致しなくてよい部分

Previewは画面表示用であるため、以下はVMDと完全一致しなくてもよい。

* 描画ピクセル単位の形状
* 色
* 線幅
* 表示上の補間
* viewport clipping
* 表示負荷軽減のための省略

ただし、意味が変わる差異は避ける。

避けるべき差異:

* Previewでは開いているのにVMDでは閉じている
* PreviewではbridgeされているのにVMDでは完全に切れている
* Previewではclosing softnessが見えるのにVMDでは反映されない
* VMDに出ないshapeをPreviewだけに表示する
* VMDに出るshapeをPreviewに表示しない

### 19.4 Preview更新条件

以下の場合、PreviewはVMD出力可能状態と整合するよう更新またはクリアする。

* TEXT再読込
* 音声ファイル再読込
* 解析用WAV生成元変更
* 解析成功
* 解析失敗
* 解析キャンセル
* パラメータ変更
* timing plan 無効化
* writer契約変更

---

## 20. テスト観点

### 20.1 writer単体テスト

以下をテスト対象とする。

* 基本VMD出力
* 対象モーフ `あ / い / う / え / お`
* 秒からフレームへの変換
* peak_value 反映
* morph upper limit 反映
* short fallback
* asymmetric trapezoid
* multi-point envelope
* closing hold
* closing softness
* bridge / smoothing
* zero-only shape 除去
* 立ち上がり前 zero
* 終了 zero
* 重複フレーム正規化
* キーフレーム上限
* 保存失敗時の扱い

### 20.2 pipeline連携テスト

以下を確認する。

* pipeline から writer へ必要情報が渡る
* observation が必要なshape判断に使える
* closing_hold_frames が writer へ渡る
* closing_softness_frames が writer へ渡る
* zero peak の扱いが壊れない
* fallback時にもVMD出力が成立する

### 20.3 Preview整合テスト

以下を確認する。

* writer shape と Preview shape の意味が一致する
* closing hold がPreviewへ反映される
* closing softness がPreviewへ反映される
* bridge / smoothing がPreviewへ反映される
* Previewクリア条件がVMD保存可能状態と整合する

### 20.4 GUI保存導線テスト

以下を確認する。

* 解析前はVMD保存できない
* 解析成功後はVMD保存できる
* 入力再読込後はVMD保存できない
* パラメータ変更後はVMD保存できない
* 同名保存時に確認が入る
* 保存失敗時にエラーが表示される
* 保存失敗時にPython例外種別またはエラーメッセージを確認できる

### 20.5 MMD実機確認

自動テストだけでは、MMD上の見た目までは完全に確認できない。

必要に応じて、以下を手動確認する。

* MMDでVMDを読み込める
* 対象モーフにキーが入る
* ボーンやカメラが動かない
* 音声と大きくズレない
* closing hold / softness が不自然でない
* same-vowel bridge が過剰でない
* 無音区間で口が開き続けない

---

## 21. 変更時の禁止事項

VMD writer 周辺を変更する場合、以下は禁止する。

### 21.1 出力対象の拡大禁止

明示的な仕様変更なしに、以下を出力してはならない。

* ボーンキー
* カメラキー
* 照明キー
* セルフシャドウキー
* IKキー
* モデル表示キー
* アクセサリ制御
* 独自拡張データ

### 21.2 モーフ対象の拡大禁止

明示的な仕様変更なしに、対象モーフを `あ / い / う / え / お` 以外へ広げてはならない。

追加モーフ対応は将来課題として扱う。

### 21.3 正規化破壊禁止

以下を壊してはならない。

* 重複フレーム正規化
* 非ゼロ優先
* 最大値採用
* 全ゼロ1件化
* 立ち上がり前 zero
* 終了 zero
* zero-only shape 除去
* short fallback 保護
* multi-point envelope 保護

### 21.4 Previewとの乖離禁止

writerを変更した場合、Previewとの意味的整合を確認する。

以下は禁止する。

* VMDだけshapeが変わり、Previewが旧仕様のまま残る
* Previewだけ新shapeに対応し、VMD出力が旧仕様のまま残る
* closing hold / softness の片方だけ反映される
* bridge / smoothing の判断がPreviewとVMDで分岐する

### 21.5 エラー握りつぶし禁止

VMD保存・writer処理で例外が発生した場合、例外を握りつぶしてはならない。

少なくとも以下を確認可能にする。

* Python例外種別
* エラーメッセージ
* 発生フェーズ
* 対象ファイル

---

## 22. MS17以降との関係

### 22.1 wav / mp3 / m4a 対応

MS17以降で wav / mp3 / m4a 入力に対応する場合でも、VMD出力仕様自体は維持する。

入力音声は直接VMDに影響するのではなく、以下の流れで扱う。

```text
wav / mp3 / m4a
→ 安全な解析用WAV生成
→ 解析用WAV検証
→ 既存pipeline
→ VMD writer
→ VMD出力
```

### 22.2 MMD用WAV出力

MMD用WAV出力を追加する場合、出力物は以下の2系統になる。

| 出力物 | 目的 |
| --- | ---------- |
| VMD | リップモーション |
| WAV | MMDに読み込む音声 |

VMDファイル自体に音声を含めない。

VMDとWAVの対応関係は、ファイル名・保存先・UI表示で分かるようにする。

### 22.3 VMDとMMD用WAVの両方を出力する場合の注意

VMDとMMD用WAVの両方を出力する場合、以下を明確にする。

* VMD保存成功 / WAV保存成功
* VMD保存成功 / WAV保存失敗
* VMD保存失敗 / WAV保存成功
* 両方失敗
* 片方のみ存在する場合の利用者案内
* 不完全ファイルの削除
* 再実行時の上書き確認

### 22.4 MS25 MMD一括出力

MMD一括出力では、現在の有効なVMD状態、入力音声から生成したMMD用WAV、同じ診断snapshotに基づく
レポートを専用directoryへまとめる。出力名は次の契約とする。

| 成果物 | ファイル名 |
| --- | --- |
| VMD | `<audio_stem>_lip.vmd` |
| MMD用WAV | `<audio_stem>_mmd.wav` |
| 診断レポート | `<audio_stem>_report.txt` |

既定のdirectory名は`<audio_stem>_MMD`で、親directoryとfolder名は利用者が指定できる。
一括出力は個別保存済みファイルを流用せず、staging directoryで3成果物を生成・検証してから確定する。
同名destinationのmerge・置換・上書きは行わず、失敗やcancelでは既存出力を保護する。

---

## 23. 将来拡張候補

以下は将来課題とする。

### 23.1 モーフ名マッピング

モデルごとに母音モーフ名が異なる場合に備え、モーフ名マッピング機能を検討してよい。

例:

* `あ / い / う / え / お`
* `A / I / U / E / O`
* 独自モーフ名

日本語とLatinの2セットはMS23で組み込み対象とする。モデルごとの独自モーフ名や
ユーザー定義セットなど、任意のマッピングは現時点では非対象。

### 23.2 追加表情

以下は将来課題とする。

* 口角
* 笑い
* まばたき
* 困り顔
* 発音補助モーフ

現時点では非対象。

### 23.3 英語・多言語対応

英語音声や多言語音声への対応では、5母音モーフへのマッピング方針を別途定義する必要がある。

現時点では将来課題とする。

### 23.4 VMDフォーマット詳細文書

必要になった場合、VMDバイナリ仕様の詳細調査文書を別途作成してよい。

ただし、本書はあくまで本ツールのVMD出力契約を定義する文書である。

---

## 24. 実装報告時の必須記載

VMD writer またはVMD保存導線を変更した場合、実装報告には以下を含める。

* 変更したファイル
* 変更したshape生成規則
* 変更した正規化規則
* zero key の扱いに影響があるか
* closing hold / softness に影響があるか
* bridge / smoothing に影響があるか
* Previewとの整合確認
* 実行したwriterテスト
* 実行したpipelineテスト
* MMD実機確認の有無
* 残した未確認点

---

## 25. 変更履歴

### 2026-08-20 / MS23-B6 cross regression同期

* profile未選択時の日本語セットと、組み込みLatinセットのVMD出力契約を追加。
* 任意のモデル固有mapping、ユーザー定義セット、追加表情は将来課題として維持。

### 2026-07-26 / MS21-B5追加補正

* 自動解析とglobal tailは後続shape直前clampを維持することを明記。
* 単イベントの終了offset・hold・softnessに限るmanual crossfade例外を追加。
* target値0.95以上をclipせず、PreviewとVMDで同じeffective planを使う契約を固定。

### 2026-05-01 / 初版

* `MMD_AutoLipTool` が出力するVMDリップモーションの仕様を独立文書化。
* 出力対象をモーフキーフレームのみに限定する方針を明記。
* ボーン、カメラ、照明、セルフシャドウ、IK、表示制御を出力しないことを明記。
* 対象モーフを `あ / い / う / え / お` に限定。
* 30fps基準、モーフ値、peak_value、zero key、zero-only shape の扱いを整理。
* closing hold / closing softness の意味を分離。
* bridge / smoothing の扱いを整理。
* 重複フレーム正規化の契約を明記。
* Preview表示との関係を整理。
* MS17以降の wav/mp3/m4a対応、MMD用WAV出力との関係を整理。
* writer変更時の禁止事項と実装報告項目を追加。
