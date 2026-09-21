# MS28-B3C Implementation Plan

## 1. 文書情報

- 対象Block: `MS28-B3C`
- 名称: Resolver Contract Failure / Execution Diagnostics Detail Extension
- 作成日: 2026-09-20
- 文書状態: **B3C base implemented / Extension planned / Self-reviewed**。B3C本体は`4120935`で実装済み。今回の詳細拡張は未実装。
- 位置づけ: 独立修正トラックMS28のデバッグ追加Block。B3/B3Bの記録基盤、実装済みB3Cのresolver/execution診断、B4の現行resolverを利用する。
- 成果物: `docs/Implementation_Plan/MS28-B3C_Implementation_Plan.md`
- 今回の変更権限: 本計画ファイルだけ。コード・テスト・既存ログ・Gitは変更せず、追加エージェントを起動しない。
- 将来の実装範囲: 実装済みB3Cが特定した契約違反について、発行直前の派生値・生成元・局所関係を観測する。根本原因の修正は別作業。
- 基準: §2の23時台に生成された最新6 run、現行ソース、B3C実装commitを閲覧して照合した。既存ログは変更せず、過去ログへ値を補完しない。

## 2. 背景

### 2.1 根拠となる6 run

対象時刻は2026-09-20、JST。ユーザーが手動操作で生成した23:23以降の最新6件を、ディレクトリ時刻順で固定する。ログだけでは操作主体を識別できない。

| run directory（`debug/`配下） | 入力 | mode | B3C resolver結果 | revision数 | Preview終端 |
| --- | --- | --- | --- | ---: | --- |
| `20260920_232331_341_893d5262dad344a0bac876cfa9cebe30` | 00 | `text_audio` | `admission_range_invalid` / event 79 / frame 380 | 2 | not_evaluable |
| `20260920_232410_227_46b71162902f49afa7458407b46eed87` | 00 | `voice_only` | `admission_range_invalid` / event 77 / frame 380 | 2 | not_evaluable |
| `20260920_232436_584_7ef2bf5f25ec408885115097acbb87ec` | 01 | `text_audio` | completed / resolved | 2 | success |
| `20260920_232503_115_204d1a243e034af4855721ecdf77e824` | 01 | `voice_only` | completed / resolved | 2 | success |
| `20260920_232537_206_b42d92b4fdaa4a09b356800beb6733df` | 02 | `text_audio` | `admission_range_invalid` / event 36 / frame 151 | 2 | not_evaluable |
| `20260920_232604_723_8f1edafe4c904e6e97b428573859967a` | 02 | `voice_only` | `admission_range_invalid` / event 36 / frame 151 | 1 | not_evaluable |

B3C実装後のread-only確認結果:

- 6 manifestすべてで `debug_mode_snapshot=true`、`record_enabled=true`、`capture_status=completed`。
- manifest掲載327成果物すべてで存在・byte数・SHA-256が一致。11 projection recordすべてに`ms28-b3c-resolver-v1`、attempt、execution diagnosticsが存在する。
- 00と02の4 run・7 revisionは `admission_range_invalid / silence_admission / effective_frame_range`。resolverはfailed、effective shapeはfailed、Preview/Writerはnot_evaluableまたはnot_attempted。
- 00の失敗イベントは両modeとも約12.659秒・frame 380で、入力eventの`start_frame=peak_frame=end_frame=380`。TEXT＋音声側は`no_peak_in_window`、音声のみ側は正のpeak値でも同じframeへ潰れている。
- 02の失敗イベントは両modeとも約5.019秒・frame 151で、`start_frame=peak_frame=end_frame=151`。両modeとも`below_rel_threshold`。
- 01の両modeはresolver/effective shape/Preview/Writerが成功し、Previewの`model_valid=true`、比較の`within_tolerance=true`。
- 失敗診断のleaf code・phase・field・event indexは取得できたが、`details_availability=not_available`、`source_event_index=not_available`で、実際の派生`effective_frame_range`とshape生成元は未記録。
- runtime identityは全件 `python.exe / source / Python 3.14.3 / app 1.0.0`、`build_identifier=unavailable`。実行時ソースと現行ソースの厳密な同一性は証明できない。

327成果物の整合性は記録保存の証拠であり、Preview成功、全契約の正当性、根本原因の修復を意味しない。03番はこの6件に含まれない。

### 2.2 現行実装から確認した不足

| 根拠 | 現状と不足 |
| --- | --- |
| `src/core/effective_shape_plan.py::resolve_effective_shape_plan` | B3Cでphase/pass/leaf failureは記録できるが、`EventSilenceAdmission`構築前に例外となると、候補値・shape provenanceを保存する前にeffective planが欠落する |
| 同ファイルの `_build_event_silence_admissions` / `EventSilenceAdmission.__post_init__` | `effective_frame_range`、positive/required-zero range、shape所属、source eventを計算してからdataclass検査へ渡す。今回の失敗ではその入力値がfailure detailsに出ていない |
| `src/core/event_adjustment.py::AdjustmentContractError` / `src/core/effective_shape_diagnostics.py` | B3Cのsafe code/field/phase/passは機能しているが、`safe_details`が付かないconstructor由来エラーでは`details_availability=not_available`になる |
| `src/gui_wx/ui_sync_context.py::build_ui_sync_context` | 詳細属性のない例外を `adjustment_contract_invalid / unknown` に補完する |
| `src/gui_wx/main_frame.py::_build_current_ui_sync_context` / `_update_preview_display` | 外側phaseだけを付ける。contextがない場合、Preview側からもcontext構築を呼ぶ既存経路があり、最後の診断dictだけでは試行を区別できない |
| 同ファイルの `_debug_downstream_payload` | context有無・Preview model有効性・writer入力state・保存可否から処理実行を推定している |
| 同ファイルの `_record_debug_projection_impl` | `projection_input`記録後にdebug用writer投影を実行する。入力snapshotの時点でその投影の完了を宣言できない |
| `src/core/analysis_debug_trace.py::safe_payload` | 任意文字列を値として通す。汎用sanitizerだけでは例外message等の漏出を防げない。`None`や非有限値は欠落し得る |
| `tests/manual_ms28_b3b_sample_debug.py::_validate_run` / `run` | B3Cで構造・診断・Previewを分離できるが、失敗時のcandidate detail充足性までは検証しない |
| `tests/test_ms28_b3c_resolver_diagnostics.py` / `tests/test_ms28_b3c_execution_diagnostics.py` | B3Cの9件は通過済み。今回の実runで不足したconstructor直前の派生値、shape provenance、隣接関係の回帰条件は未追加 |

### 2.3 原因についての確度

停止層と直接の契約違反は特定済みである。4 runすべてが`silence_admission`の`effective_frame_range`検査で失敗し、入力eventのframe範囲が同一frameへ縮退している。ただし、最終的な派生rangeがraw event由来かshape event range由来か、また長音・隣接event・無音coreのどの関係が縮退を作ったかは未特定である。B3C拡張ではこの局所値と生成元を取得する。これは製品修正の原因確定や仕様変更を意味しない。

## 3. 目的

1. 実装済みB3Cの`admission_range_invalid`を、候補値・生成元・隣接関係まで追跡できるようにする。
2. `raw event range`、`effective event range`、`shape event range`、`required-zero/positive range`を分離して記録し、どの変換で幅0になったかを判定できるようにする。
3. 処理の試行・成功・skip・評価不能と、artifact記録成功・保存可否を区別する。
4. B3B互換・privacy・通常モードの結果を維持し、デバッグ機構の合格とPreview修復の合格を分ける。
5. B3Cのv1 optional拡張として、既存consumerが新詳細項目を無視しても旧判定・旧ログ読込が壊れないようにする。

## 4. In Scope

- 実装済みB3Cのoptional診断を維持し、`details_availability=not_available`になる失敗境界へ、局所値のallowlist化された詳細を追加する。
- `EventSilenceAdmission`生成直前に、raw/effective/shape由来のframe range、range種別、source event、shape provenance、隣接eventを記録する。
- `admission_range_invalid`に限らず、同じconstructor/derived-value境界で発生するrange・role・index・rejection系failureへ同じ詳細契約を適用する。
- `projection_input`のresolver diagnosticsと、同一revisionの`projection_comparison`終端summaryへ、同じattempt/cycle/ownerに紐付いた詳細をoptionalで保存する。
- `details_availability`を`available` / `partial` / `not_available` / `not_applicable`で明示し、値が取れない場合も固定理由を残す。成功経路でdetailを生成しない場合は`not_applicable`とし、診断のための再計算は行わない。
- 00〜03 × 2入力modeの既存手動スクリプトへ、失敗時の詳細充足性、raw/effective rangeの照合、mode間比較の判定を追加する。
- B3C既存回帰、constructor直前fixture、privacy、旧v1 payload互換、collector障害隔離を検証する。

## 5. Out of Scope

- 長音hold、丸め、無音判定、suspicious/continuity、admission、required-zero、Preview/Writerの製品規則の修正。
- 検査の緩和、データ補正、失敗イベントの削除、例外抑制によるPreview復旧。
- 診断を理由とする再解析・resolver再実行・新規retry・追加の音声読込。
- UIのエラーメッセージ、保存可否、入力mode、cache hit/miss条件、解析採否の変更。
- 既存ログの更新、schema/versionの更新、旧ログへの新しい値の補完保存。拡張はB3C v1のoptional fieldとして扱い、既存`contract_version`と`diagnostic_revision`を変更しない。
- raw例外/message/traceback/path、TEXT/Whisper本文、音声、モデル実体、任意オブジェクト、全shape/全eventの無制限dumpのdebug保存。
- build identifierの新しい収集機構、EXEビルド、依存・ライセンス変更、INI/preset/profile更新、Git変更、公開。

## 6. 前提条件

- B3デバッグモードは初期OFF・セッション限定。run snapshot、既存trace gate、ownerの契約を維持する。B3C本体の診断を基礎とし、拡張だけを追加する。
- `schema_version=1`、`contract_version="ms28-b3b-projection-input-v1"`、`diagnostic_revision="ms28-b3c-resolver-v1"`、既存reasonとfixed valueは維持する。拡張項目はすべてoptionalで、旧readerは無視できる。
- 既存の例外型・`str(error)`・`args`・raise順序を保つ。safe属性は診断専用であり製品分岐へ使わない。
- 固定safe metadataの付与はOFFでも許容するが、collector、履歴、局所snapshot、追加hash/I/OはOFFで作らない。
- 診断のために新しい契約検査を製品経路へ追加しない。既存検査を実行した範囲だけ記録する。
- 実装時に実ファイルを再解析しても、Whisper等の結果が過去runと一致するとは限らない。決定的fixtureと実解析の検証を分ける。
- 最新6件でB3Cの基本診断は取得済みである。今回の拡張は、既に特定できた`silence_admission/effective_frame_range`の発行直前情報を増やすためのものとする。製品修正は別作業であり、拡張の実装結果だけで原因修復を宣言しない。

## 7. 対象ファイル

以下は今回の詳細拡張の実装対象であり、今回編集するのは本計画だけである。

| 区分 | ファイル | 責務 |
| --- | --- | --- |
| 主変更 | `src/core/effective_shape_plan.py` | admission生成直前のcandidate range・shape provenance・隣接関係の観測。既存検査順と失敗条件は変更しない |
| 関連確認 | `src/core/event_adjustment.py` | 実装済みsafe属性を維持。必要な詳細値が例外へ渡る場合だけ互換的に拡張 |
| 関連変更 | `src/core/effective_shape_diagnostics.py` | 実装済みcollectorへbounded local detail、availability、固定理由、range種別のallowlistを追加 |
| 関連変更 | `src/gui_wx/ui_sync_context.py` | candidate detailをlegacy failure_contextで上書きせず、optional diagnosticsへ伝播 |
| 関連確認 | `src/gui_wx/main_frame.py` | resolver detailとexecution summaryの同一cycle/attempt/owner紐付けを維持 |
| 限定変更 | `src/core/analysis_debug_trace.py` | 既存save actionへ実行意味のoptional payload追加。汎用sanitizerの制約は弱めない |
| 関連確認 | `src/core/analysis_debug_store.py` | 新ネスト値が既存artifact・manifest・comparison・saveへ保存されること。新artifactは原則不要 |
| 関連確認 | `src/gui_wx/app_controller.py` | 既存 `vmd_save_request/completed/failed/cancelled` の通知位置。保存ロジックは変更しない |
| 主変更 | `tests/manual_ms28_b3b_sample_debug.py` | 8組合せ・複数revision・詳細充足性・range照合・mode分離 |
| 関連変更 | `tests/test_ms28_b3c_resolver_diagnostics.py` | constructor直前のcandidate detail、range種別、shape/event provenance、非干渉 |
| 関連変更 | `tests/test_ms28_b3c_execution_diagnostics.py` | detailのprojection/comparison所属、欠損・partial・collector障害、cycle/attempt/owner |
| 関連変更 | `tests/test_ms28_b3b_projection_diagnostics.py` | optional v1拡張・legacy code維持・補正後のdownstream |
| 参照 | `docs/Implementation_Plan/MS28-B3B_Implementation_Plan.md`、§2の最新6 run、commit `4120935` | 互換基準、実装済みB3Cの境界、今回の不足情報。既存ファイルは本計画作成では変更しない |

B3C本体の新規ファイルとテストは既に存在する。今回の詳細拡張では既存B3C実装を拡張し、無関係な新規ログ基盤は作らない。

## 8. 実装方針

### 8.1 発行点で固定metadataを作る

`AdjustmentContractError`へoptional keyword-only属性 `safe_phase`、`safe_pass_kind`、`safe_details`を追加する。既存 `safe_code/safe_field_code/event_index/source_event_index` を維持する。`safe_details`は専用型のprimitive値だけとし、任意dictやdataclassの一括serializeを受け入れない。

leaf codeは下表の固定値とする。同一codeでもfieldとphaseで検査を一意に辿れるようにする。外側catchでは不足属性だけを補い、発行点のcode/field/indexを消さない。exception messageの解析、正規表現分類、stack/locals探索は行わない。

| phase | 現行の主な発行点/境界 | 固定failure_code | field_codeの対応 |
| --- | --- | --- | --- |
| `resolver_input` | resolver入口、BaseTimingPlanInput | `base_input_type_invalid`, `source_duration_invalid`, `shape_parameters_type_invalid` | `base_input`, `source_duration_frames`, `shape_parameters` |
| `shape_parameters` | ShapeParameters、validate_long_vowel_mode | `shape_parameter_invalid`, `long_vowel_mode_invalid` | `closing_hold_frames`, `closing_softness_frames`, `long_vowel_mode` |
| `timeline_metadata` | `_timeline_long_metadata` | `long_metadata_type_invalid`, `long_source_order_invalid`, `long_source_unexpected`, `long_metadata_mixed`, `long_token_order_invalid`, `long_active_source_mismatch`, `long_source_vowel_mismatch` | `vowel_token_index`, `is_long_vowel_continuation`, `long_vowel_source_token_index`, `long_metadata`, `vowel`から該当field |
| `base_events` | `_finite_number`, `_point_bounds`, `_base_events` | `numeric_type_invalid`, `numeric_non_finite`, `numeric_negative`, `timeline_bounds_invalid`, `vowel_unsupported`, `base_frame_order_invalid` | `time_sec`, `duration_sec`, `start_sec`, `end_sec`, `peak_value`, `timeline_bounds`, `vowel`, `frame_order` |
| `long_runs` | `_long_vowel_runs` | `long_source_missing` | `long_vowel_source_token_index` |
| `observations` | `_validate_observations` | `observation_count_mismatch`, `observation_index_mismatch`, `observation_vowel_mismatch`, `observation_reference_invalid`, `observation_span_invalid`, `observation_flag_invalid`, `observation_bracketing_invalid`, `observation_rms_length_mismatch`、上記numeric codes | `observations`, `event_index`, `vowel`, 各参照/flag名、`span_indices`, `bracketing`, `rms_window_times_sec`, `rms_window_values`, `local_peak` |
| `observation_contract` | `_observation_contract_payload` | `observation_frame_invalid`, `observation_range_invalid`, `observation_overlap_invalid`, `observation_coverage_invalid`, `observation_provenance_invalid`, `observation_rejection_invalid` | 現行検査の `full_span_start_frame/end_frame`, `silence_core_frame_ranges`, `boundary_fringe_frame_ranges`, `silence_core_overlap`, `coverage_status`, `provenance_status`, `bridge_rejection_reason_code` |
| `base_identity` | `build_base_plan_identity` | `identity_contract_invalid`（この境界自身の既存契約例外のみ） | `base_plan_identity`。子のtimeline/observationコードは保持 |
| `snapshot_canonicalize` | `_canonical_snapshot`, `canonicalize_adjustment_snapshot`とその呼出し先 | `snapshot_identity_mismatch`, `snapshot_schema_invalid`, `adjustment_entry_type_invalid`, `adjustment_duplicate_index`, `adjustment_index_out_of_range`, `adjustment_field_invalid` | `base_plan_identity`, `adjustment_schema`, `adjustments`, `base_event_index`, 検査対象の調整field |
| `adjustment_ownership` | `_validate_long_adjustment_ownership` | `adjustment_index_out_of_range`, `long_adjustment_ownership_invalid`, `long_role_invalid` | `base_event_index`, `adjustment_ownership`, `long_vowel_role` |
| `adjustment_apply` | `_apply_event_adjustments` | `adjusted_frame_order_invalid` | `frame_order` |
| `handoff_candidates` / `handoff_apply` | `_candidate_handoffs` / `_apply_cross_vowel_handoffs` | 成功は`none`。既存の非契約例外はfallbackのみ | 検査未実行をvalidとしない |
| `regular_shapes` | `_build_shapes`, `_shape_for_group` | `tail_override_non_tail`, `slope_midpoint_missing` | `tail_override`, `slope_ratio` |
| `long_shapes` | `_shape_for_long_run` | `long_terminal_order_invalid`, `long_hold_close_conflict` | `terminal_end_frame`, `closing_frame` |
| `manual_crossfade` | `_first_event_for_shape`, `_apply_manual_crossfade_extensions`, `_build_manual_crossfade_metadata` | `shape_event_missing`, `manual_crossfade_limit_exceeded` | `real_base_event_indices`, `end_offset_frames` |
| `slope_validation` | `_validate_active_slope_overrides` | `slope_midpoint_missing` | `slope_ratio` |
| `silence_admission` / `silence_rebind` | `_build_event_silence_admissions`, `_rebind_event_silence_admissions`, EventSilenceAdmission | `admission_index_invalid`, `admission_vowel_invalid`, `admission_shape_id_invalid`, `admission_point_kind_invalid`, `admission_source_indices_invalid`, `admission_range_invalid`, `admission_role_invalid`, `admission_flag_invalid`, `admission_rejection_invalid`, `admission_enabled_reason_conflict` | 同dataclassの検査fieldを固定列挙。rangeは `effective_frame_range`, `positive_core_frame_ranges`, `required_zero_frame_ranges`を分ける |
| `required_zero_conflicts` | `_validate_required_zero_conflicts` | `required_zero_positive_conflict` | `required_zero_frames` |
| `normalization_contract` / `plan_assemble` | `_required_zero_frames_from_admissions`, `_normalization_contract`, EffectiveShapePlan構築 | 成功は`none`。非契約例外はfallbackのみ | `normalization_contract` / `effective_plan` |

表の「各参照/flag/field」は実装時に文字列を動的生成する指定ではない。現行 `_OBSERVATION_INDEX_FIELDS`、`_OBSERVATION_FLAGS`、EventAdjustment、EventSilenceAdmissionの検査fieldを専用moduleの固定allowlistへ転記し、表のグループと一対一に対応させる。任意のfield名は `unknown`へ落とす。

既存比較を分割してtype/non-finite/negativeを識別する場合も評価順序と拒否条件は変えない。constructor由来の失敗は呼出し元が保有する安全なevent/phaseを補完する。getter等が予期せず失敗した場合に二次的な診断例外で原例外を置き換えない。

TypeError/ValueError等、safe属性を持たない例外も、collectorが観測したphaseと固定例外型だけを保持して原例外を再送出する。leafを特定できないものは `unknown_contract_failure` とし、例外型は既存allowlist外なら `unknown`。B3Cのために上位のcatch範囲を拡大して製品例外を握り潰さない。

### 8.2 phaseとpassの分離

`pass_kind`は `primary` / `identity_validation` / `silence_rebuild` / `manual_comparison` / `not_applicable` の固定値。

- resolverの本計算はprimary。
- identity内部で再度実行されるbase/observation検査はidentity_validation。既存の再計算を観測するだけであり追加呼出しはしない。
- rejected eventを除外した既存shape再構築はsilence_rebuild。
- comparison snapshot以降の再計算はmanual_comparison。
- skipped branchは実行済みとしない。phase開始/正常return/例外を既存実行順で観測する。子phaseの失敗を親phase名で上書きしない。

phase履歴は各eventの数値検査を1件ずつ展開せず、同じpass/phaseの反復を集約する。各行に最初/最後の観測順序、attempted/completed件数、検査済event数、最初の失敗を保持する。これにより正常な長いtimelineがevent数だけで履歴上限へ到達することを避ける。実際の発行点と対象eventは失敗metadataへ残す。

collectorはresolverと `build_ui_sync_context` のoptional keyword-only引数として渡す。既存呼出しは無変更で動作し、返り値はEffectiveShapePlan/UiSyncContextのまま。debug情報をplan、snapshot、cache key、canonical identity、fingerprintに追加しない。

### 8.3 最小診断項目とprivacy境界

| 層 | 全attemptに必要なsummary | 失敗時に必要な局所情報 | 保存しないもの |
| --- | --- | --- | --- |
| base input | timeline/observation件数、source duration frames、observationsのpresent/absent、検査の進行範囲 | 当該eventの秒・丸め後frame・peak値、隣接eventまたは関係相手、検査の左右の値 | 入力path、本文、全オブジェクトdump |
| effective plan | partial/available/unavailable、base/effective event・shape・handoff・admission件数（生成済みだけ） | raw-adjusted→handoff後event、該当shapeの種類・local shape ordinal・control point・所属event、失敗検査に使った値 | plan全体の追加複製、canonical payload |
| adjustment snapshot | requested有無・件数、canonical件数、identity comparison状態、明示調整の有無 | 当該eventのpeak/start/end/hold/softness/slope/long mode overrideの指定有無と型検証済み値 | snapshot全体、任意identity文字列、新しい識別hash |
| shape parameters | `closing_hold_frames`, `closing_softness_frames`, `long_vowel_mode`、検査状態 | requested/effective hold/softness、available extension、slope midpoint有無 | INIやpreset/profileの内容・名前 |
| long-vowel | metadataのexplicit/legacy/mixed、生成済run数 | source/terminal/continuationのindex、role、source peak/terminal end/next start/closing frame、同母音同frame handoff判定 | 対応する文字、読み、Whisper word |
| suspicious / continuity | 既存candidate件数、処理済handoff件数 | 当該observationの5 candidate flags、span/previous/next index、full span/core/fringe範囲、coverage/provenance、handoff採否・固定rejection理由、silence admissionの局所結果 | RMS全配列、音声波形、任意rejection文字列 |

秒・frame・母音5種・有限な値・run内indexも入力由来情報である。ローカルdebug modeの目的内で最小限保存し、匿名性を保証すると記載しない。既存manifestのbasename/size/hash契約は維持するが、新診断へpath/basenameを追加しない。

局所情報の固定ルール:

- `event_index`は元timelineの位置。時間順のeffective event ordinal、shape ordinal、token indexと混同しない。
- `source_event_index`は長音sourceなど発行点で分かる関係相手。対応がないとき `not_applicable`、取得不能は `not_available`。不正refを正常な参照として使わない。
- event/source indexはboolを除く `0 <= index < timeline_count` の整数だけを正常参照として保存する。stale adjustment indexなど範囲外の指定は `invalid_reference_value` として保存し、対応するevent indexはnot_availableにする。
- observationのevent番号自身が不正でも、外側ループ位置を対象indexとして残す。参照不正の値は型タグと有限整数値だけを `invalid_reference_value` に記録し、source indexへ入れない。
- required-zero衝突では実際に検査した同一 `(vowel, frame)`、positive側/zero側のshape ordinal、point_kind/値、所属eventを保存する。検査内の最初の衝突キーで、複数shapeの代表pairはordinal昇順で選ぶ。診断選択のために検査順序自体を変更しない。
- positiveがevent peak由来ならそのeventを指す。control pointの一意なevent帰属がない場合、shape所属の最小eventをanchorとして使い、`event_role=positive_shape_anchor` / `source_event_role=required_zero_shape_anchor`を必須にする。単一eventの責任と断定しない。空の所属はnot_available。
- primary対象と直接相手を先に保存し、任意の近傍は各前後1件まで。event details最大8件、関連index/control points/frame rangesは各collection最大32件。長音run・spanの全展開はしない。B3C admission detailでは§8.3.1の専用上限（隣接2件、shape provenance16件、control points16件、各range/index collection32件）を優先する。
- phase履歴は1 resolver attempt最大128件、1同期cycle最大16 attempt。超過時は新規detail蓄積だけを止める。first failureと総件数、`truncated=true`、drop件数は保持し、診断品質をlimitedとする。処理を中断しない。
- 各省略collectionにはtotal/recorded/truncatedを持たせる。失敗に直接使ったscalarとprimary pairを上限で落とさない。詳細が取れなければavailabilityと固定理由を記録する。
- 浮動値はfiniteのみ。type/non-finite/negativeを `value_status` で区別し、JSON NaN/Infinity、boolを整数扱い、`None`による必要キー消失を禁止する。
- 新 `input_summary.finite_checks` にfield groupと検査済/対象件数を持たせ、既存検査を完遂したgroupだけvalidにする。legacy `contract_summary.finite_value_check` は対象全体の完遂が証明できない限りnot_evaluatedのままとする。全planを一括validにしない。
- suspiciousという新しい推定判定を加えない。既存observation/handoff/admissionの値を比較可能に記録する。RMSは既存計算で得た長さ・local_peak等に限定する。

### 8.3.1 B3C拡張: derived rangeと発行直前の局所証拠

今回の最新6 runでは、leaf code・phase・field・event indexまでは取得できたが、`details_availability=not_available`のため、`effective_frame_range`へ渡された実値とその生成元が欠落した。次のoptional detailを、`EventSilenceAdmission`のconstructor呼出し直前に一度だけ組み立てる。constructorが失敗した場合も、このdetailをfailureへ渡す。

```text
failure.details
  detail_revision = "ms28-b3c-admission-detail-v1"
  detail_capture_state = available / partial / not_available
  unavailable_reason = not_available / value_not_observed / owner_mismatch / truncated
  section_status
    event_context {state, reason}
    admission_candidate {state, reason}
    range_derivation {state, reason}
  event_context
    event_index
    vowel
    raw_range {start_sec, end_sec, start_frame, peak_frame, end_frame}
    effective_event_range {start_frame, end_frame}
    event_range_status = valid / zero_width / reversed / unavailable
    adjacent {previous_event_index, next_event_index}
    adjacent_ranges[] (前後各1件まで)
    long_vowel_role, long_vowel_source_event_index
  admission_candidate
    origin_shape_id
    source_event_indices[]
    shape_match_count
    shape_provenance[]
      shape_ordinal, shape_kind, real_base_event_indices[]
      event_range, shape_range, control_points[]
    positive_point_kinds[]
    positive_core_frame_ranges[]
    observed_positive_core_frame_ranges[]
    required_zero_frame_ranges[]
    base_event_silence_core_overlap
    manual_adjustment_applied
    enabled, rejection_reason_code
  range_derivation
    raw_event_range
    shape_event_ranges[]
    effective_range_before_validation
    range_inputs_status
```

この入れ子payloadは既存`safe_details()`へそのまま渡さない。`effective_shape_diagnostics.py`にB3C専用の固定スキーマシリアライザ（実装時の責務名は`serialize_admission_detail`相当）を追加し、呼出し側から明示的なtyped fieldを受け取って、許可キー・enum・有限数値・index範囲・collection上限を適用する。任意dict、dataclass、例外本文、任意文字列、任意objectを汎用的に再帰serializeしない。

現行`MAX_DETAILS=8`およびcollectorの`max_details`はlegacy primitive detailのキー抽出だけに適用する。B3C detailはシリアライザの戻り値を一つのatomicな拡張payloadとして扱い、内部ではcollection上限を適用した後、JSON上は§8.3.1の固定キーを`details`直下へ展開する。legacy側の8項目制限で`detail_revision`、`section_status`、`event_context`、`admission_candidate`、`range_derivation`のいずれかを落とさない。B3C detailの上限超過・欠損は、payload全体ではなく該当collectionまたはsectionの状態へ反映する。

既存の`safe_details()`が生成するlegacyのprimitive detailは従来どおり`details`直下へ残す。B3C拡張の固定キー（`detail_revision`、`section_status`、`event_context`、`admission_candidate`、`range_derivation`）とはallowlistを分離し、キー衝突が起きた場合は拡張値を上書きせず`not_available`へ落とす。これにより、既存の`expected_count`等の読込契約を変更しない。legacy detailの件数制限とB3C detailのcollection制限は別の制御として実装する。

詳細の記録APIは例外属性への詰め込みではなく、collectorの失敗記録へ独立して渡す。実装時は`phase_failed(..., failure_detail=...)`と`_safe_failure(..., failure_detail=...)`相当のkeyword-only経路を定義し、`failure_detail`を専用シリアライザへ通してから既存legacy detailと統合する。例外の`args`、message、raise順序、既存safe属性は変更しない。failure detailがある場合、`details_availability`は入力dictの有無ではなく、シリアライズ後の`detail_capture_state`と必須項目の存在から決定する。

失敗時の最低限契約を次のように固定する。`available`は、`event_context.event_index`、`event_context.effective_event_range`、`event_context.event_range_status`、`range_derivation.effective_range_before_validation`、および対象candidateの所属状態が観測済みで、collectionが上限内である場合に限る。`partial`は一部の必須項目が観測済みだが、shape未生成、owner不明、またはcollection切捨てがある場合とし、該当sectionの`section_status.state`と`section_status.reason`を必ず残す。`not_available`は発行直前のcore rangeまたは対象event ownerを観測できなかった場合に限る。トップレベル`unavailable_reason`は全体の主理由、sectionごとの欠損理由は各`section_status.reason`として扱う。sectionの`reason`は`not_applicable`を含む固定理由enumに限定し、トップレベルの失敗理由には`not_applicable`を使用しない。成功経路で詳細を生成しない場合の`details_availability=not_applicable`と、失敗したが観測不能な場合の`not_available`を混同しない。

実際の内部値が取得できない場合は、値を推測・再計算せず、該当フィールドを固定値`not_available`として保存する。`event_range_status=zero_width`は、startとendが同一であるという観測結果を表し、製品上の許容・修復判定には使わない。`effective_frame_range`の実値が(380, 380)や(151, 151)のように幅0である場合は、range statusとともに記録する。

shape provenanceは全shape dumpではなく、対象eventに一致するshapeだけを対象とする。`shape_provenance`は最大16件、control pointは対象event rangeと前後1件の境界に関係するものをpayload全体で最大16件、frame range collectionは各32件とし、超過時は該当collectionの`truncated=true`を付ける。shapeがまだ生成されていない場合は`shape_match_count=0`、`shape_provenance=[]`、`section_status.admission_candidate.state=partial`、該当理由`value_not_observed`または`not_available`を記録する。shape未生成だけを理由に、取得済みraw/effective range全体を`not_available`へ落とさない。

raw timeline、RMS、Whisper本文、path、例外messageはこのdetailへ複製しない。`events.csv`の既存stage記録との照合はテスト・外部解析側で行い、resolver内で全イベントを再走査しない。

### 8.4 試行とprojectionの所有

`sync_ui_state()`入口で、既存trace gateを満たす場合だけcycle専用collectorを開始する。revision開始位置は既存の `_record_debug_projection_impl()` のままとする。

- context構築を実際に呼ぶたびにcycle内の `attempt_no` を採番する。利用元は `sync_ui_state` / `prepare_output` / `preview_refresh` の固定 `caller`。core resolverの呼出しがなければresolver attemptedにしない。
- 通常同期とPreview内fallbackを別attemptとして残す。最後の `_current_ui_sync_diagnostic` だけで前の失敗を消さない。
- `context_attempt_no`（最初に渡されたcontextの試行）、`preview_attempt_no`、`writer_input_attempt_no`を別々に参照する。複数試行で結果が異なっても無理に一つの成否へ統合しない。
- revisionが発行された時点で同じanalysis_run_id/result_idのcycleを凍結して関連付ける。gate外・解析結果変更・旧job・別cycleの値を引き継がない。
- cache/hintでplanを取得した場合は `plan_origin=cache/hint`、resolverはskipped。過去の成功履歴を今回の実行済履歴としてコピーしない。
- 再入時はcycleを別containerで保持し、finallyで元のactive cycleへ戻す。無所属のUI外resolver呼出しを古いaccepted traceへ後付けしない。
- collector/sanitizer故障は既存B3のdegraded扱い。original result/exception/returnを維持し、debug情報だけを捨てる。

## 9. 詳細ステップ

1. §8.1の発行点一覧を現行コードと照合し、resolverから到達する明示raise、constructor、canonicalization、子helperの対応を固定registryとテストケースにする。resolver外の独立編集APIは一覧に境界として記載し、無関係な再設計をしない。
2. 固定enum・safe値型・bounded collectorを追加する。既存legacy primitive向け`safe_details()`と、B3C入れ子payload向け専用シリアライザを分離し、後者は§8.3.1の固定キー・上限・section statusだけを受け付ける。dictを何でも渡せるgeneric loggerにしない。
3. `AdjustmentContractError`を互換拡張し、明示発行点にmetadataを付ける。例外本文と製品検査条件が変わっていないことを確認する。
4. `_candidate_shape_details_for_event`と`_build_event_silence_admissions`の境界で、constructorへ渡すcandidate payloadを一度だけ固定形へ変換する。raw/effective/shape range、shape provenance、隣接event、positive/zero rangeを保持し、値の再計算を行わない。
5. resolverにcollectorを渡し、§8.2のpass/phaseを観測する。特にsilence admission前後、silence再構築、manual comparison、required-zero検査前の生成物を区別する。`phase_failed`へ独立した`failure_detail`引数を追加し、例外のsafe属性とB3C detailを明示的な衝突規則で統合する。constructor失敗時も発行直前detailが失われないことを確認する。
6. UI sync境界までmetadata/collectorを伝播する。legacy failure_contextは従来category、追加resolver_diagnosticsはleaf codeとする。詳細をunknownで潰さず、`available/partial/not_available/not_applicable`を保持する。
7. cycleとattempt、利用元を管理し、既存retry/caching/Preview呼出し順を保持する。debug OFFではcollectorを渡さない。
8. downstream、comparison終端summary、保存actionの意味を§10.3に統一する。writer入力readyから投影completedを推定する処理を除く。
9. 手動スクリプトを§11.3の8組合せと判定分離へ更新する。生成済ログを選ぶロジックではなく当該accepted traceのrunを検証し、失敗caseのdetail充足性を判定する。
10. 発行点・UI伝播・privacy・非干渉・collector障害・旧payload・詳細欠損・スクリプト判定のテストを実施する。
11. 回帰と実解析の各結果・exit code・未検証範囲を報告する。00/02の派生rangeと生成元が得られても原因候補として報告するだけで、根本修正へ自動移行しない。

## 10. 状態遷移 / データ契約

### 10.1 v1 optional extension

`projection_input`の既存キー・型・reasonの意味を維持し、次のoptional objectを追加する。

```text
resolver_diagnostics
  diagnostic_revision = "ms28-b3c-resolver-v1"
  capture_state = complete / limited / unavailable
  context_attempt_no, preview_attempt_no, writer_input_attempt_no
  attempts[]
    attempt_no, caller, plan_origin(resolved/cache/hint/unavailable)
    resolver_execution, phases[]
    failure {failure_code, phase, pass_kind, field_code,
             event_index, source_event_index, event_role, source_event_role,
             exception_type, details_availability, details?}
    input_summary, partial_plan_summary, local_context, truncation
execution_diagnostics
  diagnostic_revision = "ms28-b3c-execution-v1"
  snapshot_point = projection_input
  operations {effective_shape, preview_projection, writer_projection,
              diagnostics_snapshot, vmd_save}
```

数値IDの取得不能は `not_available`、操作に対応しないIDは `not_applicable` とする。failureの成功値は `failure_code=none`、phase/pass/field/indicesは `not_applicable`。failureがあるのにleaf発行情報がない場合は `unknown_contract_failure` と最後に実際に観測したphase、または `unknown`。成功とunknownを混同しない。

追加objectのenumも固定する。`event_role/source_event_role` は `subject` / `long_source` / `related_event` / `positive_event_peak` / `positive_shape_anchor` / `required_zero_shape_anchor` / `not_applicable` / `not_available`、`details_availability` は `available` / `partial` / `not_available` / `not_applicable`。B3C拡張の`detail_revision`は`ms28-b3c-admission-detail-v1`固定、`detail_capture_state`は`available` / `partial` / `not_available`、`section_status`は`event_context` / `admission_candidate` / `range_derivation`をキーとするobject、その各`state`は`available` / `partial` / `not_available` / `not_applicable`、`unavailable_reason`は`not_available` / `value_not_observed` / `owner_mismatch` / `truncated`に限定し、sectionのreasonだけ`not_applicable`も許可する。値の状態は `valid` / `invalid_type` / `non_finite` / `negative` / `not_available` / `not_applicable` / `not_evaluated`、型タグは `bool` / `int` / `float` / `str` / `sequence` / `none` / `other`。自由なクラス名を保存しない。phase/fieldを含む未知enumはunknown、状態不明はnot_evaluatedへ落とす。typeが許容されることと製品契約がvalidであることは分ける。

`phase_failed`のdetail受渡しは、既存`safe_details`との後方互換を次のように固定する。legacy primitive detailは既存キーを保持し、B3C detailは専用allowlistで検証した新規キーだけを同じ`details` objectへ追加する。新規キーの入力が不正または衝突した場合は、その項目を`not_available`として扱い、既存legacy detail・failure code・phase・field・indexを上書きしない。B3C detailが未指定の場合は従来のsafe_details経路を維持する。

既存 `failure_context.code` はB3Bのcategory値を維持する。leaf codeと発行phase→legacy categoryの写像は次の優先順で固定する。

1. `snapshot_identity_mismatch` → `adjustment_snapshot_mismatch`。既存hint由来のsafe codeは現行値をそのまま維持する。
2. `identity_contract_invalid` → `identity_mismatch`。
3. phase=shape_parameters、またはshape_parameters型/long_vowel_mode不正 → `shape_parameters_mismatch`。
4. phase=observations/observation_contract → `observation_metadata_invalid`（共通numeric codeを含む）。
5. phase=timeline_metadata/long_runs/long_shapes → `long_vowel_metadata_invalid`。
6. phase=base_events → `timeline_metadata_invalid`。
7. その他の表内の既知resolver契約 → `adjustment_contract_invalid`。
8. 未分類の実行例外 → `unknown_contract_failure`。

既存field allowlist外のleaf fieldはlegacy側でunknownにしてよいが、新objectでは固定leaf fieldを保持する。legacy phaseは外側の `effective_plan_resolve` 等を維持する。これらの分類はUI/runtimeの分岐に使わない。

旧v1 readerは追加キーを無視できる。旧runに新objectがない場合は未記録と扱う。旧runのwrong downstreamを後から書き換えない。新objectの `diagnostic_revision` は補正済み意味の識別用であり、B3B contract/schema versionの更新ではない。

### 10.2 実行stateとoutcome

各operation/phaseは、単一の成功フラグではなく次を持つ。

| 項目 | 固定値 | 意味 |
| --- | --- | --- |
| `state` | `not_attempted` | 観測時点で呼び出しておらず、skip判断もまだない |
| 同上 | `attempted` | 呼出し済み。成功returnを得ていない。例外終了でもこのstateを使い、outcome=failedとする |
| 同上 | `completed` | 対象処理の正常returnを観測した |
| 同上 | `skipped` | 前提不足・cache/hint利用・branch不成立で呼ばない判断をした |
| 同上 | `not_evaluable` | 診断情報不足やcollector故障等で実行事実を判定できない |
| `outcome` | `success`, `failed`, `pending`, `cancelled`, `not_applicable`, `not_evaluable` | completed→success、attempted→failed/pending（保存actionではcancelledも許容）、skipped/not_attempted→not_applicable、not_evaluable→not_evaluable |
| `reason_code` | `none`, `upstream_unavailable`, `cache_reuse`, `hint_reuse`, `branch_not_required`, `operation_not_requested`, `contract_failure`, `runtime_failure`, `capture_unavailable` | 固定された実行/skip理由。契約違反の詳細はfailureを参照 |

capture completedはJSON記録の正常終了でありoperation completedではない。従来のstage wrapper statusも変更せず、新objectのstateと区別する。

### 10.3 downstream・時点・保存

既存 `downstream` のキーと固定値集合は維持する。追加objectでは試行を詳細化し、legacy表示を以下のように補正する。

| 実際の状態 | 新operation state/outcome | legacy downstream |
| --- | --- | --- |
| base input不足、resolver未呼出し | effective_shape skipped / not_applicable | effective_shape skipped |
| resolver例外終了 | effective_shape attempted / failed | effective_shape skipped（詳細は新object） |
| resolver正常return、plan利用可能 | effective_shape completed / success | effective_shape completed |
| cache/hintで利用可能planを取得 | resolver skipped、effective_shape completed / success、plan_origin明記 | effective_shape completed |
| resolver成功だがdiagnostics欠損 | effective_shape completed、diagnosticsは実観測に応じた状態 | contextがあるのにeffective_shapeをnot_attemptedへ戻さない |
| 前提不足でPreview/Writer変換未呼出し | skipped / not_applicable | skipped |
| Preview変換またはWriter変換が例外終了 | attempted / failed | skipped |
| Preview変換/表示model設定の正常終了を同じcycleで観測 | completed / success | preview_projection completed |
| debug writer投影前のprojection_input時点 | not_attempted / not_applicable | writer_projection not_attempted |
| debug writer投影を実行し正常return | completed / success（comparison時点） | comparison終端summaryでcompleted |
| 保存要求なし | vmd_save not_attempted / not_applicable | vmd_save not_attempted |
| 診断情報不足 | not_evaluable / not_evaluable | not_evaluated |

Preview modelの過去の `is_valid` だけでcompletedにしない。`prepare_current_effective_output`のreadyはwriter入力準備であり、writer変換の成功とは別物である。

`projection_input`は入力時点のimmutable snapshot。後からwriter/saveが実行されても書き戻さない。既存 `projection_comparison` payloadに同じ `execution_diagnostics`（`snapshot_point=projection_complete`）を追加し、実際に到達した終端の状態を記録する。失敗early-returnとdebug内部エラー時も可能な範囲で付け、comparisonの既存 `not_evaluable` / reasonを維持する。これによりstage順を変更せず未来の完了を先取りしない。

保存の正本は既存 `vmd_file_save` / `save_operation_id`。`analysis_state.vmd_save_ready`は可否boolのまま。各save action payloadへ同じ形式の実行状態をoptionalで付ける。

- request: attempted/pending（「保存要求の試行」。ファイル書込み開始の保証ではない）。
- completed: completed/success。既存保存処理の成功通知がある場合だけ。
- failed: attempted/failed。
- cancelled: attempted/cancelled、`reason_code=operation_cancelled`を保存actionに限り追加する。
- 保存要求時のrun/result/revisionへ紐付け、その後の失敗・成功が別revisionを参照しない。既存operation IDを利用する。過去に終えた保存で次revisionをcompletedにしない。
- projectionより後の保存を証明する際はsave actionを参照する。projection snapshotを保存実績一覧へ変えない。

### 10.4 失敗ログの期待形

下記は形式例であり00/02の原因判定ではない。

```json
{
  "failure_code": "admission_range_invalid",
  "phase": "silence_admission",
  "pass_kind": "primary",
  "field_code": "effective_frame_range",
  "event_index": 7,
  "source_event_index": "not_applicable",
  "event_role": "subject",
  "source_event_role": "not_applicable",
  "exception_type": "AdjustmentContractError",
  "details_availability": "available",
  "details": {
    "detail_revision": "ms28-b3c-admission-detail-v1",
    "detail_capture_state": "available",
    "section_status": {
      "event_context": {"state": "available", "reason": "not_applicable"},
      "admission_candidate": {"state": "available", "reason": "not_applicable"},
      "range_derivation": {"state": "available", "reason": "not_applicable"}
    },
    "event_context": {
      "raw_range": {"start_frame": 380, "peak_frame": 380, "end_frame": 380},
      "effective_event_range": {"start_frame": 380, "end_frame": 380},
      "event_range_status": "zero_width"
    },
    "range_derivation": {
      "raw_event_range": [380, 380],
      "effective_range_before_validation": [380, 380],
      "range_inputs_status": "valid"
    }
  }
}
```

上記の値は形式例であり、実装時は入力から観測した値だけを保存する。`details_availability=available`でも、製品契約が正しいことや修復済みであることを意味しない。§2の00/02が同条件で再現した場合の必須結果は、legacy `sync_context_build_failed`、resolver attempted/failed、具体的leaf code/phase/field/index、`effective_frame_range`の実値、raw/shape/effectiveの関係、後段skip理由である。実再現でも`details_availability=not_available`が継続する場合、B3C拡張の診断品質受入は未達とする。

### 10.5 B3C detail extensionの互換契約

- `resolver_diagnostics`、`failure.details`、`event_context`、`admission_candidate`、`range_derivation`はすべてoptionalであり、既存B3B payloadの必須キー・型・reasonを変更しない。
- 既存consumerが`details`を無視しても、legacy `failure_context`、`execution_diagnostics`、Preview/Writerの判定は従来と同じになる。
- 追加detailの存在は、失敗値の補正、resolverの再実行、Previewの続行、cache key/identity/fingerprintの変更を引き起こさない。
- projection_inputとprojection_comparisonは同一attempt/cycle/ownerのdetailだけを持つ。詳細が後から得られない場合、入力snapshotへ終端値を書き戻さない。
- 旧ログにdetailを補完しない。detailなしの旧runは`not_recorded`または既存の`not_available`として扱い、今回の拡張合格と混同しない。

## 11. テスト方針

### 11.1 決定的fixtureと安全性

既存 `test_ms28_b3c_resolver_diagnostics.py` を拡張し、safe属性を手で付けた例外だけではなく実際の検査条件を踏む。

- §8.1の明示failure_codeごとに少なくとも1件の発行点テスト。共通numeric/field helperはparametrizeし、呼出し先のfieldとevent伝播も確認する。
- 不正timeline範囲・丸め後frame順序・metadata混在/参照逆転・observation bracketing/RMS/range・snapshot duplicate/stale/identity・調整所有権・長音終端/次shape衝突・admission range/採否理由・required-zero衝突を含める。
- primaryとsilence_rebuildとmanual_comparisonで同じshape helperが呼ばれる場合を分ける。constructor/helper単体fixtureしか成立しないcodeはその境界で検証し、resolver伝播は別の代表fixtureで検証する。実行不能なbranchを捏造しない。
- 正常値、境界の同frame同母音、空observation、全無音、ゼロ幅event等、現行が許容する入力は許容結果を維持する。B3Cだけで新たに拒否しない。
- collector有/無で返り値、例外型・args、BasePlanIdentity、adjustment snapshot、Preview/Writer出力が一致。call-countで診断用resolver/音声処理の再実行がないことを確認する。
- 不正safe metadata、raw message/path/TEXTを含む例外、未知enum、NaN/Infinity/bool、上限超過、collector例外を注入する。全生成payload/artifactに生情報がなく、原結果が変わらないことを確認する。
- required-zeroのshape ordinalとevent index、long sourceとterminal、観測span indexとhalf-open frame範囲の取り違えを検出する。
- `EventSilenceAdmission`へ渡す直前のcandidateについて、raw/effective/shape rangeの実値、zero-width/reversed判定、shape provenance、隣接event、positive/required-zero rangeがfailure detailへ残ることを検証する。constructor validationが失敗してもdetailが消えないことを必須にする。
- 00/02相当の`start_frame=peak_frame=end_frame` fixture、正のpeak値だがzero-widthになるfixture、shape未生成fixture、長音terminal/同母音handoff fixtureを分け、同じ`admission_range_invalid`でも生成経路を区別できることを確認する。
- `details_availability=available/partial/not_available/not_applicable`を意図的に作り、available値の再計算・推測補完・既存failure_contextへの上書きがないことを確認する。
- B3C専用シリアライザについて、nested key/type/enumのallowlist、shape provenance16件・control point16件・range/index32件の上限、sectionごとのreason、legacy primitive detailとの共存を確認する。legacy側の8項目制限を超える組合せでもB3C detail全体が欠落せず、上限超過時に生データが漏れず、該当sectionだけがpartialになることを検証する。
- `phase_failed(failure_detail=...)`相当の独立受渡しについて、constructor例外のargs/message/型、既存safe metadata、legacy detailが変わらず、B3C detailだけが追加保存されることを確認する。detail未指定時は従来経路、シリアライザ障害時は原例外と結果を維持する。

既存 `test_ms28_b3c_execution_diagnostics.py` と既存B3Bテストでは以下を固定する。

- resolver failedでもattempted、cache/hintではresolver skipped、UI fallback複数attempt、最初の失敗後の別attempt成功、旧trace・別cycle・再入の混入防止。
- diagnostics欠損、Preview stale model、Preview変換失敗、writer入力readyだがdebug変換失敗、comparison terminal、collector unavailableを区別する。
- 保存可否true＋保存操作0件ではnot_attempted。request/success/failure/cancel、revision変更を含む所有を検証する。実ファイル保存はtmp_pathのみ。
- 旧B3B payload（新objectなし）を読む検査はmissing extensionと判定でき、新payloadの必須legacyキー・型・reason・schema/versionが維持される。
- 新旧artifact、manifest hash/size、stage payload、diagnostics.txt、同revision ownerの整合性。

### 11.2 回帰対象と実行順

実装時は `.\.venv\Scripts\python.exe -m pytest <対象>` を一度に1コマンドで実行し、終了コードを確認して次へ進む。

1. `tests/test_ms28_b3c_resolver_diagnostics.py`
2. `tests/test_ms28_b3c_execution_diagnostics.py`
3. `tests/test_ms28_b3b_projection_diagnostics.py`
4. `tests/test_ms28_b3_debug_trace.py`
5. `tests/test_ms21_b2_event_adjustment.py`
6. `tests/test_ms21_b2_effective_shape_plan.py`
7. `tests/test_ms22_b2_long_vowel_resolver.py`
8. `tests/test_ms28_b4_base_event_silence_core.py`
9. `tests/test_ms28_b4_contract_identity.py`
10. `tests/test_ms21_b7_ui_sync_context.py`
11. `tests/test_wx_ms21_b7_sync_efficiency.py`
12. `tests/test_ms21_b3_pipeline_preview_integration.py`
13. `tests/test_preview_transform.py`
14. `tests/test_pipeline_and_vmd.py`
15. `tests/test_ms21_b5_adjusted_vmd_save.py`
16. `tests/` 全体（core・GUI・保存境界にまたがる追加の最終回帰として1回）

対象テストファイルの実在を確認済み。テスト成功後の繰返し実行は新しい変更・失敗・具体的リスクがある場合に限る。失敗を回避するため既存assertを削除しない。今回の拡張実装時に、詳細契約のassertを追加する。

### 11.3 手動スクリプトの判定分離

既存ファイル名を維持し、以下を追加する。通常pytestから実Whisper解析を自動実行しない。

- 標準対象は `sample/00-MMD_AutoLipTool説明3`〜`03-MMD_AutoLipTool説明3` × `text_audio/voice_only` の8組合せ。各caseを直列に独立した子processで実行し、状態・text・hint・cache・旧accepted traceを共有しない。
- text_audioは現行 `_open_text_file(..., auto_load_counterpart=False)`＋音声controllerを使う。voice_onlyは新規workspaceでTEXTを開かず音声controllerだけを使う。manifestの実input_mode、source audio/text identity有無を検証し、意図したmodeと違えばharness failure。
- 実行設定はmemory内で同条件に固定（hold=0、softness=0、long_vowel_mode=hold、調整なし、モデルsmallがローカル利用可能なら使用）。既存のパラメータAPIを使い、INI等へ保存しない。モデル未配置はunverifiedであり自動downloadしない。
- 既存 `pump_until` の経過秒だけを理由とする強制失敗を標準動作から外す。60秒以内の間隔で待機対象・経過を表示し、worker terminalまたは明確なerror/cancelまで同じ処理を待つ。重複起動しない。ユーザー中断・環境障害はharness incompleteとして保存済証拠と分けて報告する。
- accepted traceからrunを特定し、store flush成功後に全revisionを検証する。revision数を2等に固定しない。flush未完了を解析失敗に読み替えず、capture incompleteとする。
- manifest掲載全成果物の存在・bytes/hash、全stageのsequence/owner、stageとprojection payload、diagnostics.txt、phase/attemptの所属を検証する。separatorはWindows/JSON双方で正規化する。

caseごとの出力は次の別フィールドを必須とする。

| フィールド | 判定 |
| --- | --- |
| `artifact_validation` | passed / failed / not_evaluable：構造・整合性・privacyの検査 |
| `diagnostic_validation` | passed / failed / not_evaluable：失敗の具体的code/field/index/局所情報と実行状態が十分か |
| `diagnostic_detail_validation` | passed / failed / not_evaluable：failure detailのcapture state、derived range、shape/event provenance、隣接関係が契約どおりか |
| `preview_execution` | succeeded / failed / skipped / not_evaluable：当該attemptの変換/モデル設定と対応stageの実績 |
| `preview_model_valid` | boolまたはnot_evaluable。succeededの補助証拠であり画面確認ではない |
| `regression_validation` | passed / failed / not_evaluable：当該caseの入力mode・設定・同一attempt内の状態整合性と既知成功条件に対する結果。pytestを内側で再実行しない |
| `reproduction_status` | reproduced / not_reproduced / not_applicable / not_evaluable：00/02の過去の失敗が今回再現したか。原因特定の受入と区別する |
| `harness_status` | completed / failed / incomplete：スクリプト自身の状態 |

新引数は `--check diagnostics`（標準）、`--check preview`。stdoutに集計と「要求したチェック名」を必ず表示する。

- diagnostics: 全8件のartifact/diagnostic/diagnostic_detail/regression判定がpassed、harness completedの場合だけexit 0。失敗caseではleaf codeだけでなく、detail capture state、effective range実値、range derivation、shape/event provenanceの必須項目を検査する。Preview failed/skipped件数は別に必ず表示し、0件でなければ「Preview修復済み」と表示しない。
- preview: 上記条件に加えて全caseのPreview succeeded＋model validを要求する。artifact等合格でもPreview未達があればexit 2。
- modeにかかわらずartifact/診断品質/回帰/harnessの不合格または必須case未検証はexit 1を優先する。
- Preview unavailableを含むdiagnostics用fixtureはexit 0＋Preview failed/skipped表示、同じfixtureのpreview判定はexit 2になることをunit testで確認する。strictの実解析を二重に実行する必要はない。
- 結果集計で例外が出ても他caseの取得済結果を失わず、実処理継続が安全なcaseだけ順次継続する。consoleの自由文字列をdebug artifactへ転記しない。

予定実行入口: `.\.venv\Scripts\python.exe tests\manual_ms28_b3b_sample_debug.py --check diagnostics`。Computer Useは使用しない。

### 11.4 sample回帰条件

| sample | text_audio | voice_only | B3C拡張受入で確認すること |
| --- | --- | --- | --- |
| 00 | 最新runは`admission_range_invalid`、detail不足 | 最新runは`admission_range_invalid`、detail不足 | 約12.659秒/frame380のraw/effective/shape rangeと隣接関係を取得。両modeで同じ音声由来の差を比較 |
| 01 | 最新runはready/Preview成功 | 最新runはready/Preview成功 | 正常経路でdetailを不要に生成せず、code=none、Preview/Writer到達、cache再利用と実実行の区別 |
| 02 | 最新runは`admission_range_invalid`、detail不足 | 最新runは`admission_range_invalid`、detail不足 | 約5.019秒/frame151のzero-width候補を取得。`below_rel_threshold`とframe縮退を混同しない |
| 03 | 今回の最新6件にはない | 今回の最新6件にはない | 両modeを新規確認。過去のtext_audio成功報告をvoice_onlyの証拠に使わず、detail有無を同じ判定軸で記録 |

実解析のイベント数・revision数・Whisper内容は固定assertにしない。00/02が再現しなくなった場合、成功を原因特定と扱わず「実ファイル再現は未確認」とする。実装前の同じ入力・設定の比較が必要になれば別runとして記録し、旧logは更新しない。live結果が揺れることと、診断を有/無にした同じin-memory fixtureの結果が変わることを分ける。後者はB3C拡張回帰不合格。detailが取得できても、製品修復やPreview成功とは扱わない。

01の同条件実解析で新たな失敗が出た場合はregression_validation=failedとして原因を調べ、単にログが採れたことだけで合格にしない。03は両modeで今回の結果を基準候補として記録し、過去6件から成功をassertしない。00/02が正常化して十分な成功ログを採れた場合、スクリプトの診断チェック自体は合格し得るが、reproduction_status=not_reproducedとAC04未確認を必ず併記する。スクリプトexit 0は全AC充足の代用ではない。

### 11.5 テスト・手動・未検証の境界

- unit/integrationは発行点・伝播・保存契約と結果非干渉を証明する。実解析スクリプトはsource環境での実行結果とartifactを証明する。
- wxスクリプトのモデル成功は、人が見たPreview画面の正常表示と同義ではない。
- ユーザー手動では00/01/02/03の必要caseについて画面上のPreviewと該当runを対応付ける。手動結果が得られるまではuser-reported確認を補完・創作しない。
- EXE、正式版build、実MMDの見た目は本Blockの必須自動条件に含めない。実施していなければ未検証。
- 本計画更新時は拡張実装・実解析・拡張用unit testを実行していない。実装済みB3Cの対象テスト9件と、ユーザー手動の最新6 runは既存証拠として扱い、今回の拡張の検証済みとはしない。

## 12. 受け入れ条件

- [ ] B3C-AC01: §8.1のresolver到達可能な明示検査を発行点で識別でき、fixtureでleaf code/phase/field/event伝播を確認する。
- [ ] B3C-AC02: primary/identity_validation/silence_rebuild/manual_comparisonと失敗直前の生成済件数を区別できる。
- [ ] B3C-AC03: §8.3のphase/pass・index role・truncationと、B3C拡張のraw/effective/shape range、shape provenance、隣接eventが揃い、失敗時に再計算せず検査条件を照合できる。
- [ ] B3C-AC04: 00/02の実失敗が再現した場合、一般コードだけで終わらず具体的検査が判明する。再現しない場合は原因特定の受入を未確認として残す。
- [ ] B3C-AC05: resolver試行失敗、cache/hint利用、Preview/Writer未呼出し・失敗・成功を実行事実として区別する。
- [ ] B3C-AC06: 保存要求なしは保存可否にかかわらずnot_attempted。保存実績は同一save_operation_idの実actionからのみ取得する。
- [ ] B3C-AC07: projection_inputとcomparison終端のsnapshot時点が明示され、後発処理を入力時点の完了にしない。
- [ ] B3C-AC08: cycle/attempt/ownerの所属が一致し、既存fallback・cache・再入・別resultで履歴が混ざらない。
- [ ] B3C-AC09: schema/version、legacy reason・キー・型・固定値の互換性、旧run未記録の扱いが確認される。
- [ ] B3C-AC10: raw例外/message/traceback/path/本文、任意文字列・任意object・非有限JSON値が新診断へ混入しない。
- [ ] B3C-AC11: OFF、collector障害、store障害、unknown例外でも本来の結果・例外・identity・処理回数が変わらない。
- [ ] B3C-AC12: 全8case・全revisionを検証し、artifact/diagnostic/Preview/regression/harnessが独立して報告され、exit code規則がunit testで保証される。
- [ ] B3C-AC13: §11.2の回帰が成功終了し、skip・失敗・未実施は終了コードとともに別記される。
- [ ] B3C-AC14: GUIユーザー確認、source自動検証、EXE/MMD未検証、根本修正未実施を混同しない。
- [ ] B3C-AC15: `admission_range_invalid`の失敗で、constructor直前の`effective_frame_range`実値と`event_range_status`を取得できる。値が取得不能な場合は固定理由付きで`partial/not_available`になり、推測値を保存しない。
- [ ] B3C-AC16: raw event range、shape event range、effective range、positive/required-zero range、shape provenance、隣接eventの所属が同一attempt/cycle/ownerで照合できる。
- [ ] B3C-AC17: B3C v1 optional拡張として、旧payload reader、legacy failure_context、schema/version、identity/fingerprint、通常のPreview/Writer結果に影響しない。
- [ ] B3C-AC18: 00/02相当のzero-width fixtureと、01相当の正常fixtureで、detail capture stateと製品結果を独立判定できる。detail取得成功だけで原因修復済みと判定しない。
- [ ] B3C-AC19: B3C専用シリアライザが入れ子payloadを固定allowlist・型・enum・上限で保存し、既存`MAX_DETAILS=8`のlegacy制限によってB3C detailを欠落・上書きさせない。上限超過は該当collectionの`truncated`とsectionの`partial`へ反映される。
- [ ] B3C-AC20: `phase_failed`の独立`failure_detail`経路でconstructor失敗時のdetailを保存でき、`available/partial/not_available/not_applicable`の判定がシリアライズ後の必須項目とsection statusに一致する。例外本文・args・製品結果は変わらない。

## 13. リスクと対策

| リスク | 対策 |
| --- | --- |
| phaseだけ増えて結局field/indexがunknown | 明示raiseの発行点fixtureを必須化。実00/02再現の診断品質ゲートを別に設ける |
| admission等の中間値が失われる | constructorへ渡す直前の局所値を固定detailへ変換し、失敗時にもcollectorが残る設計にする。実値が取れない場合の固定理由も検証する |
| raw/effective/shape rangeを同一視する | range種別、生成元shape、event所属、隣接関係を別フィールドにし、単一の「range」へ潰さない |
| 観測が製品の例外・比較・結果を変える | 条件・順序・メッセージ・returnを保持し、collector有無の同一fixture比較を行う |
| staleモデル、cache、二度目のcontext取得で成功を誤認 | cycle/attempt/利用元・snapshot時点を固定する |
| 文言・値型の互換性破壊 | leaf情報はoptional object。legacyコードを固定写像し、downstreamは既存列挙値内で補正 |
| debug記録が重くなる | 局所snapshot上限、既存計算値だけ、I/Oは既存store。超過時の診断品質をlimitedとする |
| 汎用sanitizerへの過信 | 専用allowlistで値を組み立てる。safe_payloadは追加防御に留める |
| ログが正しいだけでPreview修復済みと誤報 | 判定軸・exit code・報告文言を分離する |
| ASR変動で旧runの固定失敗を期待してしまう | 保存済証拠とlive再現と決定的fixtureを分ける |
| 現行ソースと実行ログの版が一致しない | build_identifierの限界を残す。新たな版識別機構は追加しない |

### 13.1 作成後のP1/P2/P3自己点検

| 分類 | 点検した阻害要因 | 本計画での解消/境界 |
| --- | --- | --- |
| P1 | raw例外漏出、デバッグ追加による製品検査変更 | §5/6/8.3/11.1で禁止・回帰条件を明示 |
| P2 | resolver内部が一般codeのまま | §8.1の発行点表、§12 AC01/04で識別粒度を固定 |
| P2 | 同じhelperの再構築/comparison、複数UI試行の混同 | §8.2/8.4のpass/cycle/attempt/consumer対応 |
| P2 | 生存しないeffective planをdumpしようとする | §8.3のpartial summaryと発行直前の局所値。plan未生成時はcandidate detailだけを保存 |
| P2 | `details_availability=not_available`のまま失敗位置だけを記録する | §8.3.1/§10.4/AC15-16でconstructor直前の派生値と生成元を要求 |
| P2 | 入れ子detailを既存`safe_details()`へ渡して静かに欠落させる | §8.3.1/§9-2/AC19でB3C専用シリアライザと固定allowlistを定義 |
| P2 | constructor直前detailのcollector受渡しが例外属性依存で失われる | §8.3.1/§9-5/AC20で独立`failure_detail`経路と統合規則を定義 |
| P3 | sectionごとの欠損理由と全体のavailabilityが混同される | §8.3.1/§10.1で`section_status`、トップレベル理由、最低限必須項目を定義 |
| P3 | collection上限が32件と16件で不一致になる | §8.2/§8.3.1でB3C固有の上限を優先する規則を定義 |
| P2 | legacyの`MAX_DETAILS=8`がB3C入れ子detailへ誤適用される | §8.3.1/§10.1/AC19でlegacy制限とB3C atomic payloadの制御を分離 |
| P3 | `not_applicable`と`available/partial/not_available`の記載が不一致になる | §4/§10.1/§11.1/AC20で成功経路の`not_applicable`を共通化 |
| P3 | `section_status`をobjectとして扱うか単一enumとして扱うか曖昧になる | §8.3.1/§10.1でobjectの各`state`をenumと明記 |
| P2 | writer/saveの将来成功を入力snapshotへ先取り | §10.3の入力/終端/save actionの時点分離 |
| P2 | 新しいstateを既存enumへ混ぜてv1互換を壊す | 新objectにstate/outcomeを追加、legacy mappingを明文化 |
| P2 | スクリプトexit 0をPreview成功と扱う | §11.3の独立判定、strict modeと優先exit code |
| P2 | voice_onlyに以前のTEXTが残る、未完了flushの誤合格 | 独立process、実input_modeとflush・ownerの検証 |
| P2 | 8case再現不能を完了扱い | 未検証はexit 1、非再現は原因特定未確認。自動download/retryで補わない |
| P3 | 03番voice_only、実行時版の断定、detail取得とPreview成功の混同 | 未検証/版不明/判定軸分離を明記 |
| P3 | B3C本体実装と拡張計画を混同する | 文書状態を`B3C base implemented / Extension planned`とし、拡張ACを未チェックで維持 |

自己点検結論: 前回レビューで指摘されたP2/P3（入れ子detailの専用シリアライザ、独立failure detail受渡し、section別availability、collection上限）と今回の再チェックで確認したP2/P3（legacy `MAX_DETAILS`との分離、`not_applicable`のenum統一、`section_status`のobject型）は本改訂で契約・実装手順・受入条件へ反映した。B3C本体でleaf失敗位置は取得済みだが、今回の拡張で必要な派生range実値と生成元、実行時ソースの厳密な版、拡張実装後の8case再現・GUI/EXE/MMD結果は未確認である。本計画で原因修復やPreview成功を先取りしない。

## 14. Codex 実装時の注意

- 本書の作成は追加実装の実行許可を兼ねない。実装依頼時に対象・現行コードを再照合する。
- 原因が判明しても、検査緩和・長音/無音処理の補正へ自動移行しない。
- 内部phaseと外側のB3B失敗分類、phase経過とstage記録順、構造検証とPreview実績を分けて扱う。
- schema/contract versionを上げず、optional拡張と補正済downstreamの識別値を使う。既存ログを修正しない。
- グローバルな診断container、thread-localへの暗黙依存、UI/core間の新しい循環importを作らない。
- 各コマンドを直列に実行し、処理の終了を確認する。待機一回の打切りを失敗判定や重複起動の根拠にしない。
- 追加エージェント、Git、依存追加、ビルド、公開、実ファイルの再配布は本計画だけを理由に行わない。
- 完了報告には変更ファイル、実装/検証結果とexit code、実失敗のleaf診断、未確認事項を含める。保存ログの構造が正しいだけで根本原因の修復を宣言しない。
