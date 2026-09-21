# MS20-B6 Implementation Plan

## 1. 文書情報

- 文書名: MS20-B6 Implementation Plan
- 配置: `docs/Implementation_Plan/MS20-B6_Implementation_Plan.md`
- 対象Block: MS20-B6
- Block名: Diagnostic Report Export
- 実施予定ブランチ: `feature/MS20-implementation`
- 計画基準コミット: `d179ec9 Implement MS20-B5 warning save policy`
- 作成日: 2026-07-17
- 文書ステータス: Implemented / Automated and User GUI Verification Complete
- 上位計画:
  - `docs/MS20_and_Beyond_Roadmap.md`
  - `docs/Implementation_Plan/MS20_Block_Breakdown.md`
- 直接の前提契約:
  - `docs/Implementation_Plan/MS20-B1_Implementation_Plan.md`
  - `docs/Implementation_Plan/MS20-B2_Implementation_Plan.md`
  - `docs/Implementation_Plan/MS20-B3_Implementation_Plan.md`
  - `docs/Implementation_Plan/MS20-B4_Implementation_Plan.md`
  - `docs/Implementation_Plan/MS20-B5_Implementation_Plan.md`
- 正本仕様:
  - `docs/Pipeline_Data_Contract_Specification.md`
  - `docs/GUI_State_Theme_Specification.md`
  - `docs/Error_Handling_Specification.md`

MS20-B6は、B2で導入しB3からB5でInfo、Warning、VMD保存policyへ接続した `OutputDiagnosticsSnapshot` を、ユーザーが明示的に保存できる診断レポートへ変換するBlockである。レポートはRightPane表示文字列を読み戻さず、保存操作時に生成した最新snapshotだけを入力とする。

### 1.1 計画作成時の確認結果

- 2026-07-17にbranch、HEAD、worktree、MS20 routing、B1からB5契約、現行diagnostics core、UiState、MainFrameメニュー、AppController保存入口、既存出力テストを照合した。
- branchは `feature/MS20-implementation`、HEADは `d179ec9`、worktreeは計画作成前にcleanだった。
- `OutputDiagnosticsSnapshot` はinput、analysis、generation、saveability、diagnostic items、fingerprint payload、`save_state_fingerprint` をUI非依存のimmutable DTOとして保持する。
- `MainFrame.build_and_store_output_diagnostics_snapshot()` はinput mode再判定後に最新snapshotを一度生成し、UiStateへ保持できる。
- B5によりInfo、Warning、VMD保存button / menu、controller guardは同一snapshotを使用する。report出力は未実装である。
- 現行Fileメニューには `新規作業...`、TEXT / 音声読み込み、recent files、VMD保存、終了があり、診断レポート保存項目は存在しない。
- 現行VMD保存は `wx.FD_OVERWRITE_PROMPT`、MMD用WAV保存は明示的なYes / No上書き確認を使用する。B6では上書き拒否を単体テスト可能にするため、後者と同じ明示確認方式を採用する。
- `settings_store.py` と `mmd_wav_export.py` には同一directoryの一時ファイルと `os.replace()` を用いた既存の安全な確定パターンがある。
- diagnostics report用module、formatter、writer、save menu、controller action、専用testは存在しない。
- B5完了時点の自動検証記録は、限定testが終了コード0、全体442件＋subtest 7件がpass表示、既知wx終了処理由来のprocess exit code 1である。
- 本計画作成ではproduction code、GUI、test code、依存関係、build設定を変更しない。

### 1.2 計画作成時に固定する判断

- report formatterとatomic writerはwxPython非依存の新規 `src/core/diagnostic_report.py` に分離する。
- formatter APIは明示的な `generated_at` を受け取り、同一snapshotと同一時刻から常に同一文字列を生成する。formatter内部で現在時刻を取得しない。
- `Generated At` はタイムゾーン付きISO 8601、秒精度とする。controllerが `datetime.now().astimezone()` を一度だけ取得して渡す。
- report本文はLF固定、末尾LFあり、UTF-8 BOMなしとする。OS既定改行やlocaleへ依存しない。
- reportはsnapshotの全summary field、saveability、`save_state_fingerprint`、全diagnostic itemを固定順で出力する。
- diagnostic itemの順序は `snapshot.items` をそのまま使用し、GUI側やformatter側でseverity / codeを再計算または再sortしない。
- diagnosticの `identity_context` は安定したJSON表現を1行で出力し、`ensure_ascii=False` と固定separatorを使用する。これはreport全体をJSON化するものではない。
- summary、detail、path等の文字列は改行を正規化する。単一行fieldの制御文字はescapeし、detailの継続行はindentしてsection headerと誤認されないようにする。
- report本文のSource Audio Pathは `snapshot.input_summary.normalized_source_audio_path` を使用する。一方、ユーザー向け既定名の `<base>` と初期保存directoryは、既存adapterのsource audio解決規則をpublic helper化し、元の大小文字を保持した `UiState.selected_audio_input.source_path`、fallbackとして `UiState.selected_wav_path` から解決する。内部解析WAV、TEXT名、VMD出力名から導出しない。
- report保存可否は「UiStateに元入力音声pathと非空stemがある」ことと「Busyでない」ことだけで決める。VMD保存可否、ERROR、WARNING、fingerprint有無では禁止しない。
- `build_diagnostic_report_default_filename()` はsnapshotではなく元入力音声pathを受け取る。report本文だけをsnapshot正本とし、保存dialogのpath / filename決定をsnapshot正規化pathへ依存させない。
- 初期保存directoryは元入力音声pathのparentとする。B6ではreport保存先履歴をUiStateやsettingsへ追加しない。
- report保存path、dialog状態、`Generated At` はsnapshotとfingerprintを変更しない。
- report保存は軽量なローカルTEXT出力のためworker化しない。ただし既存Busy中はmenuとcontroller guardの両方で拒否する。
- 新規toolbar buttonは追加せず、`ファイル > 診断レポート保存...` の専用menuだけを追加する。
- dependency、package、license、固定モーフ、ASR、network、Qt / PySide6は変更しない。

### 1.3 実装前チェック・P2補正・再チェック結果（2026-07-17）

- 初回チェックでP1なし、P2 2件、P3なしを検出した。
- P2-1は、既定名を `normalized_source_audio_path` から生成すると、Windowsの `os.path.normcase()` により元入力音声stemの大小文字を失う問題である。report本文はsnapshot正規化pathを使用し、保存dialogの既定名とdirectoryは既存adapterのsource audio path resolverをpublic helper化してUiStateの元pathから解決する契約へ補正した。
- P2-1の補正に伴い、snapshot builder、MainFrame、AppControllerが同じsource audio path resolverを共有し、`selected_audio_input.source_path` 優先、`selected_wav_path` fallbackの規則を重複実装しないことを固定した。
- P2-2は、Windowsでtemporary file handleを開いたままreadbackまたは `os.replace()` を行う余地があった問題である。binary write、flush、`os.fsync()`、write handle close、別handle readback、readback handle close、`os.replace()` の順序を固定した。
- P2補正後に正本文書、現行DTO、path正規化、UiState、adapter、MainFrame、AppController、既存atomic保存pattern、test、package設定を再照合した。P1 / P2 / P3の残存なしと判定した。
- MS20 diagnostics回帰50件、state / export / reset回帰28件＋subtest 7件、既存output dialog回帰6件、pipeline / VMD回帰12件はすべてpass表示・process exit code 0だった。
- `git diff --check` はprocess exit code 0、新規B6 planの末尾空白は検出なしだった。
- production code、GUI、test code、dependency、build設定は変更していない。
- MS20-B6は本書の範囲で実装着手可能である。

### 1.4 実装・自動検証結果（2026-07-18）

- `src/core/diagnostic_report.py` にwxPython非依存のdefault filename helper、決定的formatter、same-directory temporary fileと `os.replace()` を使うatomic writer、`DiagnosticReportError` を実装した。
- reportはtimezone付き `Generated At`、固定5 section、全diagnostic item、LF、末尾LF、UTF-8 BOMなし、単一空値表現を実装した。
- 元入力音声path resolverを `resolve_source_audio_path_from_ui_state()` としてpublic化し、snapshot builder、MainFrame、AppControllerで共有した。既定名とdirectoryは元path、report本文はsnapshotのnormalized pathを使用する。
- File menuへ `診断レポート保存...` を追加し、入力音声あり／非Busyで有効、ERROR snapshotでも保存可能、WARNING確認なし、入力なし／Busy／reset後はfail closedとした。
- 上書き拒否、dialog cancel、write / verify / replace失敗では既存targetを変更せず、temporary fileをcleanupする。成功・失敗ともsnapshot、timing plan、failure、fingerprint、WARNING確認済み状態を変更しない。
- B6 core 13件、B6 GUI flow 10件、MS20 diagnostics回帰50件、state / export / reset回帰28件＋subtest 7件、既存output dialog回帰6件、pipeline / VMD回帰12件はpass表示・終了コード0だった。
- 全体465件は全件pass表示、failure / error表示なし、既知wx終了処理由来のprocess exit code 1だった。
- `python -m compileall src tests` と `git diff --check` は終了コード0だった。
- dependency、package、license、Qt、network、固定モーフは変更していない。
- 実装・自動検証完了時点では、ユーザー手動GUI確認14項目は未実施だった。

### 1.5 ユーザー手動GUI確認結果（2026-07-18）

- ユーザーから、手動GUI確認14項目はすべて通過し、問題なしと報告された。
- 起動直後／音声読み込み後／Busy中／workspace reset後のmenu状態、TEXTあり／voice_only／ERROR／WARNINGでのreport保存、既定名、UTF-8 BOMなし、固定5 section、上書き／cancel／失敗時保持、theme別判読性を確認済みとする。
- B6はproduction実装、自動検証、ユーザー手動GUI確認まで完了した。

## 2. 背景

MS20-B2からB5で、次の経路が成立している。

```text
UiState + current timing plan + writer parameters
  -> OutputDiagnosticsSnapshot
       -> RightPane Info
       -> RightPane Warning
       -> VMD save action state
       -> VMD save controller guard
```

B6では同じsnapshotを次へ接続する。

```text
explicit File menu action
  -> latest OutputDiagnosticsSnapshot
  -> deterministic diagnostic report formatter
  -> same-directory temporary file
  -> byte verification
  -> atomic replace
  -> <source-audio-stem>_report.txt
```

RightPaneの表示文字列をreportへ転記すると、theme、表示用日本語、解析中mask、live playback context、wrap、tab状態がreport内容へ混入し、B1で固定したUI非依存契約を破る。B6はcore DTOを直接formatし、GUI表示と保存ファイルの正本を分離したまま共通snapshotへ収束させる必要がある。

また、diagnostic reportはVMDそのものではなく、VMD保存不可の理由を確認するためにも使う。そのため、`ERROR` を含むsnapshotをreport保存不可にしてはならない。一方、入力音声がない状態ではB1の `<base>` を決められないため、report保存導線は無効とする。

## 3. 目的

- `OutputDiagnosticsSnapshot` から決定的なplain-text診断レポートを生成する。
- `ファイル > 診断レポート保存...` から `<base>_report.txt` を明示保存できるようにする。
- UTF-8 BOMなし、LF固定、安定section / field順、単一空値表現を保証する。
- 上書き拒否、dialog cancel、書き込み失敗時に既存正常ファイルを壊さない。
- VMD保存不可の `ERROR` を含むsnapshotでもreportを保存できるようにする。
- report保存がworkspace diagnostics state、fingerprint、VMD保存確認状態、解析結果へ副作用を与えないことを固定する。

## 4. In Scope

- UI非依存diagnostic report formatter
- report default filename resolver
- snapshot全sectionとdiagnostic itemsの固定format
- timezone付き `Generated At`
- LF固定、末尾LF、UTF-8 BOMなし
- same-directory temporary fileへの書き込み
- byte-level検証後の `os.replace()` による確定
- 書き込み失敗時のtemporary file cleanup
- `ファイル > 診断レポート保存...` menu
- report menuのBusy／入力音声状態連動
- report保存dialog、`.txt` 自動補完、明示的上書き確認
- AppController report保存入口
- cancel、上書き拒否、format / write / replace失敗のstatusとerror dialog
- `ERROR` / `WARNING` / `INFO` snapshotのreport保存
- B6専用core / GUI flow test
- B2からB5のdiagnostics / state / save回帰
- B6 plan、Index、Roadmap、Block Breakdownの状態同期

## 5. Out of Scope

- JSON / CSV / HTML / Markdown report
- report schemaのversion migration機構
- reportの自動保存
- VMD保存時のreport自動生成・同梱
- MMD用WAV出力との一括保存
- 出力directoryの新規一括管理
- report保存先履歴のUiState / settings永続化
- toolbarへのreport button追加
- RightPaneへのreport preview追加
- reportからsnapshotを復元する機能
- report内容の編集
- reportファイルの再読込
- VMD保存policy、WARNING確認fingerprintの変更
- B7が所有する全input / cancel / reset / late callback横断監査
- README、配布用readme、`repo_milestone.md`、`Version_Control.md` のcloseout更新
- package、build、release、tag、push
- 新規dependency
- Qt / PySide6復活
- 固定モーフ `あ / い / う / え / お` の変更
- 外部クラウドASR、音声外部送信、background通信、Whisper自動download

## 6. 前提条件

- branchが `feature/MS20-implementation` である。
- B5実装コミット `d179ec9` 以降を基準とする。
- worktreeの既存変更を確認し、ユーザー所有変更を保護する。
- B1のreport section、空値、encoding、LF、filename、ERROR保存許可契約を変更しない。
- B2の `OutputDiagnosticsSnapshot` とstable item orderをreportの唯一の入力とする。
- B3のInfo formatter、B4のlive playback context、B5のWarning表示とVMD保存policyをreport formatterへ流用しない。
- report保存操作時に最新snapshotを再生成できる。
- report本文の入力音声pathは `normalized_source_audio_path` を正本とする。保存dialogの既定名とdirectoryは元の大小文字を保持したUiStateのsource audio pathを使用し、内部解析WAVと混同しない。
- 実装前チェックで本計画と現行コード・テストを再照合する。

## 7. 対象ファイル

### 7.1 主変更

| ファイル | 変更内容 |
| --- | --- |
| 新規 `src/core/diagnostic_report.py` | formatter、default filename、atomic writer、report例外 |
| `src/core/__init__.py` | B6 public API export |
| `src/gui_wx/output_diagnostics_adapter.py` | 既存source audio path解決をpublic helper化し、snapshot builder、menu、controllerで共有 |
| `src/gui_wx/main_frame.py` | File menu、action state、save dialog、overwrite確認、event routing |
| `src/gui_wx/app_controller.py` | 最新snapshot取得、保存可否guard、core writer呼出し、status / error処理 |

`src/core/output_diagnostics.py` は原則変更しない。reportに必要な値は現行 `OutputDiagnosticsSnapshot` に揃っている。実装前チェックでDTO不足が実証された場合だけ、B6 reportに必要な最小field追加をP2として再計画する。

`src/gui_wx/ui_state.py` と `src/core/settings_store.py` は原則変更しない。B6ではreport保存先履歴を保持しないためである。

### 7.2 関連確認

- `src/core/output_diagnostics.py`
- `src/gui_wx/ui_state.py`
- `src/gui_wx/right_pane.py`
- `src/gui_wx/theme.py`
- `src/core/settings_store.py`
- `src/core/mmd_wav_export.py`
- `src/gui_wx/analysis_worker.py`
- `src/gui_wx/voice_only_errors.py`
- `README.md`
- `pyproject.toml`
- `MMD_AutoLipTool.spec`
- `build.ps1`

### 7.3 テスト

主追加:

- 新規 `tests/test_ms20_b6_diagnostic_report.py`
- 新規 `tests/test_ms20_b6_report_save_flow.py`

関連回帰:

- `tests/test_ms20_b2_output_diagnostics.py`
- `tests/test_ms20_b3_output_diagnostics_adapter.py`
- `tests/test_ms20_b3_right_pane_info.py`
- `tests/test_ms20_b5_warning_save_policy.py`
- `tests/test_wx_ms14_b2_state.py`
- `tests/test_wx_ms14_b5_export.py`
- `tests/test_wx_ms16_b3_right_pane.py`
- `tests/test_ms19_b7_voice_only_error_handling.py`
- `tests/test_ms19_b8_workspace_reset.py`
- `tests/test_pipeline_and_vmd.py`

既存test fixtureがreport menu追加でMainFrame mock契約に不足する場合は、production契約を弱めずfixtureだけを現行interfaceへ補正する。

### 7.4 文書

- 新規 `docs/Implementation_Plan/MS20-B6_Implementation_Plan.md`
- `docs/Implementation_Plan/MS20_Block_Breakdown.md`
- `docs/MS20_and_Beyond_Index.md`
- `docs/MS20_and_Beyond_Roadmap.md`

README、配布用readme、`repo_milestone.md`、`Version_Control.md` はB6実装時点では変更しない。B7 closeoutでユーザー向け説明と履歴文書の更新要否を判断する。

## 8. 実装方針

### 8.1 core report API

新規moduleは次の責務を持つ。

```python
class DiagnosticReportError(Exception):
    ...

def build_diagnostic_report_default_filename(
    source_audio_path: str | Path | None,
) -> str | None:
    ...

def format_diagnostic_report(
    snapshot: OutputDiagnosticsSnapshot,
    *,
    generated_at: datetime,
) -> str:
    ...

def write_diagnostic_report(
    snapshot: OutputDiagnosticsSnapshot,
    output_path: str | Path,
    *,
    generated_at: datetime,
) -> Path:
    ...
```

- `build_diagnostic_report_default_filename()` は元入力音声pathのstemが非空なら元の大小文字を保持した `<stem>_report.txt`、決定不能なら `None` を返す。
- default filename helperはsnapshotを受け取らない。Windowsの `os.path.normcase()` を通った `normalized_source_audio_path` からユーザー向けfilenameを作らない。
- `format_diagnostic_report()` はfilesystemへ書き込まない。
- `write_diagnostic_report()` はformat、encode、temporary write、verify、replace、cleanupだけを担当し、GUI dialogやstatusを参照しない。
- `DiagnosticReportError` はユーザー向けsummaryと内部原因を分離できる最小例外とする。既存exceptionを隠さず `raise ... from error` でchainする。
- `src/core/__init__.py` から公開し、GUIがprivate helperへ依存しない。

### 8.2 report headerと時刻

固定header:

```text
MMD AutoLipTool Diagnostic Report
Generated At: 2026-07-17T12:34:56+09:00
```

- `generated_at` はtimezone-aware `datetime` を必須とする。
- naive datetimeは黙ってlocal扱いせず `ValueError` とする。
- `isoformat(timespec="seconds")` を使用する。
- microsecondはreportへ出さない。
- formatter内部で `datetime.now()` を呼ばない。
- `Generated At` はfingerprintとsnapshotへ書き戻さない。

### 8.3 sectionとfield順

固定順:

```text
MMD AutoLipTool Diagnostic Report
Generated At: <ISO 8601>

[Input]
Input Mode:
Text Path:
Source Audio Path:
Effective WAV Path:
Text Content Present:
Analysis Text Present:

[Analysis]
Analysis Result Valid:
Analysis Pending Rebuild:
Timing Source:
Anchor Count:
Event Count:
Max Frame:
Timing Warning Present:
Observation Fallback Count:

[Generation]
VMD Model Name:
Closing Hold Frames:
Closing Softness Frames:
Fingerprint Schema Version:

[Saveability]
VMD Save Allowed:
Blocking Codes:
Warning Codes:
Save State Fingerprint:

[Diagnostics]
...
```

- boolはlocale非依存の `true / false` とする。
- intは10進数とする。
- `None`、空code list、空diagnosticsは `(not available)` とする。
- pathはsnapshot内の正規化済み文字列をそのまま出力する。
- `fingerprint_payload` 全内容は出力しない。reportには人間が照合できる `save_state_fingerprint` を出力する。
- section名とfield名は固定し、RightPaneの日本語表示文言変更から独立させる。
- formatterはsnapshot fieldを再計算しない。

### 8.4 diagnostics item形式

各itemを `snapshot.items` 順に次の形で出力する。

```text
Diagnostic 1:
  Severity: ERROR
  Code: analysis_failure
  Phase: pipeline_build
  Summary: ...
  Detail:
    ...
  Identity Context: {"category":"..."}
```

- severityはenum valueのuppercaseを使用する。
- code、phase、summary、detail、identity_contextを含める。
- detailが空なら `(not available)` とする。
- detail内のCRLF / CRはLFへ正規化し、全行を4空白indentする。
- summary等の単一行fieldに改行やtabがある場合は `\n`、`\t` のliteral escapeへ変換する。
- `identity_context` はtuple順を保ち、canonical valueをJSON互換値へ変換して1行出力する。
- `json.dumps(..., ensure_ascii=False, separators=(",", ":"))` を使用し、Python `repr()`、object address、localeへ依存しない。
- formatterはitemの順序をsortし直さない。B2 builderが定めた順序がreport順である。

### 8.5 encodingと改行

- formatterは行配列を `"\n".join(lines) + "\n"` で結合する。
- writerは `text.encode("utf-8")` を使用する。
- `utf-8-sig`、BOM byte `EF BB BF`、platform newline translationを使用しない。
- temporary fileのbytesを読み戻し、期待bytesとの完全一致、UTF-8 strict decode、BOM非存在を確認する。
- 空reportは生成しない。固定headerと全sectionを常に含める。

### 8.6 atomic writer

1. targetを `Path` へ変換する。
2. target parentが既存directoryであることを確認する。
3. targetと同一directoryへ `NamedTemporaryFile(mode="wb", delete=False, ...)` で一意なtemporary fileを作る。
4. UTF-8 bytesを書き、flushする。
5. `os.fsync()` を実行する。
6. `with NamedTemporaryFile(...)` を抜け、temporary file handleを明示的にcloseする。
7. close後に別handleでtemporary bytesを読み戻し、期待bytesとの完全一致、UTF-8 strict decode、BOM非存在を検証する。
8. 検証用handleもcloseした後に `os.replace(temp_path, target_path)` で確定する。
9. 成功時はtarget pathを返す。
10. 例外時は開いているhandleをcloseしたうえでtemporary fileだけを削除し、既存targetを削除・truncateしない。

target parentを自動作成しない。保存dialogが返した既存directoryだけを対象とし、invalid pathは明示失敗とする。Windowsではopen handleがある状態で再読込や `os.replace()` を行わない。

### 8.7 report保存可否

report menuの有効条件:

```text
source_audio_path = resolve_source_audio_path_from_ui_state(UiState)
not UiState.is_busy
and source_audio_path is not None
and Path(source_audio_path).stem is not empty
```

次はreport保存禁止条件にしない。

- `snapshot.saveability.vmd_save_allowed == False`
- `blocking_codes` が非空
- `warning_codes` が非空
- `save_state_fingerprint is None`
- 解析未実施
- 解析失敗
- 再解析待ち

入力音声がない場合だけ、既定名を契約どおり決められないため保存不可とする。

### 8.8 File menuとdialog

- `mi_diagnostic_report_save` をVMD保存の近傍へ追加する。
- labelは `診断レポート保存...` とする。
- acceleratorは既存ショートカットと競合させず、B6では追加しない。
- tooltip / helpは「現在の入力・解析・生成・保存可否・診断内容をTEXTレポートとして保存します」とする。
- `update_action_states(snapshot)` の同一sync内で、report menuだけは共有source path helperとBusyからenable状態を決める。VMD保存action stateは従来どおりsnapshotを使用する。
- toolbar buttonは追加しない。

dialog:

- message: `診断レポートの保存先を指定してください`
- wildcard: `テキストファイル (*.txt)|*.txt|すべてのファイル (*.*)|*.*`
- style: `wx.FD_SAVE`
- defaultDir: 元入力音声pathのparent
- defaultFile: 元入力音声stemの大小文字を保持した `<source-audio-stem>_report.txt`
- `.txt` はcase-insensitiveで判定し、不足時だけ追加する。
- path確定後に既存targetがある場合、`wx.MessageBox` のYes / No、No default、question iconで明示確認する。
- Noまたはdialog closeはcancelとして扱い、targetへ触れない。

### 8.9 controller save flow

```text
request_save_diagnostic_report()
  -> view / Busy guard
  -> latest snapshot build and store
  -> shared adapter helperでoriginal source audio pathをUiStateからresolve
  -> original source audio pathからdefault directory / filename resolve
  -> filenameなし: fail closed
  -> save dialog
  -> cancel / overwrite拒否: return
  -> generated_atを一度取得
  -> core atomic writer
  -> success status
```

- controllerはRightPane text、menu enabled状態、VMD button状態をpolicy入力にしない。
- MainFrameとcontrollerは同じsource audio path helperを使用し、`selected_audio_input.source_path` と `selected_wav_path` の優先順位を重複実装しない。
- 直接呼出しでもBusyとsource audioを再評価する。
- `ERROR` snapshotであってもwriterへ進む。
- WARNING保存前確認はreport出力では表示しない。B5の確認済みfingerprintも更新しない。
- 保存成功時は `診断レポート保存成功`、cancel時は `診断レポート保存をキャンセルしました`、失敗時は `診断レポート保存失敗` をstatusへ表示する。
- format / write / verify / replace失敗は `診断レポート保存エラー` dialogで、保存先権限、空き容量、file lock、別保存先の再試行を案内する。
- raw exception detailはerror dialogの詳細末尾へ付けるが、fingerprintやdiagnostic identityへ追加しない。
- 成功・失敗ともcurrent snapshot、failure、timing plan、Warning確認済みfingerprintを変更しない。

### 8.10 stateとsettings非変更

B6は次を追加しない。

- `UiState.last_report_output_dir`
- settings key
- recent report list
- report保存済みflag
- report生成時刻state

report保存pathと時刻はworkspace diagnosticsの正本ではない。保存完了後に `sync_ui_state()` を強制せず、snapshotやfingerprintを再生成しない。

## 9. 詳細ステップ

### Step 1: 実装前基準線確認

- branch、HEAD、worktreeを確認する。
- B1 / B2 / B5のreport、snapshot、fingerprint契約を再読する。
- current menu、action state、dialog、controller保存flowを確認する。
- 対象testを実行し、既存baselineを記録する。
- P1 / P2 / P3があればproduction実装前にplanへ反映する。

### Step 2: core formatter

- `src/core/diagnostic_report.py` を追加する。
- timezone-aware timestamp validationを実装する。
- fixed section / field formatterを実装する。
- empty value、bool、path、code list、diagnostic item、identity contextのformatを実装する。
- LF末尾とUTF-8 BOMなし契約を単体testへ固定する。

### Step 3: default filenameとatomic writer

- 元入力音声pathから大小文字を保持したdefault filenameを生成する。
- same-directory temporary writeを実装する。
- temporary write handleをflush / fsync後にcloseする。
- close後の別handleでbyte verification、strict decode、BOM検査を実装する。
- 全handle close後の `os.replace()` とfailure cleanupを実装する。
- existing target保持をfailure injection testへ固定する。

### Step 4: core public API

- `src/core/__init__.py` へB6 APIをexportする。
- GUIがnew moduleのprivate helperへ依存しないことを確認する。
- import cycleがないことを確認する。

### Step 5: MainFrame menu / dialog

- File menuへ `診断レポート保存...` を追加する。
- menu event handlerを追加する。
- 既存adapterのsource audio path resolverをpublic helper化し、snapshot builder、MainFrame、controllerから共有する。
- report action stateを共有source path helperとBusyから更新する。
- report save dialog、extension補完、明示上書き確認を追加する。
- Busy、入力なし、reset後のmenu stateを確認する。

### Step 6: AppController flow

- `request_save_diagnostic_report()` を追加する。
- latest snapshotと、UiStateの元入力音声path由来のdefault filename / source directoryを解決する。
- MainFrameと同じsource audio path helperを使用する。
- cancel、上書き拒否、success、writer failureを処理する。
- VMD saveabilityと独立してERROR snapshotを保存する。
- report保存がexisting diagnostics stateへ副作用を与えないことを確認する。

### Step 7: B6専用test

- formatterのgolden text testを追加する。
- encoding / newline / timestamp / empty value / multiline / identity testを追加する。
- atomic replace / cleanup / existing file preservation testを追加する。
- menu state / dialog / controller guard / ERROR save testを追加する。

### Step 8: 回帰・文書同期

- B2からB5 diagnostics、RightPane、VMD保存policy回帰を実行する。
- workspace resetと既存export回帰を実行する。
- 全体test、compileall、`git diff --check` を実行する。
- 実装結果とユーザーGUI確認結果をB6 plan、Index、Roadmap、Block Breakdownへ同期する。

## 10. 状態遷移 / データ契約

### 10.1 report save state

| 状態 | Menu | controller直接呼出し | report保存 |
| --- | --- | --- | --- |
| 入力音声なし | 無効 | fail closed | 不可 |
| 入力音声あり・未解析ERROR | 有効 | 許可 | 可 |
| 入力音声あり・解析失敗ERROR | 有効 | 許可 | 可 |
| 入力音声あり・再解析待ちERROR | 有効 | 許可 | 可 |
| 入力音声あり・WARNING | 有効 | 許可 | 可、WARNING確認なし |
| 入力音声あり・正常INFO | 有効 | 許可 | 可 |
| Busy | 無効 | 拒否 | 不可 |
| workspace reset後 | 無効 | fail closed | 不可 |

### 10.2 report input

report formatter入力:

- `OutputDiagnosticsSnapshot`
- timezone-aware `generated_at`

report formatterが参照しないもの:

- RightPane Info / Warning label
- playback position、frame、current vowel
- notebook tab、scroll位置
- status bar
- VMD save dialog state
- WARNING確認済みfingerprint
- report保存path
- raw UiState

保存dialogの既定名とdirectoryはreport formatterの入力ではない。controllerがUiStateの元入力音声pathから解決し、formatterには渡さない。

### 10.3 snapshot不変条件

- report保存前後で同じworkspace状態なら `save_state_fingerprint` は変わらない。
- `Generated At` はfingerprintへ入らない。
- report保存pathはfingerprintへ入らない。
- report保存成功はVMD保存可能性を変更しない。
- report保存失敗は解析結果を無効化しない。
- report保存はfailure DTOをclearしない。
- report保存はWARNING確認済みfingerprintを設定・clearしない。
- `ERROR` はVMD保存を禁止してもreport保存を禁止しない。

### 10.4 filesystem契約

| 操作結果 | temporary file | 既存target | status |
| --- | --- | --- | --- |
| dialog cancel | 作成しない | 不変 | cancel |
| 上書きNo / close | 作成しない | 不変 | cancel |
| format失敗 | 作成しない、またはcleanup | 不変 | failure |
| temporary write失敗 | cleanup | 不変 | failure |
| verify失敗 | cleanup | 不変 | failure |
| replace失敗 | cleanup | 不変 | failure |
| 成功 | 残さない | atomic replace | success |

## 11. テスト方針

### 11.1 core formatter

- 全section / fieldのexact order
- titleとtimezone付き `Generated At`
- naive datetime拒否
- boolの `true / false`
- `None` / emptyの `(not available)`
- normalized pathの保持
- saveabilityとfingerprint
- ERROR / WARNING / INFO item順
- diagnostic identity contextのstable JSON
- multiline detailのLF正規化とindent
- single-line fieldのcontrol character escape
- 同一snapshot / timestampで完全一致
- timestamp変更でGenerated Atだけが変わること
- 末尾LFが1つであること

### 11.2 encoding / atomic save

- UTF-8 strict decode可能
- BOM byteなし
- CRLF / lone CRなし
- default filenameがsource stem由来
- mixed-case source filenameの大小文字がdefault filenameで保持されること
- normalized snapshot pathからdefault filenameを作らないこと
- snapshot builder、menu、controllerが同じsource audio path resolverを使用すること
- analysis WAVやTEXT stemを使わないこと
- source pathなし／空stemでdefault filenameなし
- successful temporary write / verify / replace
- write handleがreadback前にcloseされること
- readback handleが `os.replace()` 前にcloseされること
- Windows実filesystemでtemporary fileからtargetへreplaceできること
- existing targetのsuccessful replace
- injected write failureでexisting target不変
- injected verify failureでexisting target不変
- injected replace failureでexisting target不変
- 全failureでtemporary fileが残らないこと

### 11.3 menu / dialog

- 起動直後menu無効
- input audioありで解析前ERRORでもmenu有効
- VMD保存不可でもreport menu有効
- Busy中menu無効
- reset後menu無効
- 元入力音声path由来のdefault directoryと大小文字を保持したfilename
- `.txt` 自動補完と大文字拡張子の非重複
- dialog cancel
- 上書きYes
- 上書きNo / close
- 上書き拒否時にwriter未呼出し

### 11.4 controller

- viewなし／Busyで何もしない
- source audioなしでdialog未表示
- `selected_audio_input.source_path` 優先、`selected_wav_path` fallbackがmenuとcontrollerで一致すること
- latest snapshotを一度取得すること
- RightPane textを参照しないこと
- ERROR snapshotでwriter実行
- WARNING snapshotでB5確認dialogを呼ばないこと
- fixed `generated_at` をwriterへ渡すこと
- success status
- cancel status
- writer failure dialog / status
- success / failure後のtiming plan、failure、snapshot、fingerprint保持

### 11.5 回帰

- B2 snapshot / fingerprint
- B3 Info
- B4 playback context
- B5 Warning / VMD save policy
- MS14 action state / export
- MS17 MMD用WAV dialog / overwrite / cleanup
- MS19 voice_only failure / workspace reset
- pipeline / VMD

### 11.6 対象testコマンド

各コマンドは一つずつ実行する。

B6 core:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_ms20_b6_diagnostic_report.py -q
```

B6 GUI flow:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_ms20_b6_report_save_flow.py -q
```

MS20 diagnostics回帰:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_ms20_b2_output_diagnostics.py tests/test_ms20_b3_output_diagnostics_adapter.py tests/test_ms20_b3_right_pane_info.py tests/test_ms20_b5_warning_save_policy.py -q
```

state / export / reset回帰:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_wx_ms14_b2_state.py tests/test_wx_ms14_b5_export.py tests/test_wx_ms16_b3_right_pane.py tests/test_ms19_b7_voice_only_error_handling.py tests/test_ms19_b8_workspace_reset.py -q
```

既存output dialog回帰:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_ms17_b7_mmd_wav_save_dialog.py tests/test_ms17_b7_mmd_wav_overwrite_confirm.py tests/test_ms17_b7_mmd_wav_failure_cleanup.py -q
```

pipeline / VMD:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_pipeline_and_vmd.py -q
```

全体:

```powershell
.\.venv\Scripts\python.exe -m pytest tests
```

compile:

```powershell
.\.venv\Scripts\python.exe -m compileall src tests
```

文書・差分:

```powershell
git diff --check
```

GUI runnerがpass表示後に既知wx終了処理でnonzeroとなる場合も、pass数とprocess exit codeを分けて記録する。

### 11.7 手動GUI確認

1. 起動直後、`診断レポート保存...` が無効である。
2. 音声読み込み後、未解析ERROR状態でもmenuが有効になる。
3. TEXTあり解析成功とvoice_only解析成功の双方でreportを保存できる。
4. 保存dialogの既定名が入力音声stem由来の `<base>_report.txt` になる。
5. 保存したreportが文字化けせず、BOMなしUTF-8として開ける。
6. reportのInput / Analysis / Generation / Saveability / DiagnosticsがRightPane状態と同じsnapshot内容を示す。
7. WARNING状態でもB5のVMD保存確認を出さずreportを保存できる。
8. 解析失敗ERROR状態でもfailure summary / detailを含むreportを保存できる。
9. 既存reportへの上書きNo / dialog closeで既存内容が変わらない。
10. 上書きYesでreportが更新され、temporary fileが見える形で残らない。
11. 書き込み不能directoryまたはfile lockでerror dialogと失敗statusが表示され、解析結果とWarning表示が保持される。
12. Busy中とworkspace reset後はmenuが無効になる。
13. report保存前後でVMD保存button、Warning確認済み状態、Preview、waveform、B4 playback表示が変わらない。
14. Light / Dark / Systemでmenu、save dialog、overwrite確認、error dialogが読める。

手動GUI確認を実施していない場合は未実施と報告する。実MMD、build、SmokeLaunch、package確認はB6範囲外とする。

### 11.8 文書・差分検証

- B6をplanned / implemented / verifiedで混同していない。
- B7以降を実装済みとして記載していない。
- reportとVMD保存可否を混同していない。
- `git diff --check` を実行する。
- dependency、package、license、Qt、network、固定モーフ変更がないことを確認する。

## 12. 受け入れ条件

- `src/core/diagnostic_report.py` がwxPythonをimportしない。
- 同一snapshotと同一timestampから同一report文字列が生成される。
- reportが固定title、Generated At、5 sectionを順番どおり含む。
- snapshot全summary、saveability、fingerprint、全diagnostic itemがreportへ反映される。
- empty valueは `(not available)` に統一される。
- diagnostic itemはsnapshot順で、severity、code、phase、summary、detail、identity contextを含む。
- reportはLF固定、末尾LFあり、UTF-8 BOMなしである。
- default filenameは元入力音声stemの大小文字を保持した `<base>_report.txt` である。
- report menuは入力音声あり／非Busyで有効になる。
- menuとcontrollerが共有source audio path helperを使用し、入力pathの優先順位が分岐しない。
- VMD保存不可のERROR snapshotでもreportを保存できる。
- WARNING report保存でVMD保存前確認を表示しない。
- 入力音声なし、Busy、reset後はUIとcontrollerの両方でfail closedになる。
- dialog cancelと上書き拒否で既存targetを変更しない。
- write / verify / replace失敗でtemporary fileを残さず、既存targetを壊さない。
- report保存成功／失敗がsnapshot、timing plan、failure、fingerprint、VMD保存状態を変更しない。
- report保存pathとGenerated Atがfingerprintへ入らない。
- B6専用testと指定回帰がpass表示まで完走する。
- pass表示とprocess exit codeが分けて報告される。
- ユーザーGUI確認の実施／未実施と結果が記録される。
- 新規dependency、package、license、Qt、network、固定モーフ変更がない。

## 13. リスクと対策

| リスク | 対策 |
| --- | --- |
| RightPane文字列をreportへ転記して表示変更とreportが連動する | core snapshotだけをformatter入力にする |
| formatter内部の現在時刻取得でtestが不安定になる | timezone-aware `generated_at` を明示注入する |
| Windows既定改行でCRLFが混入する | LF文字列をUTF-8 bytesへ直接encodeする |
| BOMが付与される | `utf-8` encodeとbyte検査を使用し、`utf-8-sig` を禁止する |
| diagnostic detail内の改行がsection構造を壊す | LF正規化と全継続行indentを行う |
| identity contextのreprが不安定になる | canonical JSON互換表現を固定separatorで出力する |
| formatterがitemを再sortしてB2順序と分岐する | `snapshot.items` 順をそのまま使用する |
| VMD保存不可ERRORでreportも無効になる | report固有のsource audio条件だけを使用する |
| 入力音声と解析WAVを混同してfilenameが変わる | UiStateの元source audio pathだけからstemを取り、analysis WAVを参照しない |
| normalized pathの `normcase` で元ファイル名の大小文字が失われる | default filename / directoryはUiStateの元source audio pathから解決し、snapshot正規化pathはreport本文だけに使用する |
| menuとcontrollerで元source audio pathの優先順位が分岐する | 既存adapter resolverをpublic helper化し、snapshot builder、menu、controllerで共有する |
| 上書き拒否後にwriterが走る | dialog helperのNo / closeをNoneとしてcontrollerで停止する |
| 直接targetへ書いて既存fileをtruncateする | 同一directory temporary fileと `os.replace()` を使用する |
| Windowsでtemporary handleを開いたままreadback / replaceして失敗する | binary temporary writeをcontext内で完了し、write / readbackの全handleをcloseしてから `os.replace()` する |
| failure cleanupが既存targetを削除する | cleanup対象を生成済みtemporary pathだけに限定する |
| report保存でsnapshotやfingerprintが変わる | 保存flowをstate非変更とし、前後同一性をtestする |
| report保存先履歴追加がsettings migrationへ波及する | B6ではsource parent固定とし、settingsを変更しない |
| menu追加で既存action state testが壊れる | MainFrame fixtureを現行menu contractへ限定補正する |
| GUI終了時の既知nonzeroをpassと誤報する | pass表示とprocess exit codeを分けて記録する |

## 14. Codex 実装時の注意

- 最初に `docs/MS17_and_Beyond_Index.md` を読む。
- コマンドは並列・連結実行せず、一つずつ実行する。
- `feature/MS20-implementation` 上で作業する。
- 未コミット変更があればユーザー所有変更として保護する。
- 実装前チェックでP1 / P2 / P3を確定するまでproduction codeを変更しない。
- B6はreport formatting / saveだけを所有し、B7横断closeoutを先行実装しない。
- `OutputDiagnosticsSnapshot` をreportの正本とし、RightPane textを読み戻さない。
- report保存可否をVMD保存可否から導出しない。
- formatter内でcurrent timeを取得しない。
- platform既定encoding / newlineを使用しない。
- targetへ直接書き込まない。
- cleanupで既存targetを削除しない。
- report保存をanalysis workerへ混ぜない。
- report保存後にsnapshotやfingerprintを再生成しない。
- `src/gui_wx/ui_state.py`、`settings_store.py`、`output_diagnostics.py` を根拠なく変更しない。
- 実行していないtestや手動GUI確認を通過と報告しない。
- 固定モーフ `あ / い / う / え / お` を変更しない。
- Qt / PySide6を復活させない。
- network、cloud ASR、音声外部送信、background通信、Whisper自動downloadを追加しない。
- package、release、tag、pushを行わない。

B6実装完了報告は次の形式とする。

1. 確認したファイル
2. 変更したファイル
3. 実装内容
4. 実行したテスト
5. テスト結果
6. 仕様から逸脱した点
7. 残課題
