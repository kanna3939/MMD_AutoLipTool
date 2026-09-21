# MS21-B4 Tail Effect Notice Temporary Fix Plan

## 1. 文書情報

- 文書名: `MS21-B4 Tail Effect Notice Temporary Fix Plan`
- 配置: `docs/Implementation_Plan/MS21-B4_Tail_Effect_Notice_Temporary_Fix_Plan.md`
- 対象Block: MS21-B4
- 種別: ユーザーGUI確認で判明した説明不足に対する一時修正プラン
- 基準ブランチ: `feature/MS21-implementation`
- 基準コミット: `c098def Plan MS21-B4 event editor`
- 作成日: 2026-07-24
- 文書ステータス: Completed / Automated Verification Complete / User GUI Verification Complete
- 上位計画:
  - `docs/Implementation_Plan/MS21-B4_Implementation_Plan.md`
  - `docs/Implementation_Plan/MS21_Block_Breakdown.md`
- 対象状態:
  - MS21-B4 production実装と自動検証は作業ツリー上で完了している。
  - 一時修正実装後の全体testは550件と7 subtestsがpass表示、process exit code 0だった。
  - ユーザーGUI確認で「開口保持・閉口スムーズ・傾斜比の効果が反映されていないように見える」と報告された。
  - 調査により、値の保存・resolver接続・Preview更新は動作しているが、次の口形との間隔による反映量制限を一般ユーザーへ説明できていないことを確認した。

## 2. 背景

MS21-B4では、選択イベントに対して次を編集できる。

- 開口量
- 開始位置
- 終了位置
- 開口保持
- 閉口スムーズ
- 傾斜比

開口保持と閉口スムーズは、次の口形へ重ならない範囲でだけ反映される。現行resolverは、利用できる間隔を開口保持へ先に割り当て、その残りを閉口スムーズへ割り当てる。

例:

```text
指定:
  開口保持 5フレーム
  閉口スムーズ 5フレーム

次の口形まで利用できる間隔:
  2フレーム

実際の反映:
  開口保持 2フレーム
  閉口スムーズ 0フレーム
  傾斜比は作用しない
```

これは口形同士の重複を防ぐ現行契約に沿った結果であり、設定値の保存失敗やPreview更新漏れではない。

しかし、現行GUIは設定値と実際の反映値を表示するだけで、差が生じた理由を明示しない。そのため、内部契約を知らない一般ユーザーには、機能が動作していないように見える。

本修正では、内部処理の名称をユーザーへ要求せず、反映量が制限された理由と結果を選択イベント欄へ非モーダルnoticeとして表示する。

## 3. 目的

一般ユーザーが次を画面上で理解できる状態にする。

1. 入力した設定値は受け付けられている。
2. 次の口形までの間隔が短い場合、設定は一部だけ反映される。
3. 閉口スムーズが反映されない場合、傾斜比も作用しない。
4. どの値が設定値で、どの値が実際に反映されている値かを判断できる。
5. 操作を続けるために内部用語や設計文書を理解する必要がない。

## 4. In Scope

- 現行tail計算結果への利用可能延長フレーム数のadditive metadata追加
- 選択イベントeditor stateへの反映制限情報追加
- 次の口形との間隔により反映量が制限された場合の非モーダルnotice
- 開口保持、閉口スムーズ、傾斜比それぞれの一般ユーザー向け説明
- 傾斜比が無効な通常状態と、間隔不足で作用しない状態を区別した補助説明
- cleanup / B5対応待ちを示す既存の操作noticeと、反映制限を示す効果noticeの独立表示
- 設定値と実際の反映値が異なる行の視認性向上
- 反映条件が変わった場合のnotice再計算・自動消去
- light / dark themeに追従するオレンジ系attention表示
- pure core、adapter、wx、MainFrame live Previewの限定test追加
- MS21-B4関連回帰と全体test

## 5. Out of Scope

- hold優先、softness残余割当、次shape重複防止のresolver semantics変更
- 次の口形を自動移動して補正用の間隔を作る処理
- 口形同士の重複許可
- 補正値の自動縮小やcanonical snapshotからの削除
- Previewの自動Zoom
- VMD writerへのadjustment接続
- diagnostics fingerprint / reportへのadjustment値追加
- Undo / Redo
- analysis failure rollback
- global parameterの意味変更
- modal dialog、警告確認dialog、Status barへの新規表示
- dependency、package、build、license変更
- Qt / PySide6、network、cloud処理

## 6. 前提条件

- canonical補正状態は `UiState.current_adjustment_snapshot` とする。
- PreviewはB2 shared resolverの `EffectiveShapePlan` から生成する。
- 選択イベントeditorはresolverの結果を表示し、次shape間隔や反映量を独自計算しない。
- 開口保持と閉口スムーズの設定値が変わっても、重複防止により出力shapeが同値となる場合がある。
- 設定値は将来のstart / end補正やgroup変更後に作用する可能性があるため、反映量が0でも自動削除しない。
- 傾斜比overrideだけは、作用する閉口スムーズ点が消えた場合に現行契約どおりcanonical removalする。
- fixed morph `あ / い / う / え / お` を変更しない。

### 6.1 調査で確認した事実

- 制約のない末尾eventでは、開口保持・閉口スムーズ・傾斜比がresolver control pointとPreviewへ反映される。
- 次shapeが近い再現ケースでは、指定した開口保持5、閉口スムーズ5に対し、実際の反映は開口保持2、閉口スムーズ0となった。
- 閉口スムーズの実際の反映が0の場合、傾斜比が作用するcontrol pointは生成されない。
- native wx spin eventからMainFrame commit、snapshot、resolver、Preview更新までの経路は動作した。
- 修正前GUIには反映量制限の理由を説明する専用noticeがなかった。

### 6.2 一般ユーザー向け表現規則

ユーザー表示では次の内部用語を使用しない。

- tail
- clamp
- midpoint
- canonical
- snapshot
- resolver
- requested / effective

代わりに次の語を使用する。

- 次の口形
- 設定値
- 実際に反映される値
- 利用できる間隔
- 一部だけ反映
- 現在のプレビューには反映されない

ユーザー表示では、global parameter由来かevent個別override由来かにかかわらず、要求された値を「設定値」と表記する。「補正値」は使用しない。event個別overrideの有無は既存のoverride表示だけで表し、効果noticeの表示条件には使用しない。

### 6.3 2026-07-24 plan review反映

実装状態との照合で、P1はなく、P2を3件、P3を2件確認した。本版では次の推奨・提案を採用して解消した。

- P2: 既存の操作noticeと新規の効果noticeの所有権が未確定だったため、別control・別入力チャネルとして固定した。
- P2: 既存 `slope_enabled` と重複するstate案、および通常補助文に必要なfield不足を解消し、追加primitiveを固定した。
- P2: global parameterとevent個別overrideでnotice条件が未定義だったため、両方を同じ「設定値」として比較・表示する契約に固定した。
- P3: 利用可能延長量の説明を、resolverの実計算式とgroup境界に一致させた。
- P3: 操作noticeとの共存、個別消去、theme、bold範囲、通常補助文の分離を明示的なtest対象へ追加した。

レビュー時の現行実装確認では、B4限定testは11件pass、B2 resolver関連testは35件passで、いずれもprocess exit code 0だった。本版の文書修正後に、解消対象の旧記載が残っていないこと、末尾空白がないこと、見出し構成、`git diff --check` を再確認した。

### 6.4 2026-07-24 一時修正実装結果

- `ResolvedTailParameters.available_extension_frames` を追加し、現行resolverが算出する利用可能延長量を表示用metadataとして公開した。
- `SelectedEventEditorState` へ制限flag、効果notice、通常補助文を追加した。global parameterとevent個別overrideは同じ「設定値」契約で扱う。
- 既存操作noticeと効果noticeを別control・別入力チャネルへ分離し、効果noticeのheaderだけをbold、header / detailsをtheme別attention色、通常補助文をmuted色とした。
- 閉口スムーズが反映されなくなった場合の操作noticeから内部用語 `midpoint` を除去した。
- B4限定16件、B2 resolver関連35件、B3 selection / Preview関連22件、RightPane / theme関連21件、diagnostics関連37件、pipeline / VMD関連12件はpass表示、各process exit code 0だった。
- 全体testは550件と7 subtestsがpass表示、process exit code 0だった。
- `compileall src tests` はprocess exit code 0だった。
- 同日にユーザーGUI再確認が完了し、問題なしと報告された。

## 7. 対象ファイル

### 7.1 主変更対象

| ファイル | 変更内容 |
| --- | --- |
| `src/core/effective_shape_plan.py` | `ResolvedTailParameters` へ利用可能延長量をadditiveに公開 |
| `src/gui_wx/selected_event_editor.py` | resolver metadataから一般ユーザー向け効果notice stateと通常補助文を決定 |
| `src/gui_wx/right_pane.py` | 操作noticeと効果noticeを別controlで表示し、設定値と反映値の強調、theme追従を行う |
| `src/gui_wx/main_frame.py` | 同じeffective planからeditor stateを同期し、既存操作noticeと効果noticeを別チャネルで渡す |

### 7.2 テスト対象

| ファイル | 変更内容 |
| --- | --- |
| `tests/test_ms21_b4_selected_event_editor.py` | 利用可能間隔、部分反映、非作用、notice生成のpure test |
| `tests/test_wx_ms21_b4_selected_event_editor.py` | native wx event、notice表示・消去、theme、live Preview結合test |

### 7.3 関連確認対象

- `src/core/event_adjustment.py`
- `src/core/preview_transform.py`
- `src/gui_wx/ui_state.py`
- `src/gui_wx/theme.py`
- `src/gui_wx/preview_panel.py`
- `docs/Implementation_Plan/MS21-B1_Implementation_Plan.md`
- `docs/Implementation_Plan/MS21-B4_Implementation_Plan.md`

`event_adjustment.py`、`preview_transform.py`、`ui_state.py` は現行責務で対応可能な見込みのため、計画時点では変更対象にしない。不足が実装前チェックで確認された場合だけ、理由を記録して主変更対象へ昇格する。

## 8. 実装方針

### 8.1 core metadata

`ResolvedTailParameters` へ次を追加する。

```text
available_extension_frames: int | None
```

- 次groupがある場合は、現在groupの末尾eventのeffective end frameから、次groupの先頭eventのeffective start frameの1フレーム前まで利用できる非負フレーム数を返す。
- 計算式は `max(0, (next_group_first_start_frame - 1) - group_tail_event_end_frame)` とし、現行resolverの `available_extension` と一致させる。
- 最終shapeなど、次shapeによる上限がない場合は `None` とする。
- 既存の設定値、実際の反映値、shape control pointを変更しない。
- UIはcontrol pointや次shape startを再解釈せず、このmetadataだけを使用する。

### 8.2 editor state

`SelectedEventEditorState` へ、UIが再計算せず表示できるprimitive stateを追加する。

```text
available_extension_frames: int | None
hold_is_limited: bool
softness_is_limited: bool
effect_notice_header: str
effect_notice_lines: tuple[str, ...]
slope_helper_text: str
```

導出規則:

- `hold_is_limited`:
  - 指定した開口保持と実際の開口保持が異なる場合にtrue。
- `softness_is_limited`:
  - 指定した閉口スムーズと実際の閉口スムーズが異なる場合にtrue。
- 傾斜比が作用するかどうかは、新しい重複fieldを追加せず既存の `slope_enabled` を使用する。
- `effect_notice_header`:
  - 反映制限がある場合の先頭行を保持する。反映制限がなければ空文字列。
- `effect_notice_lines`:
  - 設定値と実際の反映値、および傾斜比が作用しない理由を保持する。
- `slope_helper_text`:
  - group末尾eventで閉口スムーズの設定値が0の場合だけ、通常補助文を保持する。
  - group末尾eventでない場合は、既存のgroup末尾event案内を操作noticeへ表示し、本fieldは空文字列とする。
  - 閉口スムーズの設定値が1以上だが実際の反映が0の場合は、効果noticeで理由を説明し、本fieldは空文字列とする。
  - `slope_enabled` がtrueの場合は空文字列とする。
- 日本語文言はpure GUI adapterが決定する。RightPaneでは条件分岐、フレーム計算、日本語文の組み立てを行わない。

### 8.3 notice表示条件

次のいずれかを満たす場合だけnoticeを表示する。

1. 開口保持の設定値と実際の反映値が異なる。
2. 閉口スムーズの設定値と実際の反映値が異なる。
3. 閉口スムーズを1フレーム以上指定しているが、実際の反映が0で傾斜比が作用しない。

表示例:

```text
次の口形までの間隔が短いため、設定値を一部だけ反映しています。
開口保持: 設定 5 → 反映 2 フレーム
閉口スムーズ: 設定 5 → 反映 0 フレーム
閉口スムーズが反映されないため、傾斜比は現在のプレビューには反映されません。
```

global parameter由来の値とevent個別override由来の値を同じ条件で比較する。overrideの有無をnotice表示条件にしない。このため、global parameterの設定値が実際の反映値と異なるeventを選択した直後にも効果noticeを表示する。これは現在のshapeへ実際に反映された結果を一般ユーザーへ説明するための意図した挙動とする。

設定値と実際の反映値が一致する場合は効果noticeを表示しない。

group末尾eventで閉口スムーズの設定値自体が0で傾斜比controlが無効な場合は、attention効果noticeではなく次の通常補助文を表示する。

```text
傾斜比を調整するには、閉口スムーズを1フレーム以上にしてください。
```

### 8.4 表示スタイル

- 操作noticeと効果noticeは選択イベントtab内の別controlへ表示する。
- modal dialogは使用しない。
- 既存 `st_selected_event_notice` はcleanup、B5対応待ち、reset結果などの操作notice専用として維持する。
- 効果notice用に `st_selected_event_effect_notice_header` と `st_selected_event_effect_notice_details` を追加する。
- 通常補助文用に `st_selected_event_slope_helper` を追加する。
- 効果noticeのheaderだけをboldにする。headerとdetailsはthemeの `attention_text`、通常補助文は通常またはmuted text色を使用する。
- 操作noticeと効果noticeは同時表示でき、一方の更新・消去で他方を上書きしない。
- ERRORを意味する赤色は使用しない。
- 設定値と反映値が異なる行の反映値labelにも `attention_text` を使用する。
- noticeは縦scroll範囲へ含め、狭い右paneでも全文へ到達できるようにする。
- Info / Warning tab、bottom Status、diagnostic reportへ同じ文を重複表示しない。

### 8.5 lifecycle

- 操作noticeは既存の `_selected_event_notice` が所有し、cleanup、B5対応待ち、reset結果などの現行lifecycleを維持する。
- 効果noticeと通常補助文は `SelectedEventEditorState` から毎回導出し、MainFrameやUiStateへ文字列を保存しない。
- `RightPane.set_selected_event_editor_state(state, busy=False, operation_notice="")` のように、editor stateと操作noticeを別引数で受け取る契約へ固定する。
- selection変更時は新しいselected eventのstateから効果noticeを再構築する。操作noticeは既存lifecycleに従って更新または消去する。
- 未選択、legacy-only selection、invalid identityでは効果noticeと通常補助文を消す。操作noticeは同じ理由だけで暗黙消去せず、既存lifecycleに従う。
- 設定変更後は同じeffective planから効果noticeを再構築する。
- start / end変更で利用可能間隔が変わった場合も効果noticeを更新する。
- reset selectedで設定値と反映値が一致した場合は効果noticeを消す。reset結果の操作noticeは独立して表示できる。
- analysis success / failure、input invalidation、workspace resetでは両チャネルを各所有元の既存規則に従って消去する。
- Busy中は両noticeを表示したままeditor操作だけをlockする。
- cancelでは保持したsnapshotとeffective planから効果noticeを再構築し、操作noticeは既存のcancel規則に従う。
- stale edit / late callbackではどちらのnoticeも変更しない。

### 8.6 resolver semanticsの維持

本修正では次を変更しない。

```text
利用可能延長量
  -> 開口保持へ先に割当
  -> 残りを閉口スムーズへ割当
  -> 閉口スムーズ点がある場合だけ傾斜比を適用
```

この順序を変更するとPreviewと将来のadjusted VMD writerの意味が変わるため、一時修正の範囲外とする。

## 9. 詳細ステップ

### Step 1: 実装前再チェック

- Git状態とuser-owned差分を確認する。
- B4実装差分が未コミットであることを確認する。
- tail control point生成、editor state、RightPane表示、MainFrame同期を再照合する。
- findingをP1 / P2 / P3へ分類する。

### Step 2: 利用可能間隔metadata追加

- `_shape_for_group()` で既に算出している利用可能延長量を `ResolvedTailParameters` へ格納する。
- `None` と0を区別する。
- shape frame、control point、normalization結果が変更されないことをtestする。

### Step 3: pure notice state追加

- global / event個別の区別なく設定値と実際の反映値を比較する。
- `available_extension_frames`、制限flag、既存 `slope_enabled` から、一般ユーザー向けheader、detail line、通常補助文を決定する。
- 内部用語がnoticeへ混入しないことをtestする。
- 最終shape、部分反映、完全非作用を分けてtestする。

### Step 4: RightPane表示

- 既存 `st_selected_event_notice` は操作notice専用として維持する。
- `st_selected_event_effect_notice_header`、`st_selected_event_effect_notice_details`、`st_selected_event_slope_helper` を追加する。
- cleanup notice、B5対応待ちnotice、反映制限noticeが同時表示できるようにする。
- 効果noticeのheaderだけをboldにし、detailsと通常補助文はboldにしない。
- 同じ文を重複表示しない。
- 設定値と反映値が異なるlabelだけをattention styleへ変更する。

### Step 5: MainFrame同期

- selected editor stateを構築する既存経路から効果notice stateを渡し、既存 `_selected_event_notice` は `operation_notice` として別に渡す。
- MainFrameやRightPaneで次shape間隔を再計算しない。
- edit成功、reset、selection変更、Busy、cancel、failure、workspace resetの表示更新を確認する。

### Step 6: test追加

- pure core metadata test
- pure editor notice test
- native wx spin event test
- MainFrame live Preview control point test
- selection / reset / lifecycle test
- theme / scroll test

### Step 7: 回帰確認

- B4限定test
- B2 effective shape / adapter
- B3 selection / Preview
- RightPane / theme
- diagnostics / save policy
- state / reset / playback
- pipeline / VMD
- 全体test
- compileall
- `git diff --check`

## 10. 状態遷移 / データ契約

### 10.1 表示状態

| 状態 | 効果notice / 通常補助文 |
| --- | --- |
| 未選択 | 非表示 |
| 設定値と反映値が一致 | 効果noticeは非表示 |
| 閉口スムーズの設定値が0 | 制限noticeは非表示。傾斜比の通常補助文を表示 |
| 開口保持だけ部分反映 | 開口保持の設定値→反映値を表示 |
| 閉口スムーズだけ部分反映 | 閉口スムーズの設定値→反映値を表示 |
| 保持が間隔を使い切る | 保持とスムーズの両方、および傾斜比非作用を表示 |
| 次shape上限なし | 制限noticeを表示しない |
| Busy | 現在の効果notice / 通常補助文を保持し、controlはlock |
| cancel | 保持stateから効果notice / 通常補助文を再構築 |
| failure / invalidation / workspace reset | 効果notice / 通常補助文を消去 |
| reset selected | reset後のstateから効果notice / 通常補助文を再構築 |

操作noticeはこの表とは別チャネルであり、cleanup、B5対応待ち、reset結果などの既存条件に従う。効果noticeまたは通常補助文の表示・消去によって操作noticeを変更しない。

### 10.2 文言決定の正本

```text
ResolvedTailParameters
  -> SelectedEventEditorState
       - effect_notice_header
       - effect_notice_lines
       - slope_helper_text
       - slope_enabled（既存）
  -> RightPane effect notice / helper controls

MainFrame._selected_event_notice
  -> operation_notice argument
  -> RightPane.st_selected_event_notice
```

- coreは日本語表示文を持たない。
- pure GUI adapterが日本語の効果noticeと通常補助文を決定する。
- RightPaneは渡された文を表示するだけとする。
- MainFrameは効果notice条件を再判定せず、操作noticeとの文字列結合も行わない。

### 10.3 canonical state

- noticeはcanonical stateではない。
- notice文字列をUiStateへ保存しない。
- noticeをfingerprint、report、VMD writer inputへ含めない。
- canonical adjustment snapshotは現行どおり設定値を保持する。

## 11. テスト方針

### 11.1 pure core

- 次shapeなしでは `available_extension_frames=None`。
- 次shapeが近い場合に利用可能フレーム数が決定的である。
- 指定5 / 5、利用可能2で反映2 / 0となる。
- metadata追加前後でcontrol pointが同一である。

### 11.2 pure editor adapter

- 設定値と反映値が一致する場合はnoticeなし。
- global parameter由来、event個別override由来の両方で同じnotice条件となる。
- 開口保持だけが制限された場合の文言。
- 閉口スムーズだけが制限された場合の文言。
- 閉口スムーズ0で傾斜比が作用しない場合の文言。
- noticeに `tail`、`clamp`、`midpoint`、`snapshot`、`resolver` が含まれない。
- stale identity、unknown event、metadata欠落はfail closed。
- 閉口スムーズの設定値が0の場合は通常補助文だけとなる。
- 閉口スムーズの設定値が1以上で実際の反映が0の場合は効果noticeだけとなり、通常補助文と重複しない。

### 11.3 wx / MainFrame

- `EVT_SPINCTRL` から開口保持がsnapshotとPreviewへ反映される。
- `EVT_SPINCTRL` から閉口スムーズがsnapshotとPreviewへ反映される。
- `EVT_SPINCTRLDOUBLE` から傾斜比がPreview midpoint値へ反映される。
- 反映量制限時にnoticeが表示される。
- start / end変更で利用可能間隔が増えた場合、noticeが更新または消去される。
- reset selected、selection変更、workspace resetで古いnoticeが残らない。
- Busy / stale requestでnoticeが変わらない。
- 効果noticeとB5対応待ちの操作noticeが同時表示される。
- 効果noticeとtail cleanupの操作noticeが同時表示される。
- 効果noticeの消去が操作noticeを消去しない。
- selection変更で効果noticeが再構築され、操作noticeは既存lifecycleどおり更新または消去される。
- 効果noticeのheaderだけがboldで、detailsはboldではない。
- 通常補助文がattention効果noticeとは異なる通常またはmuted色で表示される。
- 各noticeと補助文に同じ行が重複しない。
- light / dark themeでattention表示が判読できる。
- 右paneを狭くしても縦scrollでnotice全文へ到達できる。

### 11.4 関連回帰

最低限、次を実行する。

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_ms21_b4_selected_event_editor.py tests\test_wx_ms21_b4_selected_event_editor.py -q
.\.venv\Scripts\python.exe -m pytest tests\test_ms21_b2_effective_shape_plan.py tests\test_ms21_b2_event_adjustment.py tests\test_ms21_b2_shape_adapters.py -q
.\.venv\Scripts\python.exe -m pytest tests\test_ms21_b3_selection_commit.py tests\test_ms21_b3_preview_hit_test.py tests\test_ms21_b3_pipeline_preview_integration.py tests\test_wx_ms21_b3_preview_selection.py -q
.\.venv\Scripts\python.exe -m pytest tests\test_wx_ms16_b3_right_pane.py tests\test_ms20_b3_right_pane_info.py tests\test_wx_ms15_b5_state_theme.py -q
.\.venv\Scripts\python.exe -m pytest tests\test_ms20_b2_output_diagnostics.py tests\test_ms20_b3_output_diagnostics_adapter.py tests\test_ms20_b5_warning_save_policy.py -q
.\.venv\Scripts\python.exe -m pytest tests\test_pipeline_and_vmd.py -q
.\.venv\Scripts\python.exe -m pytest tests -q
.\.venv\Scripts\python.exe -m compileall src tests
git diff --check
```

pass表示、failure / error / fatal、process exit codeを分離して記録する。

### 11.5 ユーザー手動GUI確認

1. 次の口形が近いeventを選択する。
2. 開口保持と閉口スムーズを大きい値へ変更する。
3. 設定値と実際の反映値、および制限理由が日本語で表示される。
4. 閉口スムーズが0の場合、傾斜比が現在のPreviewへ反映されない理由が表示される。
5. 次の口形まで余裕があるeventでは、noticeなしで効果が反映される。
6. start / endを変更して間隔を増やすと、noticeとPreviewが更新される。
7. Zoom In後も表示内容とshape変化が一致する。
8. selection変更、reset、cancel、theme変更で古いnoticeや表示崩れが残らない。

## 12. 受け入れ条件

- 一般ユーザーが内部契約を知らなくても、補正が一部だけ反映された理由を画面から理解できる。
- global / event個別にかかわらず、設定値と実際の反映値が異なる場合、その両方が数値付きで表示される。
- 閉口スムーズが作用しない場合、傾斜比も作用しないことが明示される。
- noticeに禁止した内部用語が表示されない。
- 設定値と反映値が一致する場合、不要なnoticeを表示しない。
- noticeは非モーダルであり、操作を妨げない。
- noticeはtheme別attention色を使用し、ERROR表示と混同しない。
- 操作noticeと効果noticeが別control・別入力チャネルで共存し、一方の更新・消去が他方を上書きしない。
- 効果noticeのheaderだけがboldで、detailsと通常補助文はboldではない。
- 閉口スムーズの設定値が0の場合の通常補助文と、反映量不足のattention効果noticeを同時表示しない。
- selection、edit、reset、Busy、cancel、failure、workspace resetでnotice lifecycleが正しい。
- resolver semantics、canonical snapshot、Preview control point、saveabilityを変更しない。
- VMD writer、fingerprint、report、Undo / Redo、rollbackを先行実装しない。
- B4限定test、関連回帰、全体testがpassする。
- process exit codeを個別に記録する。
- ユーザー手動GUI確認項目を提示できる。

## 13. リスクと対策

| リスク | 対策 |
| --- | --- |
| 内部用語をそのまま表示してユーザーへ理解を要求する | 一般ユーザー向け表現規則と禁止語testを固定する |
| RightPaneが次shape間隔を再計算してresolverとずれる | core metadataとpure adapterだけを表示判断の正本にする |
| noticeが常時表示されて重要性を失う | 設定値と反映値が異なる場合だけ表示する |
| 保持とスムーズの割当順を暗黙変更する | resolver semanticsを明示的にOut of Scopeへ固定する |
| 反映0の値を自動削除して将来のgroup変更時の意図を失う | canonical snapshotの設定値保持契約を変更しない |
| cleanup、B5待ち、反映制限のnoticeが競合する | 操作noticeと効果noticeを別control・別引数に分離し、共存と個別消去をtestする |
| 既存 `slope_enabled` と新規stateが矛盾する | 傾斜比の作用可否は既存 `slope_enabled` だけを正本にする |
| global parameter由来の制限が説明されない | override flagで分岐せず、両方を「設定値」として比較する |
| 小さいフレーム差が全体表示で判別しにくい | 数値表示を正本とし、手動確認ではZoom Inを併用する |
| slope disabledの理由が不明なまま残る | 「閉口スムーズが反映されないため」と具体的に表示する |
| 一時修正がB5 writer統合へ拡大する | writer、fingerprint、reportを変更禁止とする |

## 14. 実装時の注意

```text
- 最初にGit状態と未コミットのMS21-B4差分を確認する。
- user-owned差分をrestore、上書き、無断stageしない。
- 実装前に本planと現行code / testを再照合し、P1 / P2 / P3を分類する。
- shell commandは一つずつ実行し、parallel、pipeline、chained commandを使用しない。
- RightPaneで利用可能間隔や反映量を再計算しない。
- coreへ日本語表示文を追加しない。
- 既存slope作用可否を表す重複fieldを追加せず、`slope_enabled` を使用する。
- `_selected_event_notice` / `st_selected_event_notice` は操作notice専用として維持する。
- 効果noticeと通常補助文は `SelectedEventEditorState` から導出し、操作noticeと文字列結合しない。
- ユーザー表示ではglobal / event個別の両方を「設定値」と表現し、「補正値」を使用しない。
- noticeへtail、clamp、midpoint、canonical、snapshot、resolverを表示しない。
- 設定値が反映0でもcanonical adjustmentから自動削除しない。
- hold優先、softness残余割当、shape重複防止を変更しない。
- Info / Warning / Status / reportへnoticeを重複投影しない。
- VMD writer、fingerprint、report、Undo / Redo、failure rollbackを先行実装しない。
- fixed morph、wxPython主系、local-only / no-network、Qt禁止を維持する。
- dependency、package、build、licenseを変更しない。
- 実行していないtest、build、手動GUI確認を通過と報告しない。
```

実装完了報告は次を含める。

```text
1. 確認したファイル
2. 変更したファイル
3. 実装内容
4. 実行したテスト
5. テスト結果
6. ユーザーGUI確認
7. P1 / P2 / P3
8. 仕様からの逸脱
9. 残課題
```
