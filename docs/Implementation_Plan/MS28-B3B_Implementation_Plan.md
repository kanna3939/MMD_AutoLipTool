# MS28-B3B Implementation Plan

## 1. 文書情報

- 対象Block: `MS28-B3B`
- 名称: Projection Input / UI Sync Failure Diagnostics
- 作成日: 2026-09-20
- 対象branch: `feature/MS28-B1-implementation`
- 基準HEAD: `ffd24a9 Implement MS28-B4 silence handling`
- MS28位置づけ: MS20〜MS27の全体マイルストーン系列とは切り離した、Ver.1実装後の独立修正実装トラック
- 文書状態: **Revised / Existing B3B verified / Diagnostic Expansion Planned**
- 依存Block: MS28-B3のデバッグtrace/store、MS28-B4の無音観測は既存実装を利用する

本Blockは、Preview投影直前に発生する `projection_input_unavailable` の原因を分離するための観測追加である。Preview生成、B4の無音判定、shape生成規則そのものを修正するBlockではない。

### 1.1 今回の改訂理由

B3B実装後、`sample/00-MMD_AutoLipTool説明3`、`01-MMD_AutoLipTool説明3`、`02-MMD_AutoLipTool説明3`、`03-MMD_AutoLipTool説明3`を実解析した。その結果、00/02では次を記録できた。

- `analysis_result_valid=true`
- `current_timing_plan_present=true`
- `base_input.status=available`
- `diagnostics_snapshot.present=true`
- `sync_context.exception_type=AdjustmentContractError`
- `projection_input.reason_code=sync_context_build_failed`

一方、`AdjustmentContractError`の具体的な契約項目、失敗フェーズ、対象イベントまたは対象フィールドは記録されず、ログだけでは修正箇所を一点特定できなかった。01/03では同じ構造の入力診断から `projection_input_ready` となり、Preview/Writer stageまで進んだ。

したがって、本改訂では今回の`sync_context`失敗だけでなく、今後の解析受け入れ、UI同期、effective shape、Preview、Writer、VMD保存の切り分けに必要な安全な固定診断情報を追加定義する。生の例外メッセージ、本文、絶対パス、音声データを保存しない制約は維持する。

## 2. 背景

16:50以降のユーザー手動テストで、次の実行が確認された。

- `00-MMD_AutoLipTool説明3`: TEXT＋音声、音声のみの両方で解析受け入れ後にPreviewが生成されなかった。
- `01-MMD_AutoLipTool説明3`: TEXT＋音声、音声のみの両方でPreview投影が成功した。
- `02-MMD_AutoLipTool説明3`: TEXT＋音声でPreviewが生成されなかった。

失敗runでは解析と `analysis_acceptance` は完了しているが、次の記録だけが残っている。

```text
effective_shape: skipped / projection_input_unavailable
projection_comparison: not_evaluable / projection_input_unavailable
```

現行の `src/gui_wx/main_frame.py` では、`_record_debug_projection_impl()` が `sync_context is None` または `diagnostics_snapshot is None` の場合に上記の固定理由だけを記録して終了する。`_build_current_ui_sync_context()` 内部では、次の候補をすでに判定しているが、失敗時の詳細はdebug artifactへ渡されていない。

1. `analysis_result_valid`、`analysis_pending_rebuild`、`current_timing_plan` の状態
2. `_build_current_base_timing_plan_input()` の結果
3. 音声長候補の欠損・不正・非有限値
4. `build_ui_sync_context()` の `AdjustmentContractError`、`TypeError`、`ValueError`
5. `_current_ui_sync_failure_reason`
6. `prepare_current_effective_output()` のwriter入力状態と失敗理由

ただし、`_debug_trace_for_current_projection()` は、debug modeがOFF、accepted traceがない、解析中、または `analysis_result_valid=False` / `analysis_pending_rebuild=True` の場合にtraceを返さない。この入口ガードを越えない状態にはprojection revisionが存在しないため、B3Bの `projection_input` stageを後付けしない。B3Bは、現在のaccepted traceに対して実際にprojection attemptが開始された場合だけを対象とする。

このため、現在のログは「Preview投影まで到達していない」ことは示せるが、入力不足、解析状態不整合、base input生成失敗、同期コンテキスト例外のどれかを区別できない。

## 3. 目的

- `projection_input_unavailable` を、発生した内部条件ごとに再分類できるdebug artifactを追加する。
- 解析受け入れ、projection revision、UI同期、effective shape、Preview、Writerの順序を同一run内で追跡できるようにする。
- 失敗時の状態値と固定理由を記録し、ファイル固有条件とUI同期順序・状態競合を切り分ける。
- 失敗した層だけでなく、失敗フェーズ、契約ドメイン、対象フィールド、対象イベントを固定コードと有限な識別子で記録し、修正候補を一点に絞れるようにする。
- 成功runと失敗runを同じ診断軸で比較できるようにし、「入力不足」「契約不整合」「キャッシュ不一致」「診断生成失敗」「Preview/Writer変換失敗」を別々に追跡する。
- 既存のPreview表示、保存可否、診断表示、B4無音判定、通常時の処理結果を変更しない。
- raw本文、絶対パス、音声データ、例外メッセージ全文をdebug artifactへ保存しない。

## 4. In Scope

- `projection_input` stageの追加。
- 同stageに対するprojection revision、analysis result、状態フラグ、base input判定、sync context判定、diagnostics snapshot判定の記録。
- `projection_input_unavailable` を次の固定reason codeへ分離する。
  - `base_input_unavailable`
  - `sync_context_build_failed`
  - `diagnostics_snapshot_unavailable`
  - `projection_input_ready`
- trace gate通過後に実行される `_build_current_ui_sync_context()` のbase input不足・例外分岐における安全な詳細理由の保持。
- `prepare_current_effective_output()` の `effective_writer_input_state` と failure reasonの同一projectionへの関連付け。
- `build_ui_sync_context()` の失敗フェーズ、固定failure code、契約ドメイン、safe field code、有限なevent indexの記録。
- base timing plan、observation、adjustment snapshot、effective plan hint、cache利用状態の構造summary記録。
- Preview/Writer投影へ進んだか、どの入力契約が欠けたか、保存直前まで到達したかを同一runで追跡する downstream stage summary の記録。
- 解析runごとの診断項目一覧を、必須・任意・未評価に分けて記録し、「記録されなかった」のか「その段階に到達していない」のかを区別する。
- `analysis_debug_store.py` によるprojection単位の `projection_input.json` 生成。
- 既存の `effective_shape` / `projection_comparison` のreason code互換維持と、詳細情報のpayload追加。
- 決定的な状態マトリクス回帰、artifact保存回帰、機密情報非混入回帰。
- B3B実装後のデバッグモード手動解析で、失敗runと成功runを比較できる確認手順の文書化。
- 00/01/02/03相当の実ファイルを使ったテストスクリプト検証で、今回の失敗分類と修復候補情報が再現可能であることの確認。

## 5. Out of Scope

- Preview形状生成、`build_preview_data_from_effective_shape_plan()`、B4の無音core、handoff、required-zeroのロジック修正。
- `projection_input_unavailable` の発生を理由に解析を再実行すること。
- 同期失敗時の自動retry、タイマー追加、UIスレッドの待機、処理順序の変更。
- ユーザー向けPreviewメッセージ、診断画面、保存可否、VMD writerの契約変更。
- `analysis_debug_trace` の全体schema version変更、既存artifactの読み込み互換機構の追加。
- 任意の例外文字列をログへ残すこと、例外メッセージの正規表現をそのまま外部契約にすること、tracebackを保存すること。
- 診断のためだけに別の検証器、再解析、再投影、追加の音声読み込みを実行すること。
- 音声、TEXT、Whisper本文、モデル実体、入力ファイルのdebugフォルダへのコピー。
- INI、presets.json、profiles.jsonへの設定保存。
- バージョン、依存関係、spec、build、正式版EXE、リリース、push、merge。
- B3Bログから原因を推定して、B1/B2/B4の製品動作を先回りで変更すること。
- trace gate前の解析状態遷移を、古いaccepted traceへ関連付けて記録すること。必要になった場合は別の状態遷移観測Blockで定義する。

## 6. 前提条件

- デバッグモードの初期OFF、セッション限定、run開始時snapshot基準を維持する。
- デバッグモードOFFでは、新しいstage、ファイル、hash、debug directoryを生成しない。
- 既存のMS28-B3 `AnalysisDebugTrace` と単一I/O担当の `AnalysisDebugStore` を利用する。
- debug記録のために同じtiming plan、base input、effective shape planを再計算しない。
- 解析結果・Preview・Writerの実処理が返した値を観測し、診断用の副作用を追加しない。
- `projection_input` は `_debug_trace_for_current_projection()` の入口ガードを通過したprojection attemptにだけ記録する。ガードで除外されたrunは、B3Bの失敗runへ分類しない。
- 既存の `effective_shape` の `reason_code="projection_input_unavailable"` は互換のため保持し、詳細は新しい `projection_input` payloadで表現する。
- stage payloadの固定コードと型だけを保存し、例外の文字列全文、traceback、本文、絶対パスは保存しない。
- `schema_version=1` は維持し、`contract_version="ms28-b3b-projection-input-v1"`のままoptional extension fieldsを追加する。既存v1 readerは未知の追加キーを無視でき、旧runに新キーがない場合は「未記録」として扱い、B3Bの失敗とは再解釈しない。

## 7. 対象ファイル

### 7.1 主変更対象

| ファイル | 変更責務 |
| --- | --- |
| `src/gui_wx/main_frame.py` | UI同期状態、base input判定、sync context判定、writer入力状態、projection input stageの収集と記録 |
| `src/core/analysis_debug_store.py` | `projection_input` をprojection単位の `projection_input.json` として保存 |
| `tests/test_ms28_b3b_projection_diagnostics.py` | B3Bの状態マトリクス、reason code、artifact、非混入回帰 |
| `tests/manual_ms28_b3b_sample_debug.py` | **新規作成予定**。sample 00〜03の実解析、debug artifact検証、最終exit code確認。通常の全pytestには自動収集させない |

### 7.2 関連確認・必要時の限定変更対象

| ファイル | 確認責務 |
| --- | --- |
| `src/core/analysis_debug_trace.py` | `record_stage()` の既存safe payload、owner、sequence、例外隔離を確認。必要な場合のみB3B固定payloadの補助関数を追加 |
| `src/gui_wx/ui_sync_context.py` | `build_ui_sync_context()` の分岐を失敗フェーズ・契約ドメインへ写像する条件を確認。必要時のみsafe failure metadataを返す補助を追加 |
| `src/core/event_adjustment.py` | `AdjustmentContractError`へ任意のsafe diagnostic code/field/indexを付与できるか確認。既存例外の公開メッセージ互換は維持 |
| `src/core/effective_shape_plan.py` | timeline、observation、adjustment、long-vowel、shape生成の検証境界をsafe failure domainへ分類。診断目的の再検証は追加しない |
| `src/gui_wx/analysis_worker.py` | audio analysis、Whisper timing、timing plan生成のstage完了/失敗境界とprojection前後の所有関係を確認 |
| `tests/test_ms28_b3_debug_trace.py` | 既存B3契約とB3B追加stageの共存確認。既存テストの意味を変えない |
| `tests/test_ms28_b4_base_event_silence_core.py` | B3B追加がB4無音処理へ影響しないことの関連確認 |
| `tests/test_ms28_b4_contract_identity.py` | debug専用projection input情報がcanonical identityへ混入しないことの確認 |

### 7.3 文書・実行確認

- 本計画ファイル: `docs/Implementation_Plan/MS28-B3B_Implementation_Plan.md`
- 実装後に必要な場合のみ `docs/MS20_and_Beyond_Index.md` のMS28状態を実到達状態へ同期する。計画作成時点ではIndexのB3/B4完了記録を変更しない。
- ユーザー手動確認: デバッグモードで成功するファイルとPreview未表示ファイルを同じ条件で解析し、`projection_input.json` を比較する。
- テストスクリプト確認: `sample/00-MMD_AutoLipTool説明3`〜`03-MMD_AutoLipTool説明3`のTXT/WAVペアを、Computer Useなしで実解析し、debug runと診断artifactを比較する。

## 8. 実装方針

### 8.1 観測位置

`sync_ui_state()` が次の値を確定した後、既存の `_update_preview_display()` と `_record_debug_projection()` の呼び出し順を維持したまま、projection入力診断を記録できるようにする。

```text
_build_current_ui_sync_context()
→ prepare_current_effective_output()
→ build_and_store_output_diagnostics_snapshot()
→ _update_preview_display()
→ _record_debug_projection()
   → projection_revision
   → projection_input stage
   → effective_shape / Preview / Writer / comparison
```

実装時は、既存の `_record_debug_projection_impl()` が開始するprojection revisionと同じtrace ownerを使用する。新stageはrevision開始直後、`effective_shape` より前に記録し、失敗時にも必ず存在するようにする。Preview更新より前に新しいprojection revisionを開始する変更は行わない。

### 8.2 固定診断結果

`projection_input` payloadは、次の構造を基準とする。値はbool、整数、有限数、固定文字列、列挙済みstatusだけに限定する。

```json
{
  "contract_version": "ms28-b3b-projection-input-v1",
  "status": "ready",
  "projection_revision": 1,
  "analysis_state": {
    "analysis_result_valid": true,
    "analysis_pending_rebuild": false,
    "current_timing_plan_present": true,
    "current_timing_plan_type": "VowelTimingPlan",
    "analysis_info_in_progress": false,
    "is_busy": false,
    "vmd_save_ready": true
  },
  "base_input": {
    "status": "available",
    "timeline_count": 76,
    "observations_present": true,
    "duration_status": "selected",
    "duration_sec": 12.3333333333
  },
  "sync_context": {
    "status": "available",
    "failure_code": "not_applicable",
    "exception_type": "not_applicable"
  },
  "diagnostics_snapshot": {
    "present": true
  },
  "effective_writer_input": {
    "state": "ready",
    "failure_code": "not_applicable"
  }
}
```

次の値は、個別の失敗経路に応じて存在する場合だけ保存する。

- `base_input.status`: `available` / `unavailable`
- `base_input.failure_code`: `not_applicable` / `plan_missing` / `duration_unavailable` / `invalid_plan_shape` / `base_input_contract_error`
- `base_input.duration_candidates`: `selected_wav_analysis`、`selected_analysis_wav`、`selected_audio_probe`ごとの `missing` / `invalid` / `non_finite_or_negative` / `candidate`
- `sync_context.status`: `available` / `unavailable`
- `sync_context.failure_code`: `not_applicable` / `base_input_unavailable` / `sync_context_build_failed`
- `sync_context.exception_type`: `not_applicable` / `AdjustmentContractError` / `TypeError` / `ValueError` / `unknown`。例外メッセージ、本文、path、tracebackは保存しない
- `diagnostics_snapshot.present`: `true` / `false`
- `effective_writer_input.state`: `ready` / `not_applicable` / `invalid`
- `effective_writer_input.failure_code`: `not_applicable`または既存の固定failure reason。`_current_ui_sync_failure_reason` の文字列全文を直接保存しない
- payloadの `status`: `ready` / `unavailable`。debug traceのstage自体は、診断レコードを書き込めた場合は既存規則に従って `completed` とし、投影処理の成功を意味させない

### 8.3 reason codeの決定順

同じprojectionで複数条件が成立した場合、次の優先順で一つのcanonical reasonを決定する。

1. base input不足: `base_input_unavailable`
2. sync context生成例外: `sync_context_build_failed`
3. diagnostics snapshot不足: `diagnostics_snapshot_unavailable`
4. 全入力利用可能: `projection_input_ready`

`effective_shape` と `projection_comparison` の既存reason codeは変更しない。B3Bでは、既存stageのpayloadに `projection_input_reason` を追加し、同一 `projection_revision` のstage sequenceから詳細stageへ辿れるようにする。既存trace APIへrecord sequence返却を追加することは必須にしない。

### 8.3.1 改訂後の修復診断summary

今回のログで不足した「どの契約の、どの段階で失敗したか」を、次の固定summaryとして追加する。値は、以下に列挙したallowlist、bool、有限数、非負整数、または列挙済みの固定状態値だけに限定し、未列挙の自由文字列を許可しない。

```json
{
  "failure_context": {
    "phase": "sync_context_build",
    "domain": "adjustment_contract",
    "code": "adjustment_contract_invalid",
    "exception_type": "AdjustmentContractError",
    "field_code": "unknown",
    "event_index": "not_available",
    "source_event_index": "not_available",
    "index_status": "not_available",
    "observed_stage": "ui_sync_context"
  },
  "sync_inputs": {
    "effective_plan_hint": "absent",
    "cache_state": "miss",
    "adjustment_snapshot": "present",
    "adjustment_count": 0,
    "output_edit_state": "present",
    "base_identity_check": "not_evaluated",
    "shape_parameters_check": "not_evaluated"
  },
  "contract_summary": {
    "timeline_count": 76,
    "observation_count": 76,
    "long_vowel_metadata": "present",
    "event_index_range": [0, 76],
    "finite_value_check": "not_evaluated"
  },
  "downstream": {
    "diagnostics_snapshot": "present",
    "effective_shape": "not_attempted",
    "preview_projection": "not_attempted",
    "writer_projection": "not_attempted",
    "vmd_save": "not_attempted"
  }
}
```

このsummaryは`contract_version="ms28-b3b-projection-input-v1"`のoptional extensionとして追加する。`schema_version`と既存v1の必須キーは変更せず、既存v1 readerは未知の追加キーを無視できるものとする。旧runにsummaryが存在しない場合は「未記録」と扱い、B3Bの失敗や欠損状態へ再解釈しない。

`failure_context`の意味は次のとおりとする。

- `phase`: `none` / `base_input_build` / `duration_selection` / `sync_context_cache` / `sync_context_build` / `effective_plan_resolve` / `effective_plan_hint_validate` / `diagnostics_snapshot_build` / `effective_output_prepare` / `preview_projection` / `writer_projection` / `vmd_save` / `debug_store_write` / `unknown`
- `domain`: `none` / `base_input` / `duration` / `adjustment_contract` / `timeline_metadata` / `long_vowel_metadata` / `observation_metadata` / `effective_shape` / `diagnostics_snapshot` / `writer_input` / `unknown`
- `code`: `none` / `base_input_unavailable` / `duration_unavailable` / `identity_mismatch` / `adjustment_snapshot_mismatch` / `shape_parameters_mismatch` / `timeline_metadata_invalid` / `long_vowel_metadata_invalid` / `observation_metadata_invalid` / `adjustment_contract_invalid` / `diagnostics_snapshot_unavailable` / `writer_input_invalid` / `unknown_contract_failure`
- `field_code`: `not_applicable` / `not_evaluated` / `base_plan_identity` / `adjustment_snapshot_identity` / `shape_parameters` / `timeline_point` / `long_vowel_source` / `long_vowel_role` / `observation` / `output_edit_history` / `effective_plan_hint` / `duration` / `unknown`
- `event_index` / `source_event_index`: 既存例外または既存検証結果から安全に取得できる場合だけ非負整数を記録し、取得不能時は`not_available`、対象外は`not_applicable`、未評価は`not_evaluated`とする。`index_status`は`available` / `not_available` / `not_applicable` / `not_evaluated`のいずれかとし、状態値自体で記録可否の理由を残す。
- `observed_stage`: `ui_sync_context` / `effective_shape` / `preview_projection` / `writer_projection` / `vmd_save` / `debug_store_write` / `unknown`。任意の例外文字列やcall stackは保存しない。

`exception_type`は、`not_applicable` / `AdjustmentContractError` / `TypeError` / `ValueError` / `unknown`のいずれかとする。成功時または例外が発生していない経路では`not_applicable`、safe metadataを発行できない失敗では型名のallowlist、型も取得できない場合は`unknown`とする。`field_code`とindex系の固定状態値は、`safe_payload()`が`None`を除去しても診断項目の意味が変わらないよう、`null`ではなく明示的な状態値で表現する。

`sync_inputs`の固定値は、`effective_plan_hint=absent` / `present` / `not_evaluated`、`cache_state=hit` / `miss` / `not_evaluated`、`adjustment_snapshot=absent` / `present` / `not_evaluated`、`output_edit_state=absent` / `present` / `not_evaluated`、各検査結果=`valid` / `invalid` / `not_evaluated`とする。`contract_summary.long_vowel_metadata`は`present` / `absent` / `not_evaluated`、`finite_value_check`は`valid` / `invalid` / `not_evaluated`とする。`event_index_range`は、既知の半開区間`[start, end]`（非負整数かつ`start <= end`）または`not_available` / `not_applicable` / `not_evaluated`のいずれかとする。`downstream`の各stageは`completed` / `skipped` / `not_attempted` / `not_evaluated`、`vmd_save`も同じ固定値で表現する。

`sync_inputs`は、sync context生成時点で実際に使用した入力状態を記録する。`effective_plan_hint`、cache hit/miss、adjustment snapshotの有無、base identityおよびshape parametersの検査結果を別々に持ち、失敗後に未評価だった項目を成功扱いしない。`contract_summary`は、既に渡されているtiming planとobservationの件数・範囲・metadata有無だけを記録し、本文・母音列全体・任意オブジェクトを保存しない。`downstream`は、後段へ到達しなかったことを欠損と混同しないための到達状態である。

### 8.3.2 safe failure metadataの発行規則

- `AdjustmentContractError`は、`safe_code`、`safe_field_code`、`event_index`、`source_event_index`をkeyword-onlyの任意属性として保持する。属性値は、発行時に`code` / `field_code`のallowlist、または非負整数のindexを満たす場合だけ設定し、未指定値は境界で`not_available`または`not_applicable`へ正規化する。既存の表示用例外メッセージは位置引数として維持するが、メッセージ全文はartifactへ渡さない。
- `ui_sync_context.py`は、`resolve_effective_shape_plan()`呼び出しを`phase=effective_plan_resolve`、hintのbase identity／adjustment snapshot／shape parameters検証を`phase=effective_plan_hint_validate`として発行する。各hint不一致は、既存の`ValueError`捕捉互換を保つ`AdjustmentContractError`へ置き換え、それぞれ`identity_mismatch`／`adjustment_snapshot_mismatch`／`shape_parameters_mismatch`へ固定写像する。plain `ValueError`のメッセージ解析には依存しない。base input型境界の`TypeError`だけは`phase=sync_context_build`、`domain=base_input`、`code=base_input_unavailable`へ写像する。
- `effective_shape_plan.py`の既存検証発行点は、代表fixtureに必要な範囲で`AdjustmentContractError`へsafe code／field／indexを付与する。event/source indexを発行点で確定できない場合は推測せず、`not_available`とする。
- `main_frame.py`は例外の`str()`を読まず、例外型とsafe属性だけをallowlist検証して`failure_context`へ正規化する。`AdjustmentContractError`／`TypeError`／`ValueError`以外、またはsafe属性がallowlist外の場合は`phase=unknown`、`domain=unknown`、`code=unknown_contract_failure`、`exception_type=unknown`へ収束する。
- `effective_shape_plan.py`のtimeline、long-vowel、observation、adjustment検証は、既存の検証境界を越えて再実行せず、既存エラー発行点からsafe domain/codeを渡す。広範な全raise箇所の機械的置換は行わない。
- safe metadataを取得できない既存経路は、`phase=unknown`、`domain=unknown`、`code=unknown_contract_failure`、例外型のみを記録する。このfallbackを理由に例外文字列を保存しない。
- 一つのprojectionで複数の失敗がある場合は、最初に発生した観測点をprimary failureとし、後段は`not_attempted`または既存のskip/not_evaluable状態で残す。
- 成功runにも同じsummaryのキーを持たせ、`failure_context.phase/domain/code=none`、`exception_type/field_code/event_index/source_event_index/index_status=not_applicable`、各未評価項目は`not_evaluated`として、成功と欠損を比較可能にする。

producerとconsumerの責務は次で固定する。

| producer | 発行する情報 | consumer |
| --- | --- | --- |
| `src/core/event_adjustment.py` | `AdjustmentContractError`のsafe code／field／event index／source index | `ui_sync_context.py`または`main_frame.py`の正規化境界 |
| `src/gui_wx/ui_sync_context.py` | `effective_plan_resolve`、`effective_plan_hint_validate`、`sync_context_build`のphase/domain/code | `main_frame.py`のprojection summary |
| `src/core/effective_shape_plan.py` | 代表fixtureに必要なtimeline／long-vowel／observation／adjustmentのsafe domain/code | `ui_sync_context.py`を経由する正規化境界 |
| `src/gui_wx/main_frame.py` | allowlist検証済み`failure_context`、`sync_inputs`、`contract_summary`、`downstream` | `projection_input` stageと`projection_input.json` |

この表にない新しいproducer、例外文字列の後解析、safe metadataの再計算はB3B実装へ追加しない。

### 8.3.3 実装優先順位と範囲上限

- P1相当: 今回の00/02で発生したsync context失敗について、`phase`、`domain`、`code`、`field_code`、`index_status`、sync inputs、downstream到達状態を必ず記録する。現行の再現経路は`effective_plan_resolve`または`effective_plan_hint_validate`まで特定し、既知の00/02経路を`unknown_contract_failure`へ退避させない。
- P2相当: `effective_plan_hint`のidentity/adjustment/shape parameters mismatch、および既存のtimeline、long-vowel、observation検証境界でsafe metadataを取得できる代表経路を追加する。
- P3相当: 成功runと失敗runの比較補助、診断項目の欠損監査、docs/diagnostics textの表現を整える。
- 一回のB3B補正で、`effective_shape_plan.py`内の全例外を網羅的に分類することは要求しない。今回の00/02以外の未観測・未対応経路は`phase=unknown`、`domain=unknown`、`code=unknown_contract_failure`として残し、次の原因が観測された時点で対象コードとfixtureを追加する。
- P1の安全性・owner・revision・機密情報非混入が満たされない限り、P2/P3の項目を優先して実装しない。

### 8.4 再計算・副作用の防止

- `_build_current_ui_sync_context()` がtrace gateを通過したprojection attemptで取得した状態と失敗理由を、B3B用の固定payloadへ渡す。既存の文字列reasonは固定code・例外型へ写像して全文を保存しない。
- `_build_current_base_timing_plan_input()` をデバッグ記録のために二度呼び出さない。
- `_selected_audio_duration_sec()` の既存stage記録を重複生成しない。候補のsummaryは同じ呼び出し結果から取り込む。
- `build_ui_sync_context()`、`resolve_effective_shape_plan()`、Preview builder、Writer adapterを診断目的で再実行しない。
- 例外時は既存のreturn、Preview placeholder、保存可否、diagnostics snapshotを変更しない。

### 8.5 artifact保存

- `src/core/analysis_debug_store.py` のprojection artifact mappingへ `projection_input: projection_input.json` を追加する。
- `projection_input` は `projections/<revision>/projection_input.json` に保存する。
- run rootのstage JSONには既存規則どおり保存する。
- `manifest.json` の `stage_status` には `projection_input` のsequence、status、reason、projection revisionを含める。
- `diagnostics.txt` の既存stage一覧にも `projection_input` の固定reasonが現れる。
- artifact metadataのsize、SHA-256、sequence整合性を既存B3契約どおり維持する。

## 9. 詳細ステップ

1. `projection_input` の固定payload、reason code、status、禁止フィールドを定義する。
2. trace gate通過後の `_build_current_ui_sync_context()` とbase input生成の各分岐から、再計算なしで安全な診断情報を収集できるようにする。gate前の状態はB3Bへ取り込まない。
3. `sync_ui_state()` から `prepare_current_effective_output()` の結果をprojection debug記録へ渡す。
4. `_record_debug_projection_impl()` でprojection revision開始直後に `projection_input` を記録する。
5. `sync_context` またはdiagnostics snapshotが不足する場合、既存の `effective_shape` skipとcomparison not_evaluableを維持しつつ、詳細stageへの参照を追加する。
6. `analysis_debug_store.py` へprojection artifactを追加し、manifest、events、diagnostics textの既存整合性を確認する。
7. 状態マトリクス、例外型、artifact、非混入の回帰テストを追加する。
8. B3/B4関連回帰を実行し、B3BがPreview、Writer、無音観測、canonical identityを変更していないことを確認する。
9. ユーザー手動テストで、00/02相当の失敗runと01相当の成功runを比較し、reason codeが分離されることを確認する。
10. 実装後の受け入れ状態、未検証範囲、次の原因調査候補をB3B記録へ反映する。
11. `build_ui_sync_context()`の例外発行点またはsync境界で、safe failure metadataを一次情報として発行する。既存の例外文字列を後から全文解析して外部artifactへ保存しない。
12. 成功・失敗の両方で`failure_context`、`sync_inputs`、`contract_summary`、`downstream`の同一キーを記録し、未評価と欠損を区別する。
13. identity mismatch、adjustment mismatch、shape parameters mismatch、timeline/long-vowel/observation metadata不整合、diagnostics snapshot不足、writer入力不正を固定状態マトリクスへ追加する。
14. safe field codeとevent indexが取得できる例、取得できないfallback例、複数段階が連鎖する例をテストし、primary failureだけが採用されることを確認する。
15. `sample/00-MMD_AutoLipTool説明3`〜`03-MMD_AutoLipTool説明3`のTXT/WAVペアをテストスクリプトで順番に解析し、失敗runの修復候補情報と成功runの同一summaryを比較する。

## 10. 状態遷移 / データ契約

### 10.1 stage順

```text
projection_revision
  → projection_input
     ├─ projection_input_ready
     │   → effective_shape
     │   → preview_projection / writer_projection
     │   → projection_comparison
     └─ failure reason
         → effective_shape skipped / projection_comparison not_evaluable
```

`projection_input` の失敗は解析run全体をfailedに変更しない。解析受け入れとprojection失敗を別状態として保持する。

### 10.2 failure matrix

| 条件 | `projection_input.status` | canonical reason | 後続stage |
| --- | --- | --- | --- |
| timing planはあるがbase inputを作れない | `unavailable` | `base_input_unavailable` | effective shape skip |
| base input後のsync context生成で固定対象例外 | `unavailable` | `sync_context_build_failed` | effective shape skip |
| sync contextはあるがdiagnostics snapshotがない | `unavailable` | `diagnostics_snapshot_unavailable` | effective shape skip |
| sync contextとdiagnostics snapshotがある | `ready` | `projection_input_ready` | 既存投影処理へ進む |

### 10.3 所有と互換性

- ownerは既存traceの `analysis_run_id`、`analysis_result_id`、`projection_revision` を継承する。
- `record_sequence` と `recorded_at` は既存traceが発行する。
- B3B payloadは新しいoptional stageであり、B3既存stageの意味を変更しない。
- 現行アプリには`projection_input`のruntime readerを追加しない。v1 optional extensionの互換性は、既存stage／artifact writerを壊さず、外部のread-only検査が未知の追加キーを無視できるJSON形状として保持することを意味する。旧runに新summaryがない場合は「未記録」と表示・報告する。
- debug専用の状態、reason、例外型、duration候補はBasePlanIdentity、save-state fingerprint、canonical output identityへ含めない。
- デバッグ保存失敗は解析、Preview、Writer、VMD保存の結果を変更せず、既存B3の `degraded` / `unavailable` 契約に従う。

### 10.4 改訂後のfailure flow

```text
existing stage / boundary
  → safe failure metadata
     ├─ primary failure context
     │   ├─ phase
     │   ├─ domain
     │   ├─ code
     │   ├─ field_code
     │   └─ event/source index
     ├─ sync input snapshot
     ├─ contract summary
     └─ downstream reachability
          → projection_input.json
```

失敗していないrunでも同じsummaryを生成し、`failure_context.code=none`、`phase=none`、`domain=none`、例外・field・index関連は`not_applicable`とする。`not_evaluated`は、その検査を実行していないことを意味し、`valid`や`available`へ補正しない。失敗がbase input段階で発生した場合はsync context以降を`not_attempted`とし、sync context段階で発生した場合はPreview/Writer以降を`not_attempted`とする。

## 11. テスト方針

### 11.1 必須単体・契約テスト

新規 `tests/test_ms28_b3b_projection_diagnostics.py` に次を固定する。

- debug mode OFF、accepted traceなし、解析中、または入口ガードで解析状態が無効な場合、B3Bの `projection_input` を生成せず、古いaccepted traceへ誤記録しない。
- duration候補が全て欠損・不正・非有限・負値のとき `base_input_unavailable` になる。
- timing plan構造が不正なとき、`base_input_contract_error` を内部詳細として保持し、外向きcanonical reasonは `base_input_unavailable` になる。
- `build_ui_sync_context()` の `AdjustmentContractError`、`TypeError`、`ValueError` を `sync_context_build_failed` と例外型へ写像する。
- `AdjustmentContractError`のsafe code、field code、event/source indexが存在する場合にpayloadへ記録し、存在しない場合は固定状態値または`unknown_contract_failure`へfallbackする。
- identity mismatch、adjustment snapshot mismatch、shape parameters mismatch、timeline metadata、long-vowel metadata、observation metadataについて、各1件以上の代表fixtureを別のfailure domain/codeとして記録する。未列挙の全例外経路を網羅することは要求しない。
- `effective_plan_hint`の有無、cache hit/miss、adjustment snapshotの有無・件数、base identity/shape parameter検査の評価状態を記録する。
- timeline/observationの件数、event index範囲、long-vowel metadataの有無、有限値検査の状態を記録する。
- downstreamの`effective_shape`、Preview、Writer、VMD保存の到達状態を`completed` / `skipped` / `not_attempted` / `not_evaluated`で区別する。VMD保存は既存の`vmd_save_ready` boolを置き換えず、debug専用summaryの`vmd_save`へ固定状態を記録する。
- sync contextがあるがdiagnostics snapshotがない場合、`diagnostics_snapshot_unavailable` になる。
- 全入力がある場合、`projection_input_ready` と有限なsummaryが記録される。
- 同一projectionで `projection_input` が `effective_shape` より先に記録され、revision/ownerが一致する。
- 既存 `effective_shape` の `projection_input_unavailable` とcomparison `not_evaluable` が維持される。

### 11.2 保存・非混入テスト

- `projection_input.json` が該当revisionへ保存される。
- manifestのstage status、artifact metadata、SHA-256、sequenceが一致する。
- payloadに絶対path、本文、transcription、raw exception message、tracebackが含まれない。
- B3B診断payloadがBasePlanIdentity、save-state fingerprint、B4 canonical identityへ混入しない。
- store書き込み失敗時に、既存の本来の解析・Preview・保存結果が変わらない。
- 成功runと失敗runのsummaryキー集合が一致し、未評価項目が欠落ではなく`not_evaluated`または`not_attempted`になる。
- safe metadataがない例外経路でも、raw exception message、traceback、本文、絶対pathが保存されず、`unknown_contract_failure`へ収束する。
- safe field codeとevent indexの存在時・不存在時、primary failure選択、後段到達状態が固定fixtureで一致する。

### 11.3 回帰範囲

実装後、次のファイルを個別のpytestコマンドとして順番に実行する。回帰対象は下記のファイル一覧で固定し、抽象的なグループ名で省略しない。

1. `tests/test_ms28_b3b_projection_diagnostics.py`
2. `tests/test_ms28_b3_debug_trace.py`
3. `tests/test_ms28_b4_base_event_silence_core.py`
4. `tests/test_ms28_b4_contract_identity.py`
5. `tests/test_ms21_b7_ui_sync_context.py`
6. `tests/test_ms21_b3_pipeline_preview_integration.py`
7. `tests/test_preview_transform.py`
8. `tests/test_pipeline_and_vmd.py`
9. `tests/test_vmd_writer_intervals.py`
10. `tests/test_vmd_writer_zero_guard.py`
11. `tests/test_ms21_b5_adjusted_vmd_save.py`
12. `tests/` 全体

各コマンドの終了コードを記録する。`.venv`に存在しない静的解析ツールは未実施として報告し、テスト成功へ読み替えない。

### 11.4 手動確認の境界

- デバッグモードONで、成功する01相当ファイルと失敗する00/02相当ファイルを解析する。
- 成功runでは `projection_input.status=ready`、失敗runでは上記failure matrixのいずれかが記録されることを確認する。
- 手動GUIでPreview表示を確認した場合はユーザー確認として記録する。自動テストやログ生成だけでGUI表示成功とは扱わない。
- EXE、正式版build、実MMD、MMD上の見た目はB3Bの自動受け入れ条件に含めず、実施した場合だけ別途記録する。

### 11.5 テストスクリプト確認の境界

- Computer Useは使用せず、リポジトリ内の実装を`.venv`のPythonテストスクリプトから起動し、wxイベントをスクリプト内で処理する。
- `sample/00-MMD_AutoLipTool説明3`〜`03-MMD_AutoLipTool説明3`の各TXT/WAVペアを同じdebug mode条件で解析する。
- 実行入口は`.\.venv\Scripts\python.exe tests\manual_ms28_b3b_sample_debug.py`とし、各sampleの処理結果を集計して、アプリ本体の失敗とスクリプト自身の集計失敗を分離する。全sampleのartifact検証が成功した場合のexit codeは`0`とする。
- 各runについて、`projection_input.json`、`manifest.json`、`diagnostics.txt`の存在、stage順、revision、artifact hash、failure summaryを検証する。
- スクリプト実行だけでは画面上のPreview表示成功とは判定しない。Preview/Writer stageへの到達はログ上の到達証拠としてのみ扱う。
- run生成用スクリプトの集計失敗とアプリ本体の解析失敗を分け、最終runのexit codeを必ず記録する。

## 12. 受け入れ条件

- [ ] B3B-AC01: Preview投影ごとに `projection_input` が `effective_shape` より先に記録される。
- [ ] B3B-AC02: base input不足、sync context例外、diagnostics snapshot不足、成功を固定reasonで区別できる。
- [ ] B3B-AC03: `analysis_result_id`、`projection_revision`、record sequenceの所属が既存traceと一致する。
- [ ] B3B-AC04: 失敗時に、状態フラグ、timing plan有無、base input状態、duration候補、diagnostics snapshot有無を確認できる。
- [ ] B3B-AC05: 例外は型と固定コードだけを保存し、例外メッセージ全文・traceback・入力本文・絶対pathを保存しない。
- [ ] B3B-AC06: 既存のPreview placeholder、解析結果、Writer、保存可否、B4無音判定の動作とreason code互換が維持される。
- [ ] B3B-AC07: 診断のための再解析、再補正、再projection、追加I/O待機が発生しない。
- [ ] B3B-AC08: `projection_input.json`、manifest、diagnostics.txtのstage/sequence/revision整合性が確認できる。
- [ ] B3B-AC09: B3B debug専用情報がBasePlanIdentity、save-state fingerprint、B4 canonical identityへ混入しない。
- [ ] B3B-AC10: §11.3に列挙したB3B、B3、B4、UI同期、Preview変換、pipeline/VMD、writer、保存回帰と全pytestが成功する。
- [ ] B3B-AC11: ユーザー手動解析で、成功runとPreview未表示runの失敗理由を比較できる。
- [ ] B3B-AC12: 実装済み、自動検証済み、ユーザー確認済み、未検証の範囲が分離して報告される。
- [ ] B3B-AC13: debug mode OFF、accepted traceなし、解析中、入口ガードで除外された解析状態がB3B artifactへ混入せず、古いaccepted traceへ誤記録されない。
- [ ] B3B-AC14: 成功・失敗の両方で`failure_context`、`sync_inputs`、`contract_summary`、`downstream`のキー集合が揃い、未評価と欠損を区別できる。
- [ ] B3B-AC15: `AdjustmentContractError`を、例外型だけでなくsafe phase/domain/code/field codeへ分類できる。分類不能時は`unknown_contract_failure`へfallbackし、raw messageを保存しない。
- [ ] B3B-AC16: identity、adjustment snapshot、shape parameters、timeline、long-vowel、observation、duration、diagnostics snapshot、writer inputについて、各1件以上の代表fixtureを同じprojection summaryで比較できる。全例外発行点の網羅は本ACの要求に含めず、未対応経路は`unknown_contract_failure`として固定する。
- [ ] B3B-AC17: safe event/source indexが利用可能な場合に非負整数で対象を特定でき、利用不能・対象外・未評価の場合は`not_available` / `not_applicable` / `not_evaluated`と`index_status`で理由が残る。
- [ ] B3B-AC18: downstream stageの`completed`、`skipped`、`not_attempted`、`not_evaluated`を区別でき、後段へ到達しなかった理由が前段failureと矛盾しない。
- [ ] B3B-AC19: 指定テストスクリプトをexit code `0`で実行し、sample 00〜03の各runで同じ診断summaryを比較できる。00/02相当の`AdjustmentContractError`経路は、少なくとも`unknown_contract_failure`より具体的なsafe `phase` / `domain` / `code`へ分類され、01/03相当の成功runは`code=none`と明示状態値で比較できる。
- [ ] B3B-AC20: safe failure metadataの追加が、既存UI、Preview、Writer、VMD保存、B4無音判定、canonical identityへ影響しない。

## 13. リスクと対策

| リスク | 対策 |
| --- | --- |
| 診断のためにbase inputやeffective planを再計算して状態を変える | 既存呼び出しの戻り値・分岐理由をそのまま渡し、診断専用再実行を禁止する |
| 失敗理由を増やしたことで既存のUIやerror契約が変わる | `effective_shape` の既存reason codeを維持し、詳細は新stageに限定する |
| 例外内容や入力情報がdebugへ漏れる | 固定reason、例外型、有限値、件数だけをallowlist保存する |
| projection revisionの異なる情報が混ざる | 新stageをrevision開始直後に記録し、owner/sequenceを既存traceから継承する |
| `diagnostics_snapshot` の欠損とsync contextの欠損を混同する | 両者を別フィールド・別reasonで記録する |
| 入口ガード前の状態を古いaccepted traceへ誤所属させる | B3Bは入口ガードを通過したprojection attemptだけを対象にし、除外された状態をartifactへ記録しない |
| B4の無音観測やcanonical identityへdebug専用値が混入する | identity生成回帰とB4回帰を必須化する |
| 成功runだけ詳細化され失敗runが記録されない | `effective_shape` の早期returnより前に `projection_input` を記録する |
| debug storeの障害が本来の処理へ伝播する | 既存B3の非blocking・例外隔離・degraded/unavailable契約を維持する |
| 例外型だけで修正対象を絞れない | 発行点のsafe code/domain/field/indexを一次情報として渡し、分類不能はunknownへ明示する |
| 成功runと失敗runでログ項目が異なり比較できない | 固定キー集合と`not_evaluated`/`not_attempted`を使用する |
| event indexやfield codeが誤ったprojectionへ混入する | 既存trace owner、analysis result、projection revision、record sequenceを継承し、同一attempt内だけで発行する |
| 診断項目の増加で本文・パス・任意オブジェクトが漏れる | 型、allowlist、有限値、件数、非負indexだけを受け付ける境界を設ける |
| テストスクリプトの集計失敗をアプリ失敗と誤認する | アプリrunのterminal/capture statusと、スクリプト自身のexit codeを別々に記録する |

## 14. 実装時の注意

- B3Bは原因を特定するための観測追加であり、原因未確定のままPreview生成や同期順序を修正しない。
- 今回の改訂は、B3B既存ログで確認できた`AdjustmentContractError`の一点特定不足を解消するための観測拡張であり、Preview生成や同期順序の製品修正を含まない。
- B3Bのprojection attemptは、現行 `_debug_trace_for_current_projection()` の入口ガードを通過したものだけとする。入口ガードの条件を緩和して、過去のaccepted traceへ状態を付け替えない。
- `_current_ui_sync_failure_reason` の文字列をそのまま外部artifactへ保存しない。安定したfailure codeと例外型へ写像する。
- safe failure metadataは例外発行点で作成し、sync境界ではallowlist検証とfallbackだけを行う。例外メッセージの後解析を主契約にしない。
- `analysis_result_valid`、`analysis_pending_rebuild`、`current_timing_plan`、`vmd_save_ready` は同一のUI同期試行時点のsnapshotとして記録する。
- duration候補のsource名は固定列挙値として保存し、候補metadataに含まれるpathや任意オブジェクトを保存しない。
- `projection_input` の新規artifactが存在しない旧B3 runを、B3Bの失敗として再解釈しない。旧artifactは読み取り互換の対象外とし、今回の実装後runから適用する。
- B3B実装後の原因調査では、まず失敗runのcanonical reasonを確認し、その後に必要なコード経路だけを調査する。ログから確定できない因果関係は推測として分離する。
- 修復可否の判定では、少なくとも`phase`、`domain`、`code`、`field_code`、対象index、入力summary、downstream到達状態が揃っているかを確認する。型だけの場合は「層特定済み・一点修正未特定」と報告する。
- 実装後に原因が特定できても、別Blockの修正実装へ自動移行しない。次の修正範囲は別途計画する。

### P2/P3再発防止ゲート

- reason codeを追加・変更する場合は、入口ガード、owner、projection revision、後続stage、回帰fixtureの対応表を同時に更新する。入口ガード外の状態を新reasonで後付けしない。
- 「関連回帰」「Preview/Writer回帰」のような抽象表現を受け入れ条件へ残さず、対象ファイルまたは実行コマンドを列挙する。
- projection attemptでない状態をB3B artifactへ記録したり、旧accepted traceへ付け替えたりする変更は、B3Bの受け入れ条件違反とする。
