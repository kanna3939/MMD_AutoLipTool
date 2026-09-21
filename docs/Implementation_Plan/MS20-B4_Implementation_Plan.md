# MS20-B4 Implementation Plan

## 1. 文書情報

- 文書名: MS20-B4 Implementation Plan
- 配置: `docs/Implementation_Plan/MS20-B4_Implementation_Plan.md`
- 対象Block: MS20-B4
- Block名: Live Playback Context
- 実施予定ブランチ: `feature/MS20-implementation`
- 計画基準コミット: `c40162d Implement MS20-B3 RightPane diagnostics info`
- 作成日: 2026-07-16
- 文書ステータス: Complete / Automated and User GUI Verification Complete
- 上位計画:
  - `docs/MS20_and_Beyond_Roadmap.md`
  - `docs/Implementation_Plan/MS20_Block_Breakdown.md`
- 直接の前提契約:
  - `docs/Implementation_Plan/MS20-B1_Implementation_Plan.md`
  - `docs/Implementation_Plan/MS20-B2_Implementation_Plan.md`
  - `docs/Implementation_Plan/MS20-B3_Implementation_Plan.md`
- 正本仕様:
  - `docs/Pipeline_Data_Contract_Specification.md`
  - `docs/GUI_State_Theme_Specification.md`
  - `docs/Error_Handling_Specification.md`

MS20-B4は、B3で実装したRightPane Infoの静的diagnostics表示へ、再生位置、現在フレーム、現在母音を軽量なlive contextとして追加するBlockである。B4は既存の約50ms周期MCI playback callbackを利用するが、timer callbackごとにB2 `OutputDiagnosticsSnapshot` を再生成しない。live contextは表示専用であり、B2 canonical payload、save-state fingerprint、診断severity、保存可否へ含めない。

### 1.1 計画作成時の確認結果

- 2026-07-16にbranch、HEAD、worktree、MS20 routing、B1からB3契約、現行playback code、RightPane、UiState、関連テストを照合した。
- branchは `feature/MS20-implementation`、HEADは `c40162d`、worktreeは計画作成前にcleanだった。
- B3は自動検証とユーザー確認を完了し、Infoの入力・解析・生成・保存可否4セクション、縦scroll、解析中maskを実装済みである。
- `PlaybackController` はWindows MCIを使い、約50ms周期で秒単位位置を `AppController._on_playback_update()` へ通知する。
- `AppController._on_playback_update()` は `UiState.playback_position_sec` を更新して `MainFrame.set_playback_position_sec()` を呼ぶが、`sync_ui_state()` は呼ばない。この経路をB4の軽量更新入口として利用できる。
- `request_playback_play()`、`request_playback_stop()`、playback finish、workspace resetは既に位置を0.0秒へ戻す経路を持つ。
- PauseはUIに存在せず、`request_playback_pause()` もstubである。B4ではPauseを実装しない。
- `VowelTimelinePoint` は `time_sec / vowel / start_sec / end_sec` を持ち、区間は重複し得る。現在母音は表示専用の決定的規則をB4で固定する。
- B2のfingerprint契約は再生位置、frame、現在母音を明示的に除外している。B4はそのDTOとschemaを変更しない。
- B3後の全体テストは406件pass表示、failure / error表示なし、既知wx終了処理由来のprocess exit code 1である。B4計画作成時にはコード・テストを実行または変更していない。

### 1.2 Pre-implementation check結果（2026-07-16）

- P1: なし。
- P2: 1件。初稿の「playback labelをconstructor時から常設表示する」方針は、B3で固定したRightPane単体構築直後と `clear_info()` 後の空表示契約に反していた。playback widget自体はconstructorで生成するが、初期labelは空かつ非表示とし、MainFrame初回 `sync_ui_state()` でdefault `[再生]` を表示する。`clear_info()` はstatic Infoとplayback表示の双方を空表示へ戻し、workspace resetはその後のstate同期でdefault `[再生]` を再表示する契約へ修正した。
- P3: 2件。非有限位置を0.0へ正規化した直後に0秒eventを解決すると誤った母音を表示し得るため、非有限／float化不能値では位置とframeだけを0へ戻し、現在母音は必ず `None` とする契約を追加した。また、停止後に遅延した位置callbackが届いても `is_playing=False` によりdefault表示を維持する回帰testを明記した。
- 現行 `MainFrame.set_playback_position_sec()` は軽量更新入口として利用可能であり、`src/gui_wx/app_controller.py` を主変更へ昇格する必要はない。
- 上記はproduction code・testを変更せず、本書とMS20 routing文書の計画契約だけへ反映した。
- 実装前チェック時点の現行前提検証としてplayback / B3 RightPane / MS16 RightPane / workspace reset 34件、およびB2 diagnostics / UiState / late worker 21件を実行し、双方とも全件pass表示、process exit code 0だった。この時点ではB4 production codeが未実装だったため、B4新規testは未実施だった。実装後の結果は1.4へ記録する。

### 1.3 実装着手前の再チェック結果（2026-07-16）

- P1: なし。
- P2: 1件。新規playback labelについて、正本GUI仕様が必須とするLight / Dark / System theme追従がテスト方針・手動確認・受け入れ条件に明記されていなかった。通常の `text_fg` へ追従し、bold／orange／severity色を使わないことをB4 GUI test、手動確認、受け入れ条件へ追加して解消した。
- P3: 1件。`docs/MS20_and_Beyond_Index.md` の現在HEADがB3実装コミット `c40162d` のままだったため、B4計画コミット `2df59c2` へ更新して解消した。
- `ThemeManager.apply_theme()` はwindow tree内の全 `wx.StaticText` へ `palette.text_fg` を再帰適用する。B4 playback labelはこの既存経路を利用し、専用色処理を追加しない。
- 計画指定のRightPane / playback / Preview回帰28件、diagnostics / UiState / reset / late worker回帰29件は全件pass表示、process exit code 0だった。

### 1.4 実装・自動検証結果（2026-07-16）

- 新規 `src/gui_wx/playback_context.py` にwx非依存の `PlaybackInfoContext`、位置／frame正規化、現在母音resolver、固定4行formatterを実装した。
- `RightPane` にB3 static Infoと分離したplayback label、set / clear / test取得helperを追加した。constructorと `clear_info()` 直後の空表示、MainFrame初回同期後のdefault表示、timer経路のLayout / FitInside非呼出しを維持した。
- `MainFrame.sync_ui_state()` と `set_playback_position_sec()` から専用 `_sync_playback_context()` へ接続し、B2 snapshot、B3 formatter、Preview再構築をtimer経路へ持ち込まなかった。
- 半開区間、gap、区間外、overlap tie、0長event、invalid event、非有限位置、play / stop / finish / failure / reset、停止後遅延callback、Light / Dark / System theme追従を自動testへ固定した。
- B4新規24件、RightPane / playback / Preview回帰28件、diagnostics / UiState / reset / late worker回帰29件、viewport回帰8件は全件pass表示、process exit code 0だった。
- 全体430件は全件pass表示、failure / error表示なし、既知wx終了処理由来のprocess exit code 1だった。
- production code上の計画逸脱、新規依存、MCI / Pause / Preview / Warning / save policy / report / package変更はない。
- 2026-07-16にユーザーからGUI確認完了・問題なしと報告された。B4は実装、自動検証、ユーザーGUI確認まで完了し、次作業はMS20-B5 Implementation Planの策定である。

## 2. 背景

MS20-B3では、`OutputDiagnosticsSnapshot` から次の4セクションをRightPane Infoへ表示する基盤を実装した。

1. `[入力]`
2. `[解析]`
3. `[生成]`
4. `[保存可否]`

B3の表示はworkspace状態の同期時に再生成する静的diagnosticsであり、再生timer callbackでは更新しない。これはB2 snapshotとfingerprintへ一時的な再生状態を混入させないための意図的な境界である。

一方、現行再生経路は次の状態を既に保持・通知している。

- `UiState.is_playing`
- `UiState.playback_position_sec`
- `UiState.current_timing_plan`
- `PlaybackController` から約50ms周期で通知される位置
- Waveform / Previewへ渡す `MainFrame.set_playback_position_sec()`
- stop / finish / reset時の0.0秒復帰

B4では、この既存経路にRightPane表示だけを接続する。MCI操作、timer周期、Waveform / Preview cursor、viewport auto-followは変更しない。

### 2.1 現行実装上の制約

- `MainFrame.sync_ui_state()` はB2 snapshotを生成するため、timerごとの呼出しには使用しない。
- B3の `RightPane.set_info_snapshot()` は静的4セクションを所有し、live値を埋め込まない。
- `RightPane.get_info_text()` はB3 snapshot表示のテスト用契約として維持し、B4 live contextを混ぜない。
- `UiState.playback_position_sec` はfloat秒、VMDと診断のframe基準は `VMD_FPS = 30` である。
- `VowelTimelinePoint.start_sec / end_sec` はイベント区間であり、隣接・gap・重複・0長区間を取り得る。
- 音声は解析前でも再生可能である。その場合も秒とframeは表示し、現在母音だけを `(なし)` とする。

## 3. 目的

- RightPane Infoへ独立した `[再生]` セクションを追加する。
- 再生中、再生位置を小数第2位までの秒で表示する。
- 既存VMD 30fps契約で現在フレームを表示する。
- 有効なtiming planがある場合、現在位置に対応する母音を表示する。
- gap、区間外、解析前、停止中は現在母音を `(なし)` とする。
- play、timer update、stop、finish、playback failure、workspace resetで表示を正しく更新する。
- timer更新ではlive labelだけを変更し、B2 snapshot生成、fingerprint、静的Info、Warning、Preview変換を再実行しない。
- B5以降がB4 live contextをdiagnostics snapshotやsave confirmationへ誤接続しない責務境界を固定する。

## 4. In Scope

- wx非依存のplayback表示context DTO
- 秒、frame、現在母音を解決するpure helper
- `VMD_FPS` を用いた既存規則と同じframe換算
- timeline intervalの境界、gap、重複、0長区間に対する現在母音解決
- `[再生]` セクションの固定文言と表示format
- RightPaneのlive context専用labelと更新helper
- `MainFrame.set_playback_position_sec()` からの軽量更新
- `MainFrame.sync_ui_state()` からの初期・非timer同期
- play / stop / finish / playback failure / resetの既存経路との統合確認
- snapshot builderをtimer更新で呼ばないことの回帰テスト
- playback位置だけでB2 fingerprintとB3静的Infoが変化しないことの回帰テスト
- B4新規test、既存playback / RightPane / reset回帰
- playback labelのLight / Dark / System theme追従回帰
- B4計画・routing文書の実施結果同期

## 5. Out of Scope

- `PlaybackController` のMCI command、timer周期、temp WAV処理の変更
- Pauseボタン、pause state、seek、scrub、loop、再生速度変更
- Waveform / Preview cursor、viewport auto-follow、zoom動作の変更
- Preview segmentまたはVMD morph値を時刻ごとに補間して「支配的モーフ」を厳密計算する機能
- 複数の同時母音を列挙する表示
- selected eventと現在母音の自動同期
- event選択、編集、Undo / Redo
- B2 `OutputDiagnosticsSnapshot`、canonical payload、fingerprint schemaの変更
- B3 adapterによるsnapshot生成規則の変更
- Warning表示、failure保持、severity連動save policy、確認済みfingerprint保持
- diagnostic report出力
- `UiState` へのplayback context DTO追加または永続化
- settings保存、履歴、package、build、release、license変更
- Qt / PySide6、外部通信、network service、新規依存関係

## 6. 前提条件

- 実装開始時に `feature/MS20-implementation`、HEAD、worktreeを再確認する。
- B3実装コミット `c40162d` を直接の基準とする。
- B3の静的Info4セクション、scroll、再解析attention表示を維持する。
- B1 / B2で固定した12 diagnostic code、severity、canonical payload、fingerprint schemaを変更しない。
- fixed morphは `あ / い / う / え / お` のままとする。
- `VMD_FPS` は `src.vmd_writer` の公開定数を参照し、30を別定数として重複定義しない。
- `UiState.playback_position_sec` と `is_playing` を再生状態の正本とする。
- 現在母音の参照元は、有効な `UiState.current_timing_plan.timeline` に限定する。
- `analysis_result_valid=False`、`analysis_pending_rebuild=True`、planなし、timeline空の場合、現在母音を表示しない。
- MCI callbackはUI thread上のwx timer経路であり、B4で新規threadやlockを追加しない。
- playback位置はMCIから非負のミリ秒文字列として得る。pure helperは防御的に負値を0.0へ正規化し、非有限／float化不能値は位置0.0、frame 0、母音なしへfail-softで戻す。
- B4 pre-implementation checkは2026-07-16に完了し、P1なし、P2 1件、P3 2件を計画内で解消済みである。

## 7. 対象ファイル

### 7.1 主変更

| ファイル | 変更内容 |
| --- | --- |
| 新規 `src/gui_wx/playback_context.py` | wx非依存DTO、秒／frame正規化、現在母音解決、`[再生]` 表示formatter |
| `src/gui_wx/right_pane.py` | B3静的Infoと分離したplayback context label、set / clear helper、wrap対応 |
| `src/gui_wx/main_frame.py` | timer入口と通常syncからplayback contextを更新する軽量helper |

### 7.2 テスト

| ファイル | 変更内容 |
| --- | --- |
| 新規 `tests/test_ms20_b4_playback_context.py` | pure resolver、表示format、timer軽量更新、play / stop / finish / reset、snapshot非再生成を検証 |
| `tests/test_ms20_b3_right_pane_info.py` | B3静的InfoとB4 live contextの分離、playback位置変更で静的部分が不変である期待を明確化 |
| `tests/test_wx_ms16_b3_right_pane.py` | playback context helper追加後も5タブと既存helperが維持されることを確認。必要な期待値だけ更新 |

既存testのassertion削除、skip追加、期待値緩和は行わない。B4による表示追加に直接必要な期待値だけを更新する。

### 7.3 関連確認のみ

- `src/gui_wx/playback_controller.py`
- `src/gui_wx/app_controller.py`
- `src/gui_wx/ui_state.py`
- `src/gui_wx/preview_panel.py`
- `src/gui_wx/output_diagnostics_adapter.py`
- `src/core/output_diagnostics.py`
- `src/core/preview_transform.py`
- `src/vmd_writer/writer.py`
- `tests/test_wx_ms15_b3_playback.py`
- `tests/test_wx_ms15_b2_preview.py`
- `tests/test_ms20_b2_output_diagnostics.py`
- `tests/test_ms19_b8_workspace_reset.py`
- `tests/test_ms17_b8_late_worker_result_discard.py`
- `tests/gui_wx/test_viewport_controller.py`

pre-implementation checkで現行callbackを利用できないことが判明した場合だけ `src/gui_wx/app_controller.py` の主変更化を再判定する。計画作成時点では、既存 `MainFrame.set_playback_position_sec()` が必要な入口を提供しているため、AppController変更は予定しない。

### 7.4 計画・実施結果の文書

- 新規 `docs/Implementation_Plan/MS20-B4_Implementation_Plan.md`
- B4 routingに限定した `docs/MS20_and_Beyond_Index.md`
- 次作業同期に限定した `docs/MS20_and_Beyond_Roadmap.md`
- B4状態と責務補正に限定した `docs/Implementation_Plan/MS20_Block_Breakdown.md`

B4実装中にREADME、配布用readme、`docs/repo_milestone.md`、`docs/Version_Control.md`、正本仕様を変更しない。MS20全体の仕様・ユーザー文書同期はB7が所有する。

## 8. 実装方針

### 8.1 B3 snapshotとB4 live contextを構造的に分離する

B4は `OutputDiagnosticsSnapshot` を拡張しない。新規wx非依存moduleに、次の表示専用DTOを置く。

```python
@dataclass(frozen=True)
class PlaybackInfoContext:
    is_playing: bool
    position_sec: float
    frame_no: int
    current_vowel: str | None
```

field名は実装前チェックで既存命名と再照合してよいが、意味は次に固定する。

- `is_playing`: `UiState.is_playing` の表示用copy
- `position_sec`: finiteかつ0.0以上へ正規化した現在位置。停止中は0.0
- `frame_no`: `round(position_sec * VMD_FPS)` を0以上へ制限した整数
- `current_vowel`: 現在位置に対応する固定母音。該当なしは `None`

非有限／float化不能な位置は、表示値を0.0秒／frame 0へ戻しても0秒eventのactive判定には使用せず、`current_vowel=None` とする。`is_playing` はUiStateのcopyを維持し、入力異常を再生停止へ読み替えない。

DTOはUiState、wx widget、filesystem、MCI、B2 snapshotをimportしない。

### 8.2 秒とframeの正規化

frame換算は次に固定する。

```text
normalized_position_sec = 0.0 if stopped or invalid else max(position_sec, 0.0)
frame_no = max(0, round(normalized_position_sec * VMD_FPS))
```

- `int(position * 30)` の切り捨てを新設しない。
- `pipeline._seconds_to_frame()` のprivate helperをimportしない。
- B2の最大frameとwriterが使用する `round` / `VMD_FPS` 契約に合わせる。
- NaN、positive / negative infinity、float化不能値はlive表示で例外を上げず0.0へ戻し、現在母音を解決しない。
- 表示は `0.00 秒` のように小数第2位固定とする。

### 8.3 現在母音の解決規則

現在母音はVMD出力値の厳密な補間結果ではなく、timing planのイベント区間に基づく表示用contextである。次の規則を固定する。

1. 停止中は常に `None`。
2. `analysis_result_valid` でない、再解析待ち、planなし、timeline空の場合は `None`。
3. 通常区間は半開区間 `start_sec <= position_sec < end_sec` でactive判定する。
4. これによりevent終端から次event開始までのgapでは直前母音を残さない。
5. 次eventが同じ時刻から始まる場合、境界時刻では次eventを候補にする。
6. `start_sec == end_sec` の0長eventは、現在frameとeventの `time_sec` を換算したframeが一致する場合だけ候補にする。
7. 複数区間が重なる場合、`abs(position_sec - point.time_sec)` が最小のeventを選ぶ。
8. 距離が同じ場合は `time_sec` が後のevent、それも同じ場合はtimeline indexが後のeventを選ぶ。
9. fixed morph以外、非有限時刻、不正区間、想定外objectはlive表示候補から除外し、timer callbackを失敗させない。
10. timeline自体をsort、copy back、変更しない。

重複解決規則は表示の決定性だけを保証する。実際のMMD上では複数モーフが同時に非0となり得るため、「現在母音」を支配的モーフの保証とは表現しない。

### 8.4 `[再生]` セクション契約

B3の4セクションの後に、MainFrame初回同期以降は常設となる第5セクションとして次を表示する。RightPane単体構築直後と `clear_info()` 直後はB3契約どおりInfo全体を空表示とし、default `[再生]` はMainFrameのstate同期だけが設定する。

```text
[再生]
再生位置: 0.00 秒
現在フレーム: 0
現在母音: (なし)
```

再生中は値だけを更新する。

```text
[再生]
再生位置: 1.23 秒
現在フレーム: 37
現在母音: あ
```

- 停止中、終了後、reset後は0.00秒、0frame、`(なし)` に戻す。
- 解析前に音声だけを再生した場合、秒とframeは更新し、母音は `(なし)` とする。
- gap、区間外、無効planでは母音だけを `(なし)` とする。
- `[再生]` に診断件数、severity、fingerprint、saveabilityを表示しない。
- current vowelへbold、orange、severity色を付けない。B3の再解析attention表示と混同しない。
- playback label全体は `ThemeManager` の通常 `text_fg` に追従し、専用foreground colourや専用font weightを設定しない。

### 8.5 RightPane ownership

RightPaneはcontextを再計算せず、受け取ったDTOまたはformat済み文字列だけを表示する。

追加helper候補:

```python
set_playback_context(context: PlaybackInfoContext) -> None
clear_playback_context() -> None
get_playback_context_text() -> str
```

契約:

- playback labelはB3 `st_info`、再解析専用label、`st_info_suffix` と別widgetにする。
- `set_info_snapshot()` はplayback labelを上書きしない。
- `get_info_text()` はB3静的Infoだけを返す現行テスト契約を維持する。
- playback label widgetは固定4行用としてconstructor時に生成するが、labelは空かつ非表示とし、RightPane単体構築直後の空表示を維持する。
- MainFrame初回 `sync_ui_state()` の `set_playback_context()` でwidgetを表示し、以後のtimer更新では表示／非表示やsizer構造を変えない。初回表示時の `Layout()` / `FitInside()` は非timer同期として1回許可する。
- timer更新では文字列が変わった場合だけ `SetLabel()` と局所 `Refresh()` を行う。
- timerごとに `Wrap()`、`Layout()`、`FitInside()`、Notebook再構築を行わない。
- panel size変更時だけ既存 `_on_size()` / `_update_wrap()` 経路でplayback labelをwrapする。
- `clear_playback_context()` はlabelを空にしてwidgetを隠す。
- `clear_info()` はB3 static Infoに加えて `clear_playback_context()` を呼び、RightPane全体の空表示契約を維持する。
- workspace resetは `clear_info()` だけで完了扱いにせず、その後のMainFrame state同期からdefault playback contextを再表示する。

### 8.6 MainFrameの軽量更新経路

MainFrameにplayback context構築・反映用のprivate helperを追加する。

```text
_sync_playback_context()
  ├─ UiState.is_playing / playback_position_secを読む
  ├─ 有効なcurrent_timing_plan.timelineだけを選ぶ
  ├─ pure resolverを呼ぶ
  └─ RightPane.set_playback_context()を呼ぶ
```

接続点:

- `sync_ui_state()`: static snapshot同期後に1回呼び、初期、input変更、analysis結果、play失敗、stop、resetを反映する。
- `set_playback_position_sec()`: Waveform / Preview cursor更新後に `_sync_playback_context()` だけを呼ぶ。

timer callbackでは `AppController._on_playback_update()` がUiStateを先に更新してから `set_playback_position_sec()` を呼ぶ現行順序を維持する。B4はAppControllerからRightPaneへ直接アクセスしない。

### 8.7 lifecycle別の表示

| 状態 | 秒 / frame | 現在母音 | 更新入口 |
| --- | --- | --- | --- |
| RightPane単体構築直後 / `clear_info()` 直後 | 非表示 | 非表示 | RightPane helper契約 |
| 起動直後 | `0.00 / 0` | `(なし)` | 初回 `sync_ui_state()` |
| 音声読込済み・未再生 | `0.00 / 0` | `(なし)` | input同期 |
| 解析前の再生中 | live | `(なし)` | `set_playback_position_sec()` |
| 有効planの再生中・event内 | live | 解決した固定母音 | timer軽量更新 |
| 有効planの再生中・gap / 区間外 | live | `(なし)` | timer軽量更新 |
| 再生失敗 | `0.00 / 0` | `(なし)` | play failure後の `sync_ui_state()` |
| Stop | `0.00 / 0` | `(なし)` | stop経路 |
| 自然終了 | `0.00 / 0` | `(なし)` | finished → stop経路 |
| analysis開始 | `0.00 / 0` | `(なし)` | 既存の再生停止＋sync |
| parameter / input変更 | `0.00 / 0` またはlive位置 | 無効planなら `(なし)` | state同期 |
| workspace reset | `0.00 / 0` | `(なし)` | stop＋reset＋sync |

Pauseは現行未実装のため状態表へ追加しない。

### 8.8 performanceとfingerprint分離

- timer callbackはB2 snapshot builderを呼ばない。
- timer callbackはB3 formatterを呼ばない。
- timer callbackはpreview dataを再構築しない。既存cursor更新だけを維持する。
- `PlaybackInfoContext` をUiStateへ保存しない。
- playback labelや表示文字列をsnapshot入力へ読み戻さない。
- 再生秒、frame、現在母音をcanonical payloadへ追加しない。
- B5の確認済みfingerprintは再生だけで無効化しない。

### 8.9 compatibility

- `PlaybackController` の公開APIとMCI backendを変更しない。
- `AppController._on_playback_update()` のcallback順序を変更しない。
- `MainFrame.set_playback_position_sec()` の引数とWaveform / Preview cursor動作を維持する。
- `UiState` fieldを追加・削除しない。
- B3の4セクション内容、再解析attention色、scroll、5タブを維持する。
- B2 core DTO、diagnostic item、fingerprint、saveabilityを変更しない。
- fixed morph、VMD writer output、Preview shapeを変更しない。
- input audio、analysis WAV、MMD-use WAVの3役を混同しない。

## 9. 詳細ステップ

### Step 1: 実装開始状態を再確認する

- branch、HEAD、worktreeを確認する。
- B4 plan、B3実装、Block Breakdown、正本仕様を再読する。
- `PlaybackController`、`AppController`、`MainFrame`、`RightPane`、UiState、既存playback testを照合する。
- pre-implementation checkのP1 / P2 / P3を記録し、P1 / P2を解消する。

### Step 2: playback contextのpure契約を追加する

- 新規 `src/gui_wx/playback_context.py` を追加する。
- frozen DTO、位置正規化、frame換算、現在母音resolver、formatterを実装する。
- wx、UiState、MCI、filesystemへ依存させない。
- fixed morphと `VMD_FPS` は既存公開定数を参照する。

### Step 3: 境界・重複・異常値を単体テストする

- stopped、playing、負値、NaN / infinityを確認する。
- NaN / infinity / float化不能位置を0秒eventの母音解決へ流用しないことを確認する。
- 0.00、1/30秒、1.23秒、frame半値境界を確認する。
- interval開始、終端、隣接、gap、前後区間外を確認する。
- 0長event、overlap、同距離tieを確認する。
- unsupported morph、不正objectでlive更新が失敗しないことを確認する。

### Step 4: RightPaneへ常設live sectionを追加する

- B3静的Info widgetと別のplayback labelを追加する。
- default、set、clear、test取得helperを追加する。
- constructorと `clear_info()` 直後はInfo全体を空表示とし、MainFrame初回同期でdefault sectionを表示する。
- 固定行数と既存scroll / wrapを維持する。
- timer更新でlayout全体を再計算しない。

### Step 5: MainFrameへ軽量同期を接続する

- `_sync_playback_context()` を追加する。
- `sync_ui_state()` から初期・lifecycle表示を同期する。
- `set_playback_position_sec()` からlive labelだけを同期する。
- `build_output_diagnostics_snapshot_from_ui_state()` をlive更新経路から呼ばない。

### Step 6: lifecycle回帰を追加する

- play前、再生開始、timer update、stop、finish、失敗、resetを確認する。
- 解析前再生では母音なし、解析済み再生ではevent内母音ありを確認する。
- gapと区間外で直前母音が残らないことを確認する。
- B3静的Infoがtimer更新で変化しないことを確認する。

### Step 7: fingerprint非影響を固定する

- playback位置変更前後のB2 fingerprintが同じであることを既存B2契約と再照合する。
- timer update中にsnapshot builderが呼ばれないことをmockで確認する。
- `PlaybackInfoContext` がB2 DTO、canonical payload、UiStateへ追加されていないことを確認する。

### Step 8: 段階的回帰を実行する

1. B4 pure / GUI test
2. B3 adapter / RightPane回帰
3. MS15 playback / Preview回帰
4. B2 diagnostics / B8 reset回帰
5. 指定限定回帰
6. 全tests

pass表示、failure / error、process exit codeを分けて記録する。

### Step 9: 手動GUI確認を行う

- 解析前と解析後の再生を確認する。
- event内、gap、stop、自然終了、resetを確認する。
- Info scroll、再解析attention、Waveform / Preview cursor、viewport追従の回帰を確認する。
- 実施していない場合は未実施と報告する。

### Step 10: B4実施結果を同期する

- B4 planへ実装、テスト、手動確認、逸脱、残課題を記録する。
- Index、Roadmap、Block Breakdownを実到達状態へ同期する。
- B5 Planningへ進める状態かを明記する。

## 10. 状態遷移 / データ契約

### 10.1 B4データフロー

```text
Windows MCI
  └─ PlaybackController._on_timer()
       └─ update_callback(position_sec)
            └─ AppController._on_playback_update()
                 ├─ UiState.playback_position_sec = position_sec
                 ├─ MainFrame.set_playback_position_sec(position_sec)
                 │    ├─ Waveform / Preview cursor更新（既存）
                 │    └─ MainFrame._sync_playback_context()（B4）
                 │         ├─ UiState.is_playing / valid plan参照
                 │         ├─ pure resolver
                 │         └─ RightPane.set_playback_context()
                 └─ Viewport auto-follow（既存）
```

B2 snapshot builderとB3 formatterはこのlive経路に含めない。

### 10.2 静的Infoとlive Infoのownership

```text
B3 static ownership
  OutputDiagnosticsSnapshot
    └─ [入力] [解析] [生成] [保存可否]

B4 live ownership
  UiState playback fields + valid timing plan
    └─ [再生]
```

- B3 static値はworkspace / analysis / parameter同期で更新する。
- B4 live値はtimerとplayback lifecycleで更新する。
- B4はB3 labelをparseしない。
- B5 / B6はB4 labelをsnapshotまたはreportへ取り込まない。

### 10.3 snapshot / fingerprint非影響

次をB2入力へ追加しない。

- `is_playing`
- `playback_position_sec`
- `frame_no`
- `current_vowel`
- playback label text

同じinput、timing plan、writer parameter、diagnosticsであれば、再生前、再生中、stop後の `save_state_fingerprint` は同一である。

### 10.4 stop / finish / reset

```text
Stop
  ├─ PlaybackController.stop()
  ├─ is_playing = False
  ├─ playback_position_sec = 0.0
  ├─ cursor clear / 0.0通知
  └─ playback context = default

Natural Finish
  └─ request_playback_stop()へ合流

Workspace Reset
  ├─ request_playback_stop()
  ├─ UiState.reset_workspace()
  └─ sync_ui_state()でstatic / live双方を初期化
```

### 10.5 B5以降への引き継ぎ

- B5はWarningとsave policyを実装するが、再生位置だけで確認済みfingerprintを破棄しない。
- B5がsnapshotをworkspaceへ保持しても、B4 contextは別のephemeral表示とする。
- B6 reportへ再生位置、frame、現在母音を追加しない。
- B7はstop、reset、late callback、input変更でstatic / live双方が古く残らないことを横断確認する。

## 11. テスト方針

### 11.1 B4 pure test

新規 `tests/test_ms20_b4_playback_context.py` で少なくとも次を確認する。

- stoppedは位置0.00、frame 0、母音なしになる。
- playing 1.23秒は既存30fps `round` 規則でframe 37になる。
- 負値、NaN、infinityは表示を壊さず0.0へ戻る。
- NaN / infinity / float化不能位置では0秒eventを現在母音として誤表示しない。
- interval開始はactive、終端はinactiveになる。
- 隣接eventの共通境界では次eventを選ぶ。
- gapで直前eventを残さない。
- timeline前後の区間外は母音なしになる。
- overlapではpeak時刻が近いeventを選ぶ。
- overlap tieは後のeventを選ぶ。
- 0長eventは同一frameだけ候補になる。
- fixed morph以外と不正eventを無視する。
- formatterが固定4行、2桁秒、整数frame、`(なし)` を決定的に生成する。

### 11.2 B4 GUI / callback test

- MainFrame初回同期でdefault `[再生]` セクションが表示される。
- RightPane単体構築直後と `clear_info()` 直後はstatic / live双方が空表示になる。
- 解析前playback updateで秒 / frameだけが更新される。
- 有効planのevent内で現在母音が更新される。
- stop / finish / playback failure / resetでdefaultへ戻る。
- stop後の遅延位置callbackではdefault表示を維持し、古い位置や母音を復活させない。
- `set_playback_position_sec()` が既存cursor更新を維持する。
- timer updateでB2 snapshot builderとB3 formatterを呼ばない。
- B3 `get_info_text()` と静的labelがtimer update前後で不変である。
- playback label更新でInfoのvirtual heightと横幅が増減し続けない。
- Light / Dark / System適用後もplayback labelが各paletteの通常 `text_fg` に追従し、bold／orangeにならない。

### 11.3 対象test

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_ms20_b4_playback_context.py
```

想定: pass表示、process exit code 0。

### 11.4 RightPane / playback回帰

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_ms20_b3_right_pane_info.py tests/test_wx_ms16_b3_right_pane.py tests/test_wx_ms15_b3_playback.py tests/test_wx_ms15_b2_preview.py
```

B4後の件数は実装時のcollection結果を記録し、計画段階で固定値を捏造しない。

### 11.5 diagnostics / state回帰

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_ms20_b2_output_diagnostics.py tests/test_wx_ms14_b2_state.py tests/test_ms19_b8_workspace_reset.py tests/test_ms17_b8_late_worker_result_discard.py
```

確認観点:

- playback位置だけでfingerprintが変わらない。
- stop / resetでUiStateが初期化される。
- late worker / analysis callbackが古いlive contextを復活させない。
- B3 static diagnosticsとB4 live contextが分離される。

### 11.6 全体回帰

```powershell
.\.venv\Scripts\python.exe -m pytest tests
```

B3後baselineは406件pass表示、既知wx終了処理由来のprocess exit code 1である。B4実装後はcollection件数、pass / fail / error表示、process exit codeを別々に記録する。baselineと同じ終了コードであっても、新規failure / errorがないことを確認する。

### 11.7 手動GUI確認

1. 起動直後に `[再生]`、0.00秒、frame 0、母音なしが表示される。
2. 解析前に音声を再生すると秒とframeが更新され、母音はなしのままである。
3. 解析後に再生するとevent内で固定母音が更新される。
4. 無音gapまたはevent区間外で直前母音が残らない。
5. Stopで0.00秒、frame 0、母音なしへ戻る。
6. 自然終了でも同じ初期表示へ戻る。
7. 新規作業resetで前作業のlive contextが残らない。
8. live更新中にInfo scroll位置や横幅が不自然に跳ね続けない。
9. Waveform / Preview cursorとviewport auto-followが従来どおり動く。
10. B3再解析attention、Warning、選択イベント、preset、model profileタブが従来どおりである。
11. Light / Dark / System切替後もplayback labelが通常文字色で表示され、再解析attention用のbold／orangeにならない。

手動GUI確認を実施していない場合は未実施と報告する。B4では実MMD確認、build、SmokeLaunch、package確認を実施しない。

実施結果: 2026-07-16にユーザーからGUI確認完了・問題なしと報告された。実MMD、build、SmokeLaunch、package確認はB4範囲外のため実施していない。

### 11.8 文書・差分検証

```powershell
git diff --check
```

実装後はstaged / unstaged / untrackedを確認し、MCI、Pause、seek、Preview transform、B2 schema、Warning、save policy、report、packageの範囲外変更がないことを監査する。

## 12. 受け入れ条件

- wx非依存のplayback context DTO / resolver / formatterが追加されている。
- resolverがUiState、wx、MCI、filesystem、networkへ依存しない。
- frameが既存 `VMD_FPS` と `round` 規則で計算される。
- negative / nonfinite位置でtimer callbackが失敗しない。
- nonfinite / float化不能位置で0秒eventの母音を誤表示しない。
- current vowelがevent interval内だけ表示される。
- gapと区間外で直前母音が残らない。
- adjacent boundary、overlap、0長eventの規則が単体テストで固定されている。
- fixed morph以外を現在母音として表示しない。
- RightPaneに、MainFrame初回同期後は常設される独立した `[再生]` セクションがある。
- RightPane単体構築直後と `clear_info()` 直後はB3の空表示契約を維持する。
- 停止中は0.00秒、frame 0、母音なしを表示する。
- 解析前再生では秒 / frameが更新され、母音はなしになる。
- 有効plan再生では秒 / frame / 母音がlive更新される。
- stop、finish、playback failure、analysis開始、resetでdefaultへ戻る。
- timer updateでB2 snapshot builder、B3 formatter、Layout / FitInsideを呼ばない。
- B3静的4セクションと再解析attention表示が維持される。
- playback labelがLight / Dark / Systemの通常 `text_fg` に追従し、bold／orange／severity色を使用しない。
- Waveform / Preview cursorとviewport auto-followが維持される。
- playback位置だけでB2 fingerprintが変化しない。
- `OutputDiagnosticsSnapshot`、canonical payload、fingerprint schema、UiState fieldを変更していない。
- MCI backend、timer周期、Pause、seek、event選択、Warning、save policy、reportを変更していない。
- B4新規test、指定回帰、全testsのpass表示とprocess exit codeが記録されている。
- 新規依存関係、external communication、build、package、license変更がない。
- B5開始前に解消が必要な未記名の判断事項が残っていない。

## 13. リスクと対策

| リスク | 対策 |
| --- | --- |
| timerごとにsnapshotを再生成してGUI負荷とfingerprint責務が混ざる | `set_playback_position_sec()` からlive context専用helperだけを呼び、builder非呼出しをmock testで固定する |
| RightPane全体を50msごとにLayoutしてscrollが跳ねる | 常設固定行labelを値だけ更新し、timer経路でWrap / Layout / FitInsideを呼ばない |
| constructorからdefault playback表示を出してB3の空表示契約を壊す | widgetは空かつ非表示で生成し、MainFrame初回同期でだけdefaultを表示する。`clear_info()` はstatic / live双方を空にする |
| 新規playback labelだけtheme未追従、または再解析attention色を誤用する | 既存 `ThemeManager` の通常 `StaticText` 適用経路を利用し、Light / Dark / Systemで `text_fg` と通常weightをtestする |
| interval終端後も直前母音が残る | 半開区間とgap testを固定する |
| overlapで結果が実行順依存になる | peak距離、time_sec、indexの順でtie breakを固定する |
| 0長eventが永久に表示される、または一度も候補にならない | 同一VMD frameの場合だけ候補にする |
| 「現在母音」を実際の支配的VMD morphと誤解する | timing interval由来の表示用contextと明記し、補間・複数モーフ評価を範囲外にする |
| 解析前再生でplan参照例外になる | 秒 / frameと母音解決を分離し、planなしは母音なしにする |
| invalid planでtimer callbackが落ちる | live resolverは不正eventをfail-softで除外し、保存契約のfail-closed処理とは分離する |
| nonfinite位置を0秒へ正規化した結果、0秒eventを現在母音として誤表示する | position / frameはdefault化しても母音resolverは実行せず `None` を返す |
| stop直前のtimer callbackが古い母音を復活させる | UiState.is_playingをresolver入力にし、停止中は位置と母音を強制default化する |
| finishとmanual Stopの表示が異なる | finishを既存 `request_playback_stop()` へ合流させる契約を維持する |
| playback位置をfingerprintへ追加してB5確認状態を壊す | B2 DTO / payload非変更とfingerprint不変testを固定する |
| B3 `get_info_text()` にlive値が混ざり既存回帰が不安定になる | static / live labelとtest helperを分離する |
| Pauseまで実装してMCI状態機械が拡大する | 現行stubを維持しB4 Out of Scopeへ明記する |
| VMD_FPSを30として重複定義し将来ずれる | `src.vmd_writer.VMD_FPS` を参照する |
| full suiteのexit code 1を新規failureと誤認する | pass表示、failure / error、process exit codeを分けて記録する |

## 14. Codex 実装時の注意

```text
- コマンドは必ず一つずつ実行し、並列・パイプ・連結実行をしない。
- 実装前にbranch、HEAD、worktree、B4 plan、callback順序を再確認する。
- 未コミット差分はユーザー所有変更として保護する。
- B3 static InfoとB4 live contextを同じsnapshot／formatterへ統合しない。
- RightPane constructor / `clear_info()` からdefault `[再生]` を生成せず、MainFrame初回同期から表示する。
- timer callbackからsync_ui_state()を呼ばない。
- timer callbackからsnapshot builder、B3 formatter、Layout、FitInsideを呼ばない。
- playback位置、frame、現在母音をB2 DTO、fingerprint、UiState永続fieldへ追加しない。
- RightPaneでtimelineを直接解析しない。pure resolverの結果だけを表示する。
- timeline、UiState、VowelTimingPlanを変更しない。
- current vowelを厳密な支配的VMD morphとして表現しない。
- gap、区間外、停止中に直前母音を残さない。
- fixed morph あ / い / う / え / お を変更しない。
- MCI backend、timer周期、temp WAV、Pause、seek、loopを変更しない。
- Waveform / Preview cursor、viewport auto-follow、zoomを変更しない。
- Warning、failure保持、save policy、reportを先行実装しない。
- Qt / PySide6、新規依存、network、background通信を追加しない。
- testを削除・skip・期待値緩和してpassさせない。
- 実施していないGUI、MMD、build、package確認を通過と報告しない。
- pass表示とprocess exit codeを分けて報告する。
```

B4完了報告は次の形式とする。

```text
1. 確認したファイル
2. 変更したファイル
3. 実装内容
4. 実行したテスト
5. テスト結果
6. 仕様から逸脱した点
7. 残課題
```
