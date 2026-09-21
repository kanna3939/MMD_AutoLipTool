# MS28-B3 Implementation Plan

## 1. 文書情報

- 対象Block: `MS28-B3`
- 名称: Analysis Debug Mode / Intermediate Trace Artifacts
- 作成・改訂日: 2026-09-20
- 対象branch: `feature/MS28-B1-implementation`
- MS28位置づけ: MS20〜MS27の全体マイルストーン系列とは切り離した、Ver.1実装後の独立修正実装トラック
- 基準HEAD（既存計画の記録）: `92c8ffc Implement MS28 B2 boundary repairs`
- 文書状態: **Revised / Implementation In Progress**
- 今回の改訂: 実装前レビューのP2-1〜P2-7、P3-1〜P3-2、実run確認で発見したP1（capture状態・terminal保存順）、P2（manifest自己参照・無音補間評価）、P3（runtime識別）に加え、再実runで確認したP2-8（解析完了後の最終timing/model/analysis_text sourceがmanifestへ反映されない）を計画へ反映した。計画反映後に、同じ契約をソースと回帰テストへ適用する。
- ユーザー承認済み方針: メニュー切替、初期OFF・セッション限定、Pythonはリポジトリ直下/debug、exeはexe同階層/debug、timestamp folder、入力本体をコピーしない、保存失敗でも解析継続。

本Blockは、解析run開始時にデバッグONだった処理と、その採用結果に属する後続操作を観測する。B1/B2や無音区間の生成アルゴリズムを修正するBlockではない。

## 2. 背景

現行処理の観測順は次のとおりである。B1/B2を独立した直列stageと仮定しない。

~~~text
既存の音声読み込み結果を取得
→ Whisper timing新規生成／保持結果の再利用
→ 初期timeline
→ pre_rms境界補正（長音境界 → 非隣接同母音境界）
→ RMS取得
   ├─ 成功: RMS区間補正 → post_rms境界補正 → peak評価 → observations
   └─ 取得失敗: pre_rms結果 → fallback peak評価 → observations
→ GUIで解析結果を採用／キャンセル・失敗・破棄
→ 音声長選択 → EffectiveShapePlan → PreviewとWriter用フレームの投影・比較
→ 採用後の設定変更／再同期は結果所属を維持して別revisionへ
→ ユーザーが通常のVMD保存を要求した場合だけ実ファイル保存
~~~

現行のOutputDiagnosticsSnapshotは利用者向け診断と保存可否を扱い、diagnostic adapterは保存前にもWriter用フレームを生成する。この既存処理を利用し、B3の詳細traceを独立した診断として接続する。

無音・非ブリッジeventのgroup化は今回の調査仮説であり、group所属だけでは不正な開口の証明にならない。数値上の開口区間とRMSの関係を記録し、仮説・既存契約違反・判定不能を区別する。

## 3. 目的

- 入力、timing、境界補正、peak、shape、UI反映のどこで状態が変化したか追跡する。
- B1/B2の適用位置・分岐理由と、GUI設定が採用／拒否された理由を確認する。
- Python/exe間で実際に使用した入力・モデル・決定的な生成データを比較できるようにする。
- 無音中の数値上の開口を、長音・保持・手動調整などの説明とともに観測する。
- 解析完了時点のtiming source、実際に取得したmodel identity、analysis_text sourceをmanifestへ確定し、初期snapshotの仮値や後段の汎用値で上書きしない。
- デバッグ処理の失敗で、本来の解析・取消し・保存可否・出力を変えない。

## 4. In Scope

- 「設定/表示」のチェック式「デバッグモード」とセッション内状態。
- 試行ID、採用結果ID、出力revision、操作IDによるartifact所属管理。
- debug/runフォルダのJSON・イベント一覧CSV・安全な診断TXT。
- §8.2の実処理位置での中間状態、RMS失敗経路、GUI判断の記録。
- Preview/Writer用フレームの正規化前後の比較とprovenance対応表。
- 既存の通常VMD保存操作に対する、実保存stageの開始・取消し・成功・失敗記録。
- 確定した既存契約の検査と、無音に関する疑わしい状態の非阻害的な検出。
- workerが確定した最終入力identity metadataのtrace反映と、sourceの優先順位管理。
- 例外隔離、保存フィールド制限、/debug/の将来的なGit除外と関連回帰。

## 5. Out of Scope

- B1/B2、RMS閾値、shape grouping、製品側の補間・Preview描画・VMD形式の変更。無音区間の補間値を観測するB3診断処理は対象に含めるが、生成結果は変更しない。
- デバッグ検出を新たな解析失敗・VMD保存禁止条件にすること。
- デバッグ用に解析・Whisper・補正・VMD保存を自動再実行すること。
- 実行時の冪等性確認のために補正を二重適用すること。
- OutputDiagnosticsSnapshot、既存診断レポート、保存確認fingerprintの置換・契約変更。
- INI、presets.json、profiles.jsonへのデバッグ状態永続化。
- 入力音声、TEXT、書き起こし本文、生Whisper結果、モデル実体の保存・コピー。
- ネットワーク送信、新規依存、GUI診断オーバーレイ、ログ閲覧UIの新設。
- MMD一括出力の配布・commit処理への新規hook。本計画の実保存観測は通常の「VMD保存」を対象とする。
- バージョン変更、配布・build設定変更、正式版ビルド、リリース公開。

## 6. 前提条件

- モードは起動時OFF、セッション限定。切替だけでは再解析・旧結果への記録開始を行わない。
- 「OFF時は生成しない」は、run開始時snapshotのrecord_enabled=falseを意味する。現在のチェック状態では判定しない。
- ON開始後にOFFへ切り替えても、そのrunと採用結果の後続記録は継続する。OFF開始後にONへ切り替えても、そのrunは記録しない。
- Pythonはanalysis_debug_store.pyのプロジェクト位置から求めたリポジトリ直下/debug、frozen exeはsys.executableの親/debug。CWDやonefile展開先は使わない。書けない場合に別の場所へ暗黙に切り替えない。
- フォルダ名はローカル時刻のYYYYMMDD_HHMMSS_mmmとUUIDベースのanalysis_run_id。識別可能な入力名は含めず、既存フォルダを再利用・上書きしない。
- 本来の結果・例外・保存可否・fingerprint・警告確認状態をON/OFFで変えない。
- 保存失敗はデバッグ側の状態と安全な画面通知で扱う。部分artifact保持は、生成・保存できた範囲を保証する。
- 本改訂では、P1/P2/P3の契約を計画へ反映し、対応するsource/test変更を適用する。GUI/exeでの実run確認、正式版build、Git stage/commit、releaseは本作業の対象外とする。

## 7. 対象ファイル

### 7.1 将来の主変更候補

| ファイル | 責務 |
| --- | --- |
| src/core/analysis_debug_trace.py（新規候補） | 不変DTO、所属、safe sink、stage・検出コード、保存許可フィールド、比較 |
| src/core/analysis_debug_store.py（新規候補） | 保存先、単一I/O担当、非同期保存、manifest、JSON/CSV/TXT、保存障害 |
| src/core/pipeline.py | §8.2の境界で実行済みデータと分岐理由を取得 |
| src/core/effective_shape_plan.py | group、long run、required zero、失敗直前状態を観測 |
| src/gui_wx/analysis_worker.py | session/model identityと最終timing sourceの確定通知 |
| tests/test_ms28_b3_debug_trace.py | 最終metadata反映、source優先順位、既存trace/store回帰 |
| src/core/preview_transform.py | 実際に生成したPreviewDataの制御点・provenance取得 |
| src/vmd_writer/effective_shape_adapter.py | 実際のWriter変換の正規化前後を観測 |
| src/gui_wx/main_frame.py | メニュー、試行/結果所属、rollback連動、revision、GUI要求/採否、Preview結果 |
| src/gui_wx/ui_state.py | セッション限定モード、採用結果参照、入力変更・新規作業時の参照破棄 |
| src/gui_wx/analysis_worker.py | immutable run context、入力snapshot、timing生成/再利用、worker結果通知 |
| src/gui_wx/output_diagnostics_adapter.py | 既存Writer投影結果をB3へ通知する限定接続。既存診断DTOは変更しない |
| src/gui_wx/app_controller.py | request_save_vmdの既存処理を観測する限定hook。保存を追加実行しない |
| .gitignore | B3実装時にルート/debug/を除外する |

analysis_rollbackの既存復元可否を変更しない。main_frame側の試行contextにprior_result_refを持ち、既存rollback成否と同じ分岐で結果所属を復元する。

### 7.2 関連確認対象

- src/vmd_writer/writer.py: 既存の重複処理、最終正規化、開口epsilonを再利用するため確認する。生成契約は変更しない。
- src/core/output_diagnostics.py、src/core/diagnostic_report.py: fingerprint非混入、絶対パス等をB3へ転記しない境界を確認する。
- src/gui_wx/analysis_rollback.py: 既存rollback契約を参照する。新しい復元条件を追加しない。

### 7.3 将来のテスト候補

| ファイル（新規候補） | 確認内容 |
| --- | --- |
| tests/test_ms28_b3_debug_trace.py | DTO、stage順、所属、許可フィールド、検出分類、決定的比較 |
| tests/test_ms28_b3_debug_store.py | 保存先、衝突、原子的保存、manifest順序、CSV、漏えい、I/O障害 |
| tests/test_ms28_b3_debug_mode.py | mode snapshot、rollback/cancel/late callback、revision、UI判断 |
| tests/test_ms28_b3_pipeline_trace_integration.py | pre/post RMS、fallback、3入力経路、Preview/Writer、例外隔離、実保存通知 |
| tests/test_ms28_b3_real_input_contract.py | 02-MMD_AutoLipTool説明3相当の決定的な無音・補間fixture。実ファイル調査とは区別 |

## 8. 実装方針

### 8.1 モード、所有者、revision

- UiState.debug_mode_enabledは次回run用。チェック項目は通常の解析中も次回用として切替可能とし、現runの計算や取消し条件を変えない。
- analysis_run_idは試行ごとに新規発行する。OFFでも所属識別に必要な最小contextだけはメモリに保持し、collector/store/ハッシュ計算/artifactは作らない。
- active_attempt_refはjob_id、analysis_run_id、record_enabled、開始時入力/設定snapshot、prior_result_refを保持する。workerへ渡すcontextは不変とする。
- accepted_result_refは採用成功時だけ新規発行するanalysis_result_id、origin_analysis_run_id、record_enabled、base identity、最後の成功projection参照を保持する。失敗runのIDを旧結果へ付け替えない。
- artifactは書き込み時の「現在run」から所属を推定せず、生成時に固定したowner contextを必須とする。
- 所属照合に失敗したpayloadは保存しない。TRACE_IDENTITY_MISMATCHは信頼できる元contextがある場合だけその診断へ記録し、所属自体が不明ならセッション内通知に留める。
- projection_revisionは採用結果ごとの単調増加番号。shape設定・adjustment・出力モーフ対応・投影結果が変わる操作に付与する。
- 同じ結果の成功後再同期やcache hitは同じrevisionを再利用し、artifactを再上書きしない。記録失敗も同一stageとして再実行しない。
- 設定変更の要求にはaction_idを付け、要求値、直前revision、採否、理由を残す。拒否された候補もcandidate revisionとして関連付けられるが、採用済みrevisionへ昇格させない。
- revision identityにはbase identityに加えshape parameters、canonical adjustments、出力モーフ対応を含める。base identityだけで設定変更前後を同一扱いしない。
- 実VMD保存にはsave_operation_idと、操作開始時のanalysis_result_id/projection_revisionを固定する。

### 8.2 stageと現行関数の対応

pipelineの通常の呼び出し順を変えず、各行の実行位置で取得する。stage ordinalとrecord_sequenceを持ち、GUIの反復処理はrevision/actionに所属させる。

| stage名 | 現行関数・位置 | 取得内容・分岐 |
| --- | --- | --- |
| input_snapshot | MainFrame._run_analysis / AnalysisWorker.run | 入力モード、record_enabled、解析文字列由来、選択モデル、既存wav_analysisの安全なsnapshot |
| audio_analysis | MainFrame._run_analysis | 既に読み込み済みのduration、has_speech、speech_start/end。再解析しない。取得元はreused_input_metadata |
| whisper_timing | AnalysisWorker.run / pipeline.build_vowel_timing_plan | TEXT+音声ではpipeline内、音声のみではworker内で新規生成。編集済み再解析は保持結果をreusedとして記録。認識を追加実行しない |
| timeline_initial | build_vowel_timing_plan / build_anchor_based_vowel_timeline | 境界補正前timeline、tokensのindex/長音関係、anchorへの割当。本文は取得しない |
| pre_rms.long_boundary | _repair_long_vowel_same_morph_boundaries | before/after、判定分岐、長音境界・compact handoff |
| pre_rms.interleaved_boundary | _repair_interleaved_same_morph_boundaries | before/after、非隣接同母音の探索先・補正/skip理由 |
| rms_load | _refine_timeline_intervals_with_observations / load_rms_series | 成功時RMS時系列・窓/ホップ・範囲。既存のValueError/OSError/EOFError捕捉時はrms_unavailable |
| rms_refine | _refine_intervals_by_rms_series / _resolve_adjacent_interval_conflicts | RMS区間補正と隣接調整後、post_rms補正前のtimeline |
| post_rms.long_boundary | _repair_long_vowel_same_morph_boundaries | pre_rmsと別call siteとしてbefore/afterと理由 |
| post_rms.interleaved_boundary | _repair_interleaved_same_morph_boundaries | pre_rmsと別call siteとしてbefore/afterと理由 |
| peak_evaluation | _apply_peak_values_to_timeline / _build_peak_value_evaluations | 実際の評価窓、local/global peak、upper_limit、reason、fallback_reason、最終timeline |
| observations | _build_peak_value_observations / _annotate_micro_gap_bridge_candidates | RMS窓、候補flags、span、前後非zero index。評価関数の再呼び出しはevaluation_roleを区別し、追加計算しない |
| analysis_acceptance | _on_analysis_success / _on_analysis_error / _finish_analysis_cancelled | callback採否、model/parameter mismatch、rollback成否、結果所属。worker成功とGUI採用を分ける |
| gui_duration_selection | _selected_audio_duration_sec | selected_wav_analysis → selected_analysis_wav → selected_audio_probeの候補数値、採用元、欠損/型不正/非有限/負値の理由。パスは出さない |
| effective_shape | _build_current_ui_sync_context / resolve_effective_shape_plan | base/effective events、group所属理由、handoffs、long runs、shape、normalization、canonical adjustments、失敗直前の安全な状態 |
| preview_projection | _update_preview_display / build_preview_data_from_effective_shape_plan | 実際のPreviewData、placeholder、成功/失敗/skip。内部catchで表示だけ失敗した場合も記録 |
| writer_projection | build_output_diagnostics_snapshot_from_ui_state / build_morph_frames_from_effective_shape_plan | 既存診断が生成したWriter用フレームの正規化前後。adapter_failedも取得 |
| projection_comparison | 上記の同一revision両結果が揃った後 | §8.6の比較。片側欠損はnot_evaluableであって一致ではない |
| gui_generation_request | commit_generation_settings | 型・busy・同値・profile guard・resolver・履歴commit各分岐の要求値/採否/拒否コード。_project_generation_controlsによる表示復元も関連付ける |
| vmd_file_save | AppController.request_save_vmd | 既存要求のblocked、dialog/warning取消し、writing、succeeded、failed。通常の保存関数の戻り/例外を観測 |

RMS取得失敗時はrms_refineとpost_rmsの両補正をskipped(reason=rms_unavailable)とし、pre_rms結果へ既存fallback peakを付与してobservationsへ進む。空入力などの早期終了も未到達stageを成功扱いしない。

初期timelineとobservationsのinitial_intervalは同一ではない。後者は現行関数ではpre_rms補正後を参照するため、対応するstage identityを明記する。B1/B2名だけから境界を推定しない。

### 8.3 B1/B2とGUI判断の記録

- 境界補正は共通のboundary_repairs.jsonへ記録し、repair_function、call_site(pre_rms/post_rms)、contract_tags、event_index、before/after、changedを保存する。
- skip理由はafter比較から推測せず、既存分岐で取得する。different_vowel、not_target、already_satisfied、insufficient_span、timeline_limit等の固定コードと判断に使った数値を持つ。
- B1/B2混在関数を分割・再設計しない。contract_tagsは帰属説明であり、追加の適用順を意味しない。
- long source/continuation/terminal、same-frame/compact handoff、canonical zero、hold/decayは、それを実際に決定するpipelineまたはresolverで記録する。
- 補正できず未変更の状態と、後続resolverが既存契約でfail-closedした事実を別stageとして保存する。
- GUIの音声長採用元、要求した生成設定、拒否して戻した設定はgui_actions配下に残す。ユーザーが操作した値が戻る現象も調査できるようにする。
- 冪等性の実行時判定欄は設けず、§11.2のテストで決定的データだけを検査する。

### 8.4 観測・契約検査と無音定義

検出レコードはcode、classification、evaluation_status、対象event/shape/frame区間、根拠stage、測定値、explanation_codesを持つ。

| classification | 意味・例 |
| --- | --- |
| suspicious | ZERO_PEAK_EVENT_GROUPED_WITHOUT_BRIDGE、OPEN_INTERVAL_IN_SILENCE。調査候補であり解析/保存を禁止しない |
| explained | 上記の観測にhold、long_vowel_hold/decay、manual_peak/interval/tail/crossfade、許可されたbridge等の理由が対応する |
| contract_violation | 既存required-zero欠落/衝突、B2境界検証の既存失敗、§8.6の比較不一致、TRACE_IDENTITY_MISMATCH |
| not_evaluable | RMSや投影結果の欠損、coverage不足、保存前の実ファイル、対応不能。正常扱いしない |

- peak_value=0だけで無音としない。upper_limit_zero、below_abs_threshold、below_rel_threshold、no_peak_in_window、rms_unavailable、手動変更を区別する。
- group所属だけでは開口残存を断定しない。構造候補と開口測定を別レコードで関連付ける。全eventがzeroのgroupや上限0を開口違反扱いしない。
- MISSING_TERMINAL_ZEROは既存normalization contractが要求するzeroの欠落を対象とする。全shapeへ新しい開始/終了zero規則を課さない。
- 既存resolverの例外はそのまま維持する。新しいデバッグ検出から例外を投げたり、成功扱いへ変更したりしない。

無音測定のB3診断専用定数は次で固定し、実行時に使用した値をartifactへ保存する。製品側閾値は変更しない。

| 項目 | 定義 |
| --- | --- |
| RMS閾値 | 線形振幅RMS < 0.01を無音候補。現行絶対閾値に合わせた診断値。相対閾値によるpeak=0は別情報 |
| 最小継続時間 | coverageが連続した無音候補が0.10秒以上。短いgapは別の観測として保持するが、この検出には含めない |
| サンプルcoverage | 有効サンプル中心の前後hop_sec/2を担当区間とし、音源範囲へclip。欠損・非有限値や隣接間隔>1.5 hopは未観測区間とし、無音で埋めない |
| frame対応 | VMD_FPS=30。完全に無音区間内に入る半開frame cell [f/30, (f+1)/30)を評価。境界計算の許容差は1e-9秒 |
| 開口判定 | MORPH_FRAME_OPEN_EPSILON=1e-9を超える値。制御点の有無だけでなく、区間を線形補間してcell内の正値区間を求める |
| 評価範囲 | source_duration_frames内。必要な前後制御点がなく補間境界を確定できない部分はnot_evaluable。required-zero欠落は別に検査 |
| 理由の対応 | resolved_tail、long_vowel_runs、canonical adjustments、enabled handoffsから根拠indexと影響区間を付ける。理由が存在するだけで全区間を免除しない |

無音区間の補間評価は、制御点の存在確認だけで終了させない。各母音のWriter投影系列をframe順に取り出し、無音区間と交差する半開frame cellごとに、前後の有限な制御点から線形補間値を求める。無音区間内の正値制御点は`positive_control_point`、制御点間の正値区間は`positive_interpolation`として分離し、最大値・区間・source shape/eventを記録する。前後の制御点が揃わず境界を確定できない場合だけ`not_evaluable`とし、制御点が無いことを補間未評価の理由にしない。

rms_analysis.jsonには可能な範囲の全RMS系列・coverage・無音区間を保存し、eventのpeak窓だけから区間全体の無音を推定しない。RMS不足と真の0を区別する。

Previewの各segmentと正規化後Writer系列の両方について補間後の開口を記録し、複数shapeの区間をunionする。ここでの実開口は数値契約上の区間であり、画面pixelや実MMDの見た目を測定したという意味ではない。制御点が無音区間の外にしかないケースも対象とする。

### 8.5 成果物と保存許可フィールド

すべての構造化記録にschema_version=1、owner_kind、analysis_run_id、analysis_result_id（採用前はnull）、projection_revision/action_id/save_operation_id（該当時）、record_sequence、stage、状態、タイムゾーン付き時刻を付ける。列挙した安全なprimitiveへ明示変換し、汎用asdict、__dict__、reprによる一括dumpを禁止する。

~~~text
debug/<YYYYMMDD_HHMMSS_mmm>_<analysis_run_id>/
  manifest.json
  audio_analysis.json
  rms_analysis.json
  whisper_timing.json
  timeline_initial.json
  timeline_pre_rms.json
  timeline_post_rms_raw.json
  timeline_refined.json
  peak_observations.json
  boundary_repairs.json
  events.csv
  diagnostics.txt
  gui_actions/<action_id>.json
  projections/<revision>/
    effective_shape_plan.json
    preview_controls.json
    writer_frames.json
    provenance.json
    comparison.json
    silence_observations.json
    events.csv
  saves/<save_operation_id>.json
~~~

未到達・失敗したstageのデータファイルは必須ではない。manifestにskipped/failed/not_evaluableと理由を残す。失敗前の許可済み部分snapshotはpartialとして保存できる。

| artifact | 保存を許可するpayload |
| --- | --- |
| manifest.json | §8.7のidentity、安全な数値/enumの設定、mode snapshot、runtime識別、job/run/result/revision/operation ID、stage状態、固定コード、artifact相対名・size・digest・sequence、capture状態、復元先ID。manifest自身は自己参照を作らずartifact一覧から除外する |
| audio_analysis.json | duration、sample rate、channels、has_speech、speech_start/end、既存metadataの由来、解析対象identity参照 |
| rms_analysis.json | times、values、window/hop情報、coverage、診断定数、無音区間、欠損理由 |
| whisper_timing.json | model identityの安全な部分、generated/reused/fallback、再利用元ID/digest、anchor index/start/end、対応token/event index、固定warning code。word/segment本文は除外 |
| timeline_*.json | stage別event index、5母音enum、time/start/end/duration/value/peak、長音token/source関係 |
| peak_observations.json | peak窓、local/global RMS、upper_limit、zero/fallback理由、sample数、候補flags、span、前後nonzero index、参照RMS範囲 |
| boundary_repairs.json | §8.3のbefore/after数値・metadata、分岐コード、対象index、contract_tags |
| effective_shape_plan.json | base/effective event、canonical adjustment数値/enum、shape/group/control point、long run、handoff、normalization contract、tail/crossfade、決定的digest |
| preview_controls.json / writer_frames.json | revision、モーフ対応、実制御点/フレーム、正規化前後の系列、投影status。実保存成功の意味を持たせない |
| provenance.json | §8.6の多対多対応、point_kind、required_zero、由来index、正規化の追加/統合/削除 |
| comparison.json / silence_observations.json | 比較条件、許容差、差分位置、分類、測定区間、根拠index、説明コード |
| gui_actions/*.json | 操作enum、要求/直前/採用後の数値・enum設定、duration候補と採用元、accepted/rejected/noop、固定理由コード、関連revision |
| saves/*.json | operation所属、requested/blocked/cancelled/writing/succeeded/failed、理由コード、保存に使用した投影digest。出力パス/本文は含めない |
| diagnostics.txt | 上記のsafeレコードから生成した固定テンプレート文、ID、stage、数値、コードのみ。既存診断レポートをそのまま転記しない |
| events.csv | 次の固定列だけ。本文、パス、任意の自由文は含めない |

イベントCSV列は次で固定する。

~~~text
schema_version,analysis_run_id,analysis_result_id,projection_revision,stage,
event_index,vowel,start_sec,time_sec,end_sec,start_frame,peak_frame,end_frame,
peak_value,local_peak,global_peak,zero_reason,fallback_reason,
same_vowel_bridge,cross_vowel_bridge,burst_candidate,
long_role,long_source_index,shape_group_ids
~~~

root/events.csvは最終pipeline timelineとobservationsが得られた場合に1回生成し、採用前のresult/revision/group欄は空欄とする。projections/<revision>/events.csvはそのrevisionのevent/shape対応が得られた場合に生成する。groupは複数なら固定区切りでindexを並べる。行順はevent_index、UTF-8、改行LF、標準CSV引用符規則、数値はロケール非依存、欠損は空欄とする。reason等は固定enumだけを許可し、任意文字列をセルへ流さない。

生Whisper結果、解析本文・書き起こし・ひらがな本文、絶対パス、モデル保存先、未加工の例外・traceback、任意のpreset/profile表示名を保存しない。入力basenameは承認済み項目としてmanifestのfile identity欄だけに許可し、制御文字と区切り文字を除去する。ファイル名に利用者情報が含まれる可能性は残り、匿名化済みと説明しない。

例外は捕捉箇所と型を固定コードへ分類する。未知の例外はDEBUG_INTERNAL_ERROR等へ置き換え、type名も許可表外ならgenericとする。既存アプリの例外表示契約は変更せず、B3への転記だけを制限する。

### 8.6 Preview / Writer比較とprovenance

同じ採用結果・同じprojection revisionから得た実データだけを比較する。比較用にresolverを再実行しない。

1. raw対応: 実PreviewDataのvowel/frame/value/point_kindと、同revisionのEffectiveShapePlan制御点を照合する。shape/eventの対応もここで検査する。
2. 正規化前: Writer adapterの実変換前系列を取得し、Preview側の実制御点から得た系列と共通表現へ変換する。shape計算をやり直して同じ値同士を比較しない。
3. 共通正規化: Preview側系列のコピーに、同revisionのnormalization contractと既存Writer最終正規化関数を適用する。Writer側は実adapterが生成した正規化後系列を使う。
4. frame集合・母音・required-zeroの存在と値を比較し、raw/provenance/normalizedのどこが不一致か記録する。
5. 正規化差分をprovenance表へ対応付ける。比較処理の結果をPreviewやWriterへ戻さない。

共通表現は(frame_no: int, internal_vowel: enum, value: finite float)。内部母音順は「あ/い/う/え/お」とし、frame→母音順でsortする。Preview表示名とWriterの出力名はrevisionのoutput_morph_names対応表で内部母音へ戻す。未知/非一意の対応はnot_evaluableとする。

重複(frame,morph)は消す前の多重集合を保存し、既存_merge_duplicate_morph_framesと同じ規則で処理する。正値同士は最大値、正値と非正値は正値、非正値同士の重複は0。単独点の値をB3が勝手に丸めたりclampしたりしない。その後の短区間正規化、許可範囲外除去、冗長zero削除も既存順序・保護範囲を用いる。

frame・enum・indexは完全一致、値は絶対差<=1e-9（相対許容差0）、非有限値は比較不能とする。epsilon以下の値とrequired-zeroの存在判定を区別し、数値が近いことだけで欠落keyを一致扱いしない。実VMDのfloat32バイナリ比較は対象外。

provenance表の1行はorigin_shape_id、source_event_indices、raw_point_id、point_kind、required_zero、raw_key、normalized_key、normalization_action、origin_kindを持つ。統合は複数origin→1key、削除はnormalized_key=null、追加点はorigin_kind=normalization_generatedとし、Writerに失われたpoint_kindを捏造しない。

Writer投影成功はwriter_projection=completed。vmd_file_saveは初期not_requestedで、ユーザーの通常保存操作ごとに独立したoperationとなる。保存dialog取消し、既存警告の拒否、保存不可をそれぞれcancelled/blockedとして記録し、既存生成関数の正常復帰でのみsucceededとする。保存成功はディスク内容の独立再検証を意味しない。

### 8.7 input identity

| 対象 | identityと取得契約 |
| --- | --- |
| source_audio | 元音声のbasename、bytes、SHA-256、hash_observed_at、取得status。内部WAVと混同しない |
| analysis_wav | workerが実際に渡した内部解析WAVの同項目、元音声との由来relation、existing audio metadataのsnapshot |
| text_file | TEXTがある場合のbasename/bytes/SHA-256。音声のみはnot_applicable |
| analysis_text | workerに渡す、または認識/編集で得た実際の文字列のUTF-8 digestと文字数、text_file/whisper/user_editedのsource enum。本文は保存しない |
| timing | generated/reused/fallback、anchor時刻/index等の安全な構造digest、再利用元result/run ID（分かる場合）、retained model identity。本文由来token payloadは含めない |
| model | 選択・verified request・実session・retained timingのmodel_key/manifest identity/package versionなど安全な識別値。path/任意のruntime objectは除外 |

- TEXT+音声では読み込み済みselected_text_contentのsnapshot digestとディスクファイルdigestを区別する。
- 音声のみでは認識で得たanalysis_textを対象とする。編集済み再解析では編集済み文字列と再利用timingを別identityにし、新規認識と記録しない。
- ファイルハッシュは§8.8のI/O担当で読み、前後のsize/更新情報が変化した場合はchanged、読めなければunavailable。失敗を解析失敗にしない。
- 非同期のファイル読み取りは、それだけではWhisper/RMSが読んだ全byteと同一だった証明にならない。binding_status=observed_onlyを既定とし、読み込み済みmetadata/利用時snapshotとの対応証拠がある場合だけmatchedとする。
- 解析文字列は使用した不変snapshotをhash対象にする。digest算出のための一時的なメモリ参照を許可するが、storeのファイルpayloadには文字列を渡さない。
- input identityの部分欠損、モデル不一致、file changedをmanifestへ残し、比較不能の理由にする。現在のパスを後から読むだけで解析入力の同一性を保証しない。
- 初期snapshotの`pending`/`unknown`や`model.status=unavailable`は暫定値であり、verified session取得後にmodel identityを、timing plan確定後に最終timing sourceをtraceへ反映する。解析がその段階へ到達しない場合だけ暫定値を残す。
- `analysis_text.source`は情報量の高いsource（`text_file`、`whisper_transcription`、`user_edited_transcription`）を、pipeline内部の汎用`provided`記録で降格させない。digest/文字数の更新とsourceの確定を分離する。
- identityと設定のsemantic digestにはrun ID、時刻、保存場所、debug mode、記録順序を含めない。既存save_state_fingerprintとは別物とする。

runtime identityは、source/frozenの実行形態、実行ファイルbasename、Python runtime version、アプリケーションversion、利用可能なbuild identifierだけを保存する。絶対パス、環境変数全体、ユーザー名、任意のruntime objectは保存しない。build identifierが取得できない場合は`unavailable`とし、解析結果の成否へ影響させない。

### 8.8 例外隔離、I/O、保存順

| 境界 | 失敗時の扱い |
| --- | --- |
| collector/snapshot変換 | debug contextのcapture_statusをdegradedにし、その記録を破棄。本来の値・例外を変更しない |
| 構造/契約検査・比較 | 検査自体の失敗はnot_evaluable + debug内部コード。生成処理の失敗へ変換しない |
| serializer/許可フィールド検査 | 許可外/非有限/型不正を安全に分類し、そのartifactを保存しない |
| store/mkdir/hash/write/replace | capture_status=unavailableまたはdegraded。取得できたデータのみ保持し、通常処理を継続 |
| UIへの通知 | セッション内の独立したdebug通知へ集約。通知失敗を通常処理へ再throwしない |

本来のresolver・Whisper・保存関数のtry/except範囲とdebug呼び出しの例外範囲を分ける。debug wrapperは本来の計算全体を包んで失敗を握り潰すものにしない。既存の例外型・failure_class・rollback判定を維持する。

debug警告・run ID・時刻はOutputDiagnosticsSnapshot、DiagnosticItem、save_state_fingerprint、confirmed_warning_save_state_fingerprint、既存の保存可否へ追加しない。既存の診断TXTも変更しない。画面通知はmain_frameのセッション内debug通知として固定文を用い、既存Warning診断へ注入しない。

- GUI/解析workerは安全な不変snapshotと所属を渡す。GUIで追加のファイルhash・JSON整形・ディスク書き込みを行わない。
- セッション最初のON runで単一debug I/O担当を遅延起動する。以後、全runのmkdir・hash・serializer・write・manifest更新をこの担当へ直列化する。
- bounded queue（64要求）へ非blockingで投入し、満杯時はdebug側をdegradedとする。計算を待たせず、無制限に溜めない。通知用の上限付きメモリ状態にdrop件数を残す。
- 同一runへの連続submitはrun単位でcoalesceし、キューには最新状態を反映する保存要求だけを残す。workerが保存中に新しいrecordを受けた場合は、保存完了後に一度だけ最新snapshotを再保存し、同じmutable traceの古い状態を最終manifestにしない。
- 同一runのrecord_sequence採番と試行terminalのsealを短い同期区間で直列化する。seal後はworker由来の新規記録を受け付けず、seal前に受け付けたqueueは所属を変えず順に確定する。採用結果由来のrevision/操作は別の権限で追記する。外部producerはmanifestを直接更新しない。
- 順序は、run directory作成 → 初期manifest → stage artifactの同一directory内一時ファイル書き込み/replace → 成功したartifactの相対名・digest・sequenceをmanifestへ反映 → terminal/checkpoint更新とする。
- manifestは常に最後に原子的replaceする。artifact保存後にmanifest更新が失敗した場合、そのartifactは未登録の部分成果物として扱い、成功登録済みと主張しない。
- 同一revisionのartifactは不変とし、追加のrevision/operationへ追記する。manifestと集約diagnostics.txtのみ更新可能。更新のqueue受付とディスク確定を区別する。
- workerはverified session取得後にmodel identityを、timing plan確定後に最終timing sourceをtraceへ通知する。pipeline内の汎用`provided`記録は、workerが確定した`text_file`/`whisper_transcription`/`user_edited_transcription` sourceを降格させない。
- terminal成功時は、最終stageとcapture状態`completed`を同一の保存世代へ含める。I/O例外またはqueue dropが実際に発生した場合だけ`unavailable`または`degraded`とし、保存済みartifactが揃っていることだけを理由に成功へ書き換えない。
- 既に存在するrun folderや他runのファイルを上書きしない。通常削除・自動ローテーションは追加しない。
- フォルダ作成不能ならディスク上のmanifest/部分artifactは保証しない。メモリ上のcapture_statusと安全な通知だけを保証範囲とする。
- 容量不足・replace失敗・強制終了では最後に確定したmanifestとartifactまでを保証し、未到達/未確定のstageを完了扱いしない。アプリ終了をdebug flushのために無期限に待たせない。

## 9. 詳細ステップ

1. 所属context、stage/状態enum、許可フィールド、semantic digestを定義する。
2. safe collectorと単一I/O担当を実装し、OFF無生成・例外隔離・保存順を先に検証する。
3. §8.2どおりpipelineのpre/post RMS、fallback、observationsを観測する。
4. resolver、Preview、既存Writer投影へhookし、provenance・共通正規化比較を実装する。
5. 無音測定を製品計算から独立させ、説明可能例・判定不能を含めて検証する。
6. メニュー、run開始snapshot、採用/rollback、revision、GUI要求/拒否を接続する。
7. 通常のrequest_save_vmdへ所属固定の観測を追加する。保存を追加実行しない。
8. workerのverified session/timing plan確定点からtrace metadataを更新し、source優先順位を維持する。
9. JSON/CSV/TXTとmanifestを揃え、B3実装時に/debug/のGit除外を追加する。
10. §11の決定的回帰・障害注入・非混入テストを実施し、§12を照合する。
11. 実Whisper/GUI/exe確認は実施した範囲だけ別記し、未実施を完了根拠へ混ぜない。

## 10. 状態遷移 / データ契約

試行status、projection status、実保存status、capture statusは独立させる。

~~~text
run開始（ON/OFFをsnapshot）
  started
    ├─ worker成功 → worker_completed → GUI採用 → adopted
    │                                      ├─ 初期投影/比較完了 → completed
    │                                      └─ 投影失敗 → completed_with_projection_failure
    ├─ 取消し要求 → cancel_requested → 既存terminal判定 → cancelled
    ├─ 本来の解析例外 → failed
    ├─ 入力/model/parameter変更、job失効 → discarded
    └─ active試行中のアプリ終了 → interrupted（通知の保存はbest effort）

採用結果の後続操作
  projection revision → completed / rejected / failed / not_evaluable / interrupted
  vmd_file_save       → not_requested（初期）
                     → requested → blocked / cancelled / writing → succeeded / failed / interrupted

debug capture
  disabled（OFF開始）
  recording → degraded / unavailable
~~~

- 主責任はMainFrameの既存job照合を通ったterminal処理。workerはworker_completed/failed相当の証拠を通知するだけで、GUI採用・run最終完了を確定しない。
- _complete_analysis_terminalで既存参照を消す前にowner contextをローカルに確保し、その後の初期syncまで同じresult参照を渡す。
- callbackの判定優先順は既存どおり、job guard → parameter一致 → cancel_requested → 成功結果のmodel照合/通常のエラー処理とする。parameter不一致と取消し要求が同時なら、既存分岐に合わせdiscardedを記録する。取消し分岐へ到達した場合はcancelledとし、新結果を採用しない。worker内の途中artifactが残ることと結果採用は別である。
- terminalは試行につき1回確定し、後続のprojection/save操作で試行の成功/失敗を再判定しない。completedは実VMD保存完了を意味しない。
- rollback以外の分岐で旧結果が有効なまま維持される場合も、所属はその旧結果のままとする。既存処理が結果を無効化した場合はaccepted_result_refを破棄する。debug状態だけを理由に旧結果を復元・無効化しない。

| 状況 | artifact所属と状態 |
| --- | --- |
| ON→OFF（解析中/採用後） | record_enabled=trueの元runへ継続。次回runだけOFF |
| OFF→ON | 現run/採用結果へ遡及生成しない。次回ON runから開始 |
| 再解析BがAをrollback復元 | Bはfailed/cancelledとrestored_result_idだけ記録。復元したAのPreviewはAのresult/revisionへ。AがOFF由来なら生成しない |
| 成功後再同期/cache hit | 同一result/revisionを再利用。mode変更で所属を変えない |
| 設定変更/undo/redo | 同一resultの新revisionとして記録。拒否はaction/candidateのみ、旧成功revisionを維持 |
| 入力変更/新規作業 | active attemptを既存失効処理に連動してdiscardedとし、accepted_result_refを破棄。debug_mode_enabledはセッション内で維持 |
| late callback | 既存job guardで不採用。別runにも旧terminal確定済みstageにも書かない。受信済み途中artifactは保持 |
| model/parameter不一致 | 既存の不採用/rollback禁止判断に従い、固定理由を元runへ記録 |
| アプリ終了 | active試行だけをinterruptedとして通知する。採用済み試行のterminalは変更せず、後続projection/saveの進行中stageのみinterruptedとしてbest effortで記録。既存終了を妨げず、未確定書き込みの成功は保証しない |
| 実保存中に別の所属へ遷移 | 開始時に固定したsave operationの所属を維持。現在の結果へ付け替えない |

同じrunにはterminalまでのworker段階と、採用結果に属する後続revision/操作を保存できる。terminal後のworker callbackを受け付けないことと、正当な後続操作の追記は区別する。

workerの計算終了、GUIの採用、debug queue投入、ディスク確定の4点は別の状態である。manifestのcomplete表示は確定済みartifactだけに対応し、失敗した比較はfailed/not_evaluableを残す。比較不一致はrun成功を取り消さず、検出結果として記録する。

## 11. テスト方針

### 11.1 所属・保存・副作用

- 起動時OFF、非永続化、OFF開始でcollector/store/hash/dirなし。ON開始で規定のrootと衝突しないfolder。
- ON→OFFとOFF→ONの解析中/採用後切替、成功後再同期、cache hit、設定変更・拒否・undo/redoを確認する。
- A成功→B失敗/取消し→A復元、AがOFF/BがONおよび逆、rollback不可、入力変更、model/parameter mismatch、late callback、二重terminalを確認する。parameter不一致と取消しの同時発生、terminal seal前後のqueue投入も含める。
- 終了中の未flush、stage未到達、partial、artifact成功後manifest失敗、mkdir/hash/serializer/replace失敗、queue満杯を確認する。
- collector・checker・serializer・store・通知それぞれへ例外を注入する。本来成功する解析は成功、本来失敗する解析は同じ例外・rollback結果を維持する。
- ON/OFF・debug障害時でtimeline、metadata、EffectiveShapePlan、Preview、Writerフレーム、保存可否、save_state_fingerprint、警告確認状態が同一。
- 書き込みは単一I/O担当が行い、GUI callbackは追加ディスクI/Oやhash完了を待たない。
- frozen/CWDを模擬して保存rootを検査する。Git除外は将来の実装検証時に確認し、今回Git操作は行わない。

### 11.2 B1/B2・入力経路・GUI判断

- pre_rmsの長音→非隣接補正、rms_refine、post_rmsの同順、peak、observationsの順序と取得位置を確認する。
- RMS取得失敗ではpost_rmsがskippedになり、fallback peak/observationsが記録される。
- hold/decay、same-frame/compact handoff、非隣接同母音、適用不要、補正不能、既存fail-closedを含める。
- 冪等性はテストでだけ補正を再適用し、補正後timeline・metadataと、同じshape parameters/adjustmentsによるEffectiveShapePlanの決定的フィールドが同一か検査する。
- 比較対象からrun ID、時刻、record_sequence、適用/skip理由などのtrace情報を除外する。毎回異なり得るtrace全体の一致を要求しない。
- duration選択の3候補・不正値・候補なし、generation要求の採用/拒否/noopと表示復元を確認する。
- TEXT+音声、音声のみ、編集済み書き起こし再解析を決定的fixtureで通す。文字列変更でanalysis_text digestが変わり、timing再利用とmodel所属が保たれることを確認する。
- worker成功後のmanifestで、音声のみの`whisper_transcription`、TEXT+音声の`text_file`、編集済み再解析の`user_edited_transcription`がpipelineの汎用`provided`へ降格せず、最終timing source/model identityが暫定値から更新されることを確認する。
- ファイルhash changed/unavailable/observed_onlyを正常解析と区別して記録する。

### 11.3 比較・無音・実保存

- raw Preview、Writer投影、provenanceの片側だけを改変して検出できることを確認し、同じ再計算結果同士の自己比較を避ける。
- 出力名の日本語/ラテン対応、重複positive/zero、正規化の削除/追加、required-zero、1e-9境界、非有限値、片側投影失敗を確認する。
- 無音閾値0.01、最小0.10秒、frame cell境界、RMS欠損/非有限/不連続、相対閾値zero、upper_limit=0を確認する。
- 無音内に制御点がなく前後の補間で開く例、groupだけ伸びて値は閉じている例、全zero groupを含める。
- hold/long-vowel/manual adjustment/bridgeに由来する説明可能例と、説明不能な疑わしい例を分ける。診断で生成値を変えない。
- Writer投影のみではvmd_file_save=not_requested。通常保存要求のblocked、warning/dialog取消し、成功、実保存失敗を記録し、debug失敗は保存結果を変えない。
- 既存生成関数を模擬した保存stageテストと、実VMD保存の確認は区別する。

### 11.4 個人情報・成果物

- 固有のダミー本文、書き起こし、絶対パス、モデルpath、本文/path入り例外、任意display nameを全入力DTOへ与える。
- 全JSON（manifest・partial・error含む）、全CSV、diagnostics.txt、一時ファイルのpayloadへ禁止値が含まれないことを検査する。
- basenameだけはmanifestの許可欄に現れることを確認し、本文やパス全体とは別にassertする。
- unknown field/任意error detailの一括dumpを拒否し、固定コードに置換する。
- CSVの固定列、型、UTF-8、引用符、空欄、event順、rootとrevisionごとの生成条件を確認する。
- 未到達artifactを必須扱いせず、manifestのstatusと実際の確定ファイルが対応することを確認する。

### 11.5 実行境界と終了条件

決定的fixtureと障害注入を必須とする。実Whisperでのsample解析、native wxメニュー操作、exe保存root、実MMDの見た目は、実施したものだけ別に記録する。自動テストは実機確認の代替としない。必要な関連テストが通り、具体的な未解決リスクがなければ検証を終了し、未実施範囲を明記する。

## 12. 受け入れ条件

- [ ] B3-AC01: メニュー切替、初期OFF・非永続化、run開始snapshot基準のON/OFFが§6・§8.1どおり。
- [ ] B3-AC02: Python/exeの保存root、timestamp folder、自動作成、衝突回避が規定どおり。
- [ ] B3-AC03: 試行/採用結果/revision/操作の所属が分離され、rollback/cancel/late callback/入力変更/再同期で混在しない。
- [ ] B3-AC04: pre_rms/post_rms、RMS失敗経路、初期と補正後timeline、peak/observationsを区別できる。
- [ ] B3-AC05: B1/B2のbefore/after・skip・fail-closed、GUI duration採用元、generation要求/採否/拒否理由が確認できる。
- [ ] B3-AC06: 正規化前後、モーフ名、重複、数値許容差、provenanceを含む比較が§8.6に一致し、片側改変を検出できる。
- [ ] B3-AC07: Writer投影と実VMD保存が別stageで、未保存を成功扱いせず、通常の保存操作を追加実行しない。
- [ ] B3-AC08: 無音の閾値/coverage/frame/補間開口を記録し、疑わしい状態・説明可能・既存契約違反・判定不能を区別する。
- [ ] B3-AC09: 元音声/解析WAV/TEXT/実解析文字列/timing/modelのidentityを区別し、3入力経路とhash取得不能が検証される。
- [ ] B3-AC10: §8.5の許可フィールドのみを保存し、JSON/CSV/TXT/partial/errorへ本文・絶対パス・生例外が漏れない。
- [ ] B3-AC11: collector/checker/serializer/storeの例外を隔離し、本来の解析・保存の成功/失敗・rollbackを維持する。
- [ ] B3-AC12: debug警告が既存OutputDiagnostics/fingerprint/保存可否/警告確認状態へ混入しない。
- [ ] B3-AC13: I/O単一担当・非blocking投入・artifact先行/manifest後更新を守り、保存不能時は保証範囲に応じた安全な通知を行う。
- [ ] B3-AC14: 解析失敗/取消し時に保存済み部分artifactを保持し、未確定・作成不能のmanifestを存在/完了扱いしない。
- [ ] B3-AC15: root/revisionイベントCSVのファイル名・列・生成条件とmanifestが一致する。
- [ ] B3-AC16: 冪等性はテスト内の決定的timeline/metadata/EffectiveShapePlanのみで検証し、実行時に補正を増やさない。
- [ ] B3-AC17: ON/OFF・debug障害時の決定的出力と既存状態が一致し、将来の実装で/debug/がGit除外される。
- [ ] B3-AC18: 成功したterminal runは最終stageと`capture_status=completed`を同一runへ保存し、同一runの連続submitをcoalesceする。保存失敗・queue drop時だけ`unavailable`/`degraded`を記録する。
- [ ] B3-AC19: manifest自身をartifact一覧へ自己登録せず、artifact一覧に記載された全ファイルのsize・SHA-256・sequenceが最終ファイルと一致する。
- [ ] B3-AC20: RMS無音区間について、制御点内の正値と制御点間の線形補間による正値を別分類で記録し、境界制御点不足時だけ`not_evaluable`になる。
- [ ] B3-AC21: manifestへsource/frozen、実行ファイルbasename、Python runtime、アプリversion、任意のbuild identifierを安全な値だけ記録し、取得不能は`unavailable`として解析結果へ影響させない。
- [ ] B3-AC22: verified model session取得後のmodel identity、timing plan確定後の最終timing source、analysis_text sourceの優先順位が最終manifestへ反映され、暫定`pending`/`unknown`や汎用`provided`へ不意に戻らない。到達前の失敗では暫定値を保持する。

## 13. リスクと対策

| リスク | 対策・検証 |
| --- | --- |
| 失敗runへ旧結果が混入 | 試行/採用結果参照を分離、rollback同一分岐で復元（AC03） |
| OFF切替で途中traceが切断 | run開始snapshotを後続操作も継承（AC01/03） |
| B1/B2の発生位置を誤認 | 実関数とpre/post RMS、GUI判断を対応付け（AC04/05） |
| 正規化差を不具合と誤認 | raw/normalizedを分離、既存正規化・provenanceを利用（AC06） |
| 無音の誤検出・補間区間の見逃し | coverage、補間開口、意図の理由、判定不能を分離（AC08） |
| 同じ音声でも解析本文が違う | analysis_textとtiming reuseのidentityを独立記録（AC09） |
| 本文/パスが例外やDTO経由で漏れる | allowlistと固定コード、全形式の漏えいテスト（AC10） |
| debug失敗が本来の結果へ伝播 | 各境界の例外隔離と既存fingerprint非混入（AC11/12） |
| GUI停止・メモリ増加 | 単一I/O担当、bounded queue、満杯時degraded（AC13） |
| mkdir/容量不足/強制終了 | 保存できた範囲だけを保証、manifest確定順序を保持（AC13/14） |
| ディスク使用量の増加 | セッション限定の明示ON。自動削除を追加せず、利用者が終了後に管理 |
| 保存前のフレームを実保存と誤認 | 別stage・別operation・not_requested（AC07） |
| Git混入 | 将来のB3実装でルート/debug/を除外。強制addや既追跡の除外を保証しない（AC17） |

## 14. 実装時の注意・レビュー対応

- 本Blockは観測の追加である。今回の原因仮説を新しいhard errorや生成規則へ昇格させない。
- 各hookは既存処理の実行結果/分岐から記録し、診断のためにWhisper、補正、resolver、保存を追加実行しない。比較用の数値正規化は副作用のないコピーだけに行う。
- 既存fail-closed、cancel、rollback、late callback、診断表示、保存警告確認を維持する。
- GUIの追加ファイルI/O、未加工DTOの保存、既存診断TXTの転記を避ける。
- 今回適用したP1/P2/P3の主変更は`analysis_debug_store.py`、`analysis_debug_trace.py`、`analysis_worker.py`、`main_frame.py`、`test_ms28_b3_debug_trace.py`である。B3の既存実装範囲外へ広げず、GUI/exeで未確認の受け入れ条件は未検証として残す。
- version、MS27完了状態、INI/preset/profile、配布/build契約を変更しない。
- 実装後は関連テスト、必要なGUI/exe確認、未検証範囲を区別して報告する。

| レビュー指摘 | 解消する節 | 対応する受け入れ条件 |
| --- | --- | --- |
| P2-1 run/採用結果/rollback/切替 | 6、8.1、10、11.1 | AC01/03/14 |
| P2-2 B1/B2 stage位置・GUI判断 | 2、8.2、8.3、11.2 | AC04/05 |
| P2-3 Preview/Writer比較・保存の意味 | 8.5、8.6、10、11.3 | AC06/07 |
| P2-4 無音検出の確度・補間 | 3、5、8.4、11.3 | AC08 |
| P2-5 入力identity | 8.7、11.2 | AC09 |
| P2-6 保存フィールド・個人情報 | 8.5、8.7、11.4 | AC10 |
| P2-7 例外隔離・fingerprint・I/O | 6、8.8、10、11.1 | AC11/12/13/14/17 |
| 実runでのcapture状態・terminal保存順 | 8.8、10、11.1 | AC18 |
| manifest自己参照によるartifact整合性 | 8.5、8.8、11.4 | AC19 |
| 無音区間の補間未評価 | 8.4、11.3 | AC20 |
| source/exe実行形態の識別不足 | 8.7、11.5 | AC21 |
| 解析完了後のtiming/model/text source未反映 | 8.7、8.8、11.2 | AC22 |
| P3-1 CSV未定義 | 8.5、11.4 | AC15 |
| P3-2 冪等性の比較対象 | 5、8.3、11.2 | AC16 |
