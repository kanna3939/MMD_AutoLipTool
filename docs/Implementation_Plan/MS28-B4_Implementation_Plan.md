# MS28-B4 Implementation Plan

## 1. 文書情報

- 対象Block: `MS28-B4`
- 名称: Silence Core / Cross-Vowel Handoff Contract Repair
- 作成日: 2026-09-20
- 対象branch: `feature/MS28-B1-implementation`
- 基準HEAD: `03f5e2c Implement MS28-B3 debug metadata finalization`
- MS28位置づけ: MS20〜MS27の全体マイルストーン系列とは切り離した、Ver.1実装後の独立修正実装トラック
- 文書状態: **Implemented / Additional Improvements Implemented; External Validation Pending**
- 依存Block: `MS28-B3` のデバッグtrace、Preview/Writer比較、無音観測、provenance

B4は、B3で発見した無音中の開口残存を、cross-vowel handoffと無音判定の契約に沿って修正する。B3のログ生成機構そのものを置き換えず、B3が記録した事実を使って製品側のhandoff適用条件を狭める。

境界専用admission、同一点zeroのrequired-zero伝播、B4 debug artifact v2、未所属境界の記録は、B4のv1履歴を保持したMS28-B4B子計画へ分離して実装・検証する。B4 v1の`contract_version`と既存artifactは変更しない。

## 2. 背景

B3の実runでは、RMS上の長い無音区間にWriterの正値と補間値が残るケースを確認した。

代表例では、次の状態が同時に記録された。

- 元timelineの「あ」はフレーム147〜151で終了
- 後続の「う」はフレーム180以降に存在
- effective shapeの「あ」がフレーム147〜187へ拡張
- フレーム148と185に「あ」の正値制御点が存在
- `cross_vowel_transition` handoffが有効
- 5.107〜6.097秒のRMS無音区間へ「あ」の補間値が残存

この結果は、単なる制御点の検出ではなく、代表ピーク間隔を基準にしたcross-vowel候補が、zero-run全体の長さと無音coreを十分に考慮せず、前母音の終端を延長している可能性を示す。

現在の`suspicious`は、正値制御点・正値補間の検出には有効だが、timing境界、許可された短いhandoff、長音処理、handoffによる契約違反を一つの調査候補へまとめている。B4では診断結果の分類と製品側のhandoff適用条件を分離する。

## 3. 目的

- RMS無音区間の厳密な内部範囲を定義し、境界重複と無音core内の開口を区別する。
- `clear`、`suspicious`、`explained`、`contract_violation`、`not_evaluable`の診断契約を固定する。
- 長いzero-runまたは無音coreをまたぐcross-vowel handoffを適用しない。
- handoffではなく、通常のbase event自身が無音core内に正値shapeを生成するケースを検出し、通常母音ではcore内開口を採用しない。
- 長音hold／continuation／terminal、manual adjustment、required-zeroを通常母音のcore競合と分離し、許可理由または拒否理由を固定する。
- 短いbridge可能なgapと、今回のような長い無音区間を区別する。
- 前母音のeffective shapeが、無音をまたいで後続母音側へ延長されないことを保証する。
- デバッグ検出結果を理由に解析やVMD保存を禁止せず、通常処理への副作用を維持しない。

## 4. In Scope

- B3の`silence_observations`における無音core／boundary fringeの分類。
- `suspicious`等のresult、reason code、evaluation statusの整理。
- 無音中の開口値をmorph、frame、shape、event、handoff、provenanceへ対応付ける記録。
- `_classify_bridgeable_zero_run_span`および関連するcross-vowel候補の全区間長検証。
- cross-vowel handoff適用前の無音core交差検査。
- base event admission時の無音core交差検査と、通常母音のcore内正値shape拒否。
- provenance artifactからdebug silence observationへのshape／event／point対応付け。
- 長いzero-runをまたぐ前母音の終端延長を抑止するfail-closed動作。
- TEXT＋音声、音声のみ、編集済み書き起こし再解析の決定的回帰。
- B3計画との契約・回帰条件の同期。

## 5. Out of Scope

- RMSの製品側閾値、Whisper、音声認識、音声ファイル変換の変更。
- 長音の基本生成規則、Preview描画方式、VMD形式、MMD用WAV出力の変更。
- 全母音shapeへの一律zero追加、固定フレーム数による無条件clamp。
- `suspicious`を解析失敗、Preview失敗、VMD保存禁止へ昇格すること。
- Debug modeのメニュー、保存先、manifest、個人情報保護契約の再設計。
- バージョン変更、build設定変更、正式版build、release、push、merge。

## 6. 前提条件

- B3のRMS無音候補定数を使用する。診断上のRMS閾値は`0.01`、最小継続時間は`0.10秒`、VMD FPSは30を維持する。
- `silence_core`は、coverageが有効な無音区間内に完全に含まれる半開frame cellで構成する。
- 無音区間と一部だけ交差するframe cellは`boundary_fringe`として別記録し、core内の契約違反と同じ強度で扱わない。
- `contract_violation`はデバッグ上の診断結果であり、通常の解析・Preview・VMD保存を停止させない。
- handoff候補の採否はeffective shape生成前に確定し、effective shape生成後に無音を理由として値を後付け削除しない。
- RMSの無音判定は`pipeline`側で一度だけ行い、`silence_core`のframe範囲、coverage状態、交差判定結果をbridge候補の契約フィールドまたは事前に確定したrejected理由として`effective_shape_plan`へ渡す。`effective_shape_plan`が音声を再読込して判定してはならない。
- 長音処理が関係する場合は、long source、continuation、terminal、resolved tailを明示的に記録する。

## 7. 対象ファイル

### 7.1 主変更候補

| ファイル | 責務 |
| --- | --- |
| `src/core/pipeline.py` | zero-run全体のframe span、RMS無音coreとの関係、bridge候補とbase event admissionの根拠を確定する |
| `src/core/effective_shape_plan.py` | handoffおよびbase eventの採否、前後eventの範囲、拒否理由、effective shape延長・core内開口のfail-closed |
| `src/gui_wx/main_frame.py` | silence core／boundary fringe、診断result、raw/normalized Writer point、shape/event/point provenanceのdebug専用結合 |
| `src/core/analysis_debug_trace.py` | B4の診断payload、`contract_version="ms28-b4-silence-v1"`、固定reason codeのsafe serialization。B3の`schema_version=1` envelopeを維持 |
| `src/core/analysis_debug_store.py` | B4で追加するartifactの保存・manifest登録。既存I/O契約を維持し、旧artifactを上書き・runtime readしない |
| `src/core/output_diagnostics.py` | `PeakValueObservation`の実行時契約フィールドを既存の観測canonicalization／fingerprintへ含め、debug artifact専用フィールドは含めない境界を固定 |

### 7.2 テスト候補

| ファイル | 確認内容 |
| --- | --- |
| `tests/test_ms28_b4_silence_handoff.py` | 長い無音をまたぐhandoff拒否、短いgapのhandoff維持、required-zero |
| `tests/test_ms28_b4_debug_classification.py` | result分類、core/fringe、reason code、provenance、not_evaluable |
| `tests/test_ms28_b4_base_event_silence_core.py` | base eventのcore交差、通常母音のcore内開口拒否、長音・manualの許可分類、`EventSilenceAdmission`の追跡項目・final required-zero |
| `tests/test_pipeline_peak_values.py` | 代表ピークだけで長いzero-runをhandoff候補にしないこと、短いgapとfloor候補の境界 |
| `tests/test_ms21_b2_effective_shape_plan.py` | `ObservationHandoff`のenabled/rejected、調整済みeventとの競合、長音除外 |
| `tests/test_ms28_b3_debug_trace.py` | B3の既存trace、保存、privacy、補間検出の回帰 |
| `tests/test_ms28_b4_contract_identity.py` | stage envelope／canonical payloadのJSON path、schema／contract配置、runtime契約フィールドのfingerprint包含、debug専用フィールドの除外、Debug ON/OFF identity不変 |
| `tests/test_ms20_b2_output_diagnostics.py` | 既存save-state fingerprintの正規化順序とB4追加フィールドの回帰 |
| `tests/test_preview_transform.py` | 短いbridgeのPreview維持、長い無音handoff拒否後の境界反映 |
| `tests/test_vmd_writer_intervals.py` | 既存VMD frame intervalとzero境界の回帰 |
| `tests/test_vmd_writer_zero_guard.py` | zero guard、重複、required-zeroの既存回帰 |

### 7.3 確認対象

- `src/vmd_writer/writer.py`: 既存のframe正規化、重複処理、開口epsilon
- `src/vmd_writer/effective_shape_adapter.py`: effective shapeからWriter投影への所属
- `src/core/preview_transform.py`: Preview投影との同一revision比較
- `docs/Implementation_Plan/MS28-B3_Implementation_Plan.md`: B3の診断・保存契約との整合
- `docs/MS20_and_Beyond_Index.md`: MS28の現在地、B4計画、次工程のrouting

`src/vmd_writer/effective_shape_adapter.py`の既存`build_morph_frames_from_effective_shape_plan()`戻り値は変更しない。Writer／Previewの公開tuple APIを維持し、debug専用provenanceの組立は`main_frame.py`側で行う。

## 8. 実装方針

### 8.1 無音区間の評価範囲

無音区間を次の3つへ分ける。frame `f` のcellは、FPS=30を固定して半開区間`[f / 30, (f + 1) / 30)`とする。RMS無音区間`[start_sec, end_sec)`に対し、cell全体が含まれるframeを`silence_core`、正の長さで交差するが全体は含まれないframeを`boundary_fringe`とする。境界の判定は秒の丸め後の代表点ではなく、このcell区間との包含・交差で行う。

1. `silence_core`: frame cell全体がRMS無音区間に含まれる範囲
2. `boundary_fringe`: 無音区間とframe cellが部分的に交差する範囲
3. `unobserved`: RMS coverageが不足し、無音と判定してはいけない範囲

正値が`silence_core`に存在する場合のみ、開口残存の本判定対象とする。`boundary_fringe`だけの正値は、`result=clear`、`evaluation_status=evaluable`、`reason_code=boundary_overlap_only`として記録し、単独では`suspicious`または`contract_violation`にしない。coverageまたはprovenanceが不足する場合は、この規則より`not_evaluable`を優先する。`boundary_overlap_only`はreason codeであり、8.2の`result`列挙値ではない。

### 8.2 診断result契約

| result | 判定条件 | 通常処理への影響 |
| --- | --- | --- |
| `clear` | silence core内に正値制御点・正値補間がない | なし |
| `suspicious` | silence core内に正値があるが、許可説明または既存契約違反へ分類できない | なし。調査候補として保存 |
| `explained` | 正値が明示されたlong/hold/manual/許可bridgeへ帰属でき、契約範囲内 | なし。原因説明として保存 |
| `contract_violation` | 無音coreをまたぐhandoff、required-zero欠落、禁止範囲へのeffective shape延長など | なし。製品側修正対象として保存 |
| `not_evaluable` | RMS coverage、投影、frame境界、provenanceのいずれかが不足 | 正常扱いしない。保存可能な不足理由を残す |

`evaluation_status`は`evaluable`／`not_evaluable`を保持し、resultとは別にする。writer全体に点が存在するだけで対象intervalをevaluableとは判定しない。

診断フィールド名はB4で次のように固定する。B4の新規`silence_observations.json`では、B3の構造化記録 envelopeの`schema_version=1`を維持するだけでなく、canonical payloadのrootにも`schema_version=1`を明示し、payloadへ`contract_version="ms28-b4-silence-v1"`を付ける。`silence_observations[].result`をB4の正本フィールドとし、値は8.2の5分類のいずれかに限定する。`candidate_classification`はRMS側が付けた入力区間の候補ラベルであり、診断結果とは別である。B3 artifactの既存payloadは上書き・再解釈せず、現行アプリにartifact readerは追加しない。旧artifactとの互換性は、旧ファイルを保持し、外部のread-only検査が旧フィールドを扱えることを意味する。B4の新規silence artifactでは`classification`、`silence_classification`を診断結果の別名として出力しない。

artifactのJSON配置を次で固定する。`stages/*_silence_observations.json`は既存record envelopeの`schema_version=1`と、`payload.schema_version=1`、`payload.contract_version="ms28-b4-silence-v1"`、`payload.observations[].result`を持つ。`silence_observations.json`および`projections/<revision>/silence_observations.json`は`analysis_debug_store.py`がpayloadだけを書き出すcanonical artifactなので、rootに同じ`schema_version=1`、`contract_version`、`observations[].result`を持つ。したがって、AC17はstage envelopeの有無だけでなく、canonical artifactのroot keysを検証する。B3の`observations`／`peak_observations.json`はこの配置規則の対象外であり、従来のpayloadを変更しない。

分類の優先順位は、`not_evaluable`（必要な観測またはprovenanceが不足）を最優先とし、次に`contract_violation`（handoff・required-zero・禁止範囲延長の違反）、`explained`（明示された許可理由があり契約内）、`suspicious`（正値はあるが帰属未解決）、`clear`の順とする。正値が`silence_core`にあり、handoff交差・required-zero欠落・禁止範囲延長のいずれかが実測された場合は必ず`contract_violation`とする。許可されたlong/hold/manual/short bridgeへ完全に帰属し、契約違反がない場合だけ`explained`とする。観測とprovenanceは十分だが許可された帰属も契約違反も確定できない場合だけ`suspicious`とする。正値がcoreにない場合は、fringe単独を`clear`＋`boundary_overlap_only`、正値なしを`clear`＋`clear_no_positive_opening`とする。許可理由が存在しても無音coreをまたぐ契約違反を免除せず、違反を優先して記録する。

同一silence observation intervalにhandoff拒否とbase event admission拒否が同時に存在する場合、rootの`result`／`reason_code`は上記優先順位で1つに決め、詳細は`handoff_rows`と`base_event_admissions`を別配列で保持する。reason codeの連結、自由文からの再判定、handoff修正済みをbase event修正済みとみなす省略は行わない。これによりevent 65相当のような複数原因を、単一の`suspicious`へ圧縮しない。

### 8.3 reason code

最低限、次の固定codeを使用する。

- `positive_writer_control_point_in_silence_core`
- `positive_writer_interpolation_in_silence_core`
- `positive_writer_control_point_and_interpolation_in_silence_core`
- `positive_base_event_in_silence_core`
- `clear_no_positive_opening`
- `boundary_overlap_only`
- `cross_vowel_handoff_crosses_silence_core`
- `cross_vowel_handoff_exceeds_full_span_limit`
- `base_event_overlaps_silence_core`
- `required_zero_missing`
- `explained_long_vowel_decay`
- `explained_manual_adjustment`
- `explained_allowed_short_bridge`
- `writer_projection_unavailable`
- `silence_coverage_insufficient`
- `provenance_unavailable`

既存の自由文、例外本文、入力本文、絶対パスはreason codeへ入れない。

B3で保存済みの固定reason codeは削除せず、B4の`result`／新reason codeへ決定的に対応付ける。既存artifactを読める期間を確保するため、必要な場合は`legacy_reason_codes`として残すが、自由文への逆戻りやコード名の推測変換は行わない。

旧コードの対応は次の規則で固定する。

| B3旧reason code | B4への対応 |
| --- | --- |
| `positive_writer_control_point_in_silence` | core内なら`positive_writer_control_point_in_silence_core`、fringeだけなら`boundary_overlap_only` |
| `positive_writer_interpolation_in_silence` | core内なら`positive_writer_interpolation_in_silence_core`、fringeだけなら`boundary_overlap_only` |
| `positive_writer_control_point_and_interpolation_in_silence` | core内なら`positive_writer_control_point_and_interpolation_in_silence_core`、fringeだけなら`boundary_overlap_only` |
| `no_positive_control_or_interpolation` | `clear_no_positive_opening` |
| `writer_projection_unavailable` | `writer_projection_unavailable`および`not_evaluable` |
| `OPEN_INTERVAL_IN_SILENCE`等の旧分類コード | 元の`legacy_reason_codes`を保持し、実測されたcontrol/interpolation・core/fringe・handoff情報から上記B4コードを決定する。文字列だけの一対一変換は禁止 |

`ZERO_PEAK_EVENT_GROUPED_WITHOUT_BRIDGE`のように原因が旧分類だけでは確定しないものは、`legacy_reason_codes`を保持し、handoffが短gapとして有効なら`explained_allowed_short_bridge`、全区間上限またはsilence coreにより拒否されたなら対応する`cross_vowel_handoff_*`、根拠不足なら`provenance_unavailable`へ分岐する。

### 8.4 開口の出所

正値の各区間について、次を記録する。

- morph名
- 開始／終了frameと秒
- 最大値、正値継続時間
- 制御点か補間か
- 左右のsource frame
- source shape ID
- source event index
- `base_range`と`effective_range`
- `origin_kind`
- handoff kind、previous／next event index、enabled／rejected理由
- long run、manual adjustment、required-zeroとの関係

これにより、単に「あが開いている」ではなく、「どのshape延長または補間が開口を作ったか」を再現できるようにする。

データの責任境界は次で固定する。

| 段階 | 保持する項目 | 判定責任 |
| --- | --- | --- |
| `pipeline.PeakValueObservation` | 既存のfull span／core／fringe／coverage／provenanceに加え、`base_event_silence_core_overlap`、`positive_core_frame_ranges`、`long_vowel_role`、`manual_adjustment_applied`、`base_event_rejection_reason_code` | RMS coverage、zero-run全体、base event自身のcore競合を一度だけ確定 |
| `effective_shape_plan.ObservationHandoff` | handoffのfull span／core overlap／coverage／provenance／rejectionを引き継ぐ`enabled`判定済み情報 | `enabled=True`だけをeffective shapeへ適用し、`False`は延長に使わない |
| `effective_shape_plan.EventSilenceAdmission`（追加契約） | `event_index`、`vowel`、`origin_shape_id`、`positive_point_kinds`、`source_event_indices`、`effective_frame_range`、`base_event_silence_core_overlap`、`positive_core_frame_ranges`、`long_vowel_role`、`manual_adjustment_applied`、`enabled`、`rejection_reason_code`、`required_zero_frame_ranges` | 通常母音のcore内正値を採用せず、long/hold/manualの許可理由を明示。`origin_shape_id`は同一projection revisionのprovenanceにおけるshape ordinal、`source_event_indices`はshapeの実所属event群、`positive_point_kinds`は該当eventのpositive control point種別を保持する |
| `main_frame._build_debug_silence_observations`およびdebug専用provenance builder | core/fringeのframe区間、morph、point kind、source frame、shape/event、handoff、base event admission、`result`、primary reason、`legacy_reason_codes`。raw/normalizedの追加・統合・削除も実データから記録 | debug artifactの診断分類。RMS再読込と製品処理の変更は行わない |

`silence_intervals`の入力には、少なくとも`coverage_status`、`silence_core_frame_ranges`、`boundary_fringe_frame_ranges`、`source_stage`を含める。デバッグビルダーへ渡す`writer point record`は、既存adapterの3要素tupleを読み取った後に、morph、frame、valueに加えてpoint kind、source shape/event、provenanceを追跡できる内部recordへ拡張する。既存adapterの公開3要素tuple API自体は変更しない。欠損時は推測せず`not_evaluable`とする。

B4で追加する契約フィールドの型と名前は次で固定する。`contract_version`は新規`silence_observations.json` payloadだけに付ける固定文字列`"ms28-b4-silence-v1"`、frame rangeは半開区間の`tuple[tuple[int, int], ...]`、overlapは`bool`、statusは固定enum、reasonは固定reason codeまたは`None`とする。`EventSilenceAdmission.vowel`は固定morph名、`base_event_silence_core_overlap`は`bool`、`positive_core_frame_ranges`は半開frame range、`long_vowel_role`は現行`effective_shape_plan`の`None`／`long_source`／`intermediate_continuation`／`terminal_continuation`を使用し、`manual_adjustment_applied`は`bool`、`base_event_rejection_reason_code`は固定reason codeまたは`None`とする。`EventSilenceAdmission`は`event_index`ごとに1行を持ち、shapeが最終採用されなかった場合の`origin_shape_id`は`None`、`effective_frame_range`は拒否前の候補範囲、`positive_point_kinds`は空tupleまたは候補shapeから解決した固定文字列tupleとする。`required_zero_frame_ranges`は、当該`vowel`について最終`NormalizationContract.required_zero_frames`へ展開する半開rangeであり、admission前に推測してはならない。`PeakValueObservation`と`ObservationHandoff`は既存handoff項目を同じ値で保持し、`EventSilenceAdmission`はbase eventの採否を明示する。handoffまたはadmissionを拒否する場合は`enabled=False`と拒否理由を常に併記する。

既存の`build_morph_frames_from_effective_shape_plan()`の公開戻り値とWriter／Preview投影APIは変更しない。`main_frame.py`は、同一projection revisionで既に取得したraw Writer frames、normalized Writer frames、EffectiveShapePlanのcontrol points、normalization contract、既存provenance rowsを使い、debug専用recordを構築する。exact raw pointはsource shape/eventへ結び付け、normalizationで追加・統合・削除されたpointは実際のbefore/after差分と`required_zero`／contract範囲から`origin_kind`を付ける。安全な対応を作れないpointは推測せず`provenance_unavailable`／`not_evaluable`とする。

無音情報の正本と受け渡しは、`pipeline._debug_rms_payload`が作るRMS coverage／無音区間を入口とし、同じ解析runの`PeakValueObservation`へframe span、core/fringe、coverage、provenanceを付加し、`effective_shape_plan.ObservationHandoff`へコピーしてhandoff採否を確定する。base event admissionは、調整済みeventとhandoffを反映したcandidate shapeを一時生成し、`EventSilenceAdmission`でregular eventの採否を確定した後、拒否eventを除外してfinal shapeを再構築する二段階とする。candidate shapeはdebug artifactへ出力せず、final shapeの`origin_shape_id`と同一projection revisionのprovenanceだけを正本とする。`main_frame._record_debug_projection`はそのrunの`rms_load` payloadと同一projection revisionのfinal EffectiveShapePlan／Writer実データをdebug専用builderへ渡す。`main_frame`はRMSを再計算せず、古い`start_sec`／`end_sec`だけのintervalを単独の正本として扱わない。受け渡し項目が欠けた場合は推測せず`not_evaluable`とし、handoffまたはadmissionを有効化しない。

B3の`observations` stageおよび`peak_observations.json`に残る`silence_classification`は、既存B3 artifactの互換フィールドとして扱い、B4のsilence resultとは別物とする。B4の正本はroot／projectionの`silence_observations.json`内の`observations[].result`であり、同じ行にRMS由来の`candidate_classification`を必要時だけ保存する。B4の新規silence artifactでは`classification`、`silence_classification`をresultの別名として追加出力しない。旧artifactは読み取り専用検査の対象とし、通常解析で8.2の分類器へ流入させない。

RMS artifactのsource fieldは移行しない。`rms_analysis.json`の`silence_intervals[].classification`はB3互換の入力区間ラベルとして保持し、B4のdebug builderがその値を`candidate_classification`へ明示的に写像する。`rms_analysis.json`の`classification`を`silence_observations[].result`へ直接コピーしてはならず、B4のresult分類器がcore/fringe、coverage、provenance、Writer実測値から別途決定する。この対応を、旧B3 field、B4 canonical field、resultとの非同一性を確認する回帰テストへ固定する。

### 8.4.1 実行時契約とdebug専用情報のidentity境界

`PeakValueObservation`のうち、`full_span_start_frame`、`full_span_end_frame`、`silence_core_frame_ranges`、`boundary_fringe_frame_ranges`、`silence_core_overlap`、`coverage_status`、`provenance_status`、`bridge_rejection_reason_code`、`base_event_silence_core_overlap`、`positive_core_frame_ranges`、`long_vowel_role`、`manual_adjustment_applied`、`base_event_rejection_reason_code`はhandoffまたはbase event admissionとeffective shapeの採否を決める実行時契約フィールドである。これらは既存の`output_diagnostics._observations_canonical()`で既存fieldの後に、指定順序で追加し、`BasePlanIdentity`／save-state fingerprintの観測canonicalizationに含める。

`span_start_index` → `span_end_index` → `full_span_start_frame` → `full_span_end_frame` → `silence_core_frame_ranges` → `boundary_fringe_frame_ranges` → `silence_core_overlap` → `coverage_status` → `provenance_status` → `bridge_rejection_reason_code`

続くbase event契約フィールドは、上記の既存handoffフィールドの後に次の順序で追加する。

`base_event_silence_core_overlap` → `positive_core_frame_ranges` → `long_vowel_role` → `manual_adjustment_applied` → `base_event_rejection_reason_code`

値が変わったまま同じidentityとして扱うことは禁止する。

`EventSilenceAdmission`の判定項目はruntimeの派生decision recordであり、debug専用説明情報ではない。`BasePlanIdentity`へ直接追加せず、入力となる`PeakValueObservation`のcanonical fieldと、同一projection revisionの`EffectiveShapePlan` canonical payloadから比較する。Debug ON/OFFでadmissionのenabled／reason／追跡項目が変わる場合はidentity不一致として扱い、debug artifactだけの`result`／自由文の変化とは区別する。

一方、`result`、`evaluation_status`、`reason_code`、`legacy_reason_codes`、`candidate_classification`、`origin_kind`、point kind、raw/normalized pointの説明provenance、`contract_version`はdebug artifact専用の説明情報であり、`BasePlanIdentity`／save-state fingerprintへ含めない。Debug ON/OFFでこれらの説明情報だけが変化しても、runtimeの`PeakValueObservation`／`ObservationHandoff`／`EventSilenceAdmission`、effective shape、Preview／Writer出力、VMD保存可否のidentityは一致しなければならない。実装前にこの2群を表として照合し、実装後は同一入力でruntime契約フィールドを含むcanonical payloadとdebug専用フィールドを除外したfingerprintを確認する。

### 8.5 cross-vowel handoff契約

cross-vowel handoffは、代表ピーク間隔ではなく、zero-run全体と前後eventの実frame範囲で判定する。判定対象の全区間は、少なくとも前のnon-zero eventの`end_frame`から後のnon-zero eventの`start_frame`までの半開区間`[previous.end_frame, next.start_frame)`を含み、途中のzero observation／residual区間を省略しない。代表ピーク同士が近くても、この全区間またはその一部が既存上限を超える場合は短いbridgeとはみなさない。

全区間長は`full_span_frames = next.start_frame - previous.end_frame`で固定する。通常の1観測zero-runは`_CROSS_VOWEL_MAX_CANDIDATE_SPAN_FRAMES`、2観測zero-runは`_CROSS_VOWEL_ZERO_RUN_MAX_CANDIDATE_SPAN_FRAMES`を上限とし、代表点間隔だけで上限を回避してはならない。既存のright-gap residual／floor residualは例外的な別上限ではなく、全区間長がそれぞれの既存`*_RESIDUAL_MAX_SPAN_FRAMES`以内で、かつ既存のoverlap・right-gap・initial-gap条件をすべて満たす場合だけ維持する。全区間長が適用上限を超えるresidual候補は`enabled=False`、対応する`cross_vowel_handoff_exceeds_full_span_limit`として記録し、前母音の延長へ使わない。

handoffを有効にできる条件は次のとおり。

1. 前後に有効なnon-zero eventがある。
2. zero-run全体のframe spanが既存の短gap上限以内である。
3. 既存の`_CROSS_VOWEL_ZERO_RUN_MAX_CANDIDATE_SPAN_FRAMES`および残差上限を、代表点ではなく全区間へ適用する。
4. `silence_core`との交差がない。boundary fringeだけの交差はcore違反とはせず、debug result側では`boundary_overlap_only`として扱う。
5. 長音対象、required-zero欠落、provenance欠損がない。
6. 前後eventの開始・終了zeroを維持できる。

条件を満たさない場合はhandoffを適用せず、前母音を元の終端で閉じ、後続母音を自身の開始frameから開始する。特に、数十frame規模のzero-runを`cross_vowel_transition`として許可しない。

### 8.6 fail-closedと互換性

- bridge候補の根拠が不足する場合は、値を延長せず`not_evaluable`またはhandoff rejectedとして記録する。
- B4の診断処理は、生成後の値を削除・clampして結果を隠さない。
- PreviewとWriterで同じeffective shape planを使う既存契約を維持する。
- `suspicious`、`explained`、`contract_violation`は保存可否や既存OutputDiagnosticsへ注入しない。

### 8.7 base event admission契約

handoffがすべて拒否されても、RMS無音core内に通常のbase eventが存在すれば、base event自身が正値shapeを生成する可能性が残る。したがって、handoff判定とは別に、effective shapeへbase eventを採用する前に`EventSilenceAdmission`を確定する。

`EventSilenceAdmission`は`EffectiveShapePlan.event_silence_admissions`へbase event順のtupleとして保持する。admission自身を`BasePlanIdentity`へ再埋め込みすると循環するため、identityの正本は`PeakValueObservation`の実行時契約フィールドとし、admissionはその入力から決定的に再生成できる派生契約として扱う。admissionの`origin_shape_id`、`positive_point_kinds`、`source_event_indices`、`effective_frame_range`、`required_zero_frame_ranges`はfinal projectionのdebug／diagnostic canonical payloadへ含めるが、debug専用の`result`や自由文はruntime identityへ含めない。

判定順序は次のとおりとする。

1. `PeakValueObservation`とEffectiveShapePlanの同一event index、shape ID、control point、provenanceを対応付ける。
2. eventのeffective rangeとsilence core／boundary fringeをframe cell単位で比較し、positive control pointとpositive interpolationのcore範囲を確定する。
3. `long_vowel_role=long_source|intermediate_continuation|terminal_continuation`、resolved tail、`manual_adjustment_applied`を確認する。`manual_adjustment_applied`は、canonical `AdjustmentLayerSnapshot.adjustments`に当該eventの非no-op `EventAdjustment`が存在する場合だけ`True`とし、shapeの見かけ上の延長から推測しない。required-zeroはadmissionの入力ではなく、拒否後のfinal `NormalizationContract.required_zero_frames`から検証する。根拠が欠ける場合は通常母音として許可しない。
4. 通常母音のpositive pointがsilence coreへ入る場合は`enabled=False`、`base_event_rejection_reason_code=base_event_overlaps_silence_core`として記録し、core内に正値を生成しない。後段の一律clampで隠してはならない。
5. eventがcoreの外側にも有効範囲を持つ場合は、候補shapeをdebug artifactへ出力せず、regular eventを除外してfinal shapeを再構築する。既存のzero／normalization契約でcore境界を明示できるときだけfringe側を保持する。拒否したadmissionの`required_zero_frame_ranges`は`(vowel, frame)`の組へ展開し、shape由来のzeroとunionしたものをfinal `NormalizationContract.required_zero_frames`としてWriter／Previewへ渡す。生成後の一律clampは行わない。必要なzeroがfinal contractに存在しない場合は`required_zero_missing`として`contract_violation`に分類し、admissionを有効化しない。
6. 長音hold／continuation／terminalまたはcanonical adjustment snapshotに明示されたmanual adjustmentが契約内でcore内開口を許可する場合だけ`enabled=True`、`result=explained`、固定reason codeを記録する。許可理由があってもrequired-zero欠落やhandoff拒否の違反を免除しない。

この判定は、`pipeline`がRMS／zero-run／base eventの事実を確定し、`effective_shape_plan`がcandidate shapeを用いてadmissionとfinal shapeの採否を確定する。`main_frame`は同じadmission結果と同一projection revisionのfinal provenanceをdebugへ記録するだけとし、RMSを再読込して別判定を行わない。

## 9. 詳細ステップ

1. B3ログの5.107〜6.097秒相当fixtureを、入力本文や実ファイルに依存しない決定的timeline/RMS fixtureへ変換する。
2. silence core、boundary fringe、unobservedのframe変換ヘルパーと契約を定義する。
3. `PeakValueObservation`へzero-run全体のframe span、`silence_core`交差、coverage、provenance、base eventのcore競合、positive core range、long-vowel roleを載せ、`ObservationHandoff`と`EventSilenceAdmission`へ明示的に渡す。`effective_shape_plan`は判定済み候補だけを消費し、音声の再読込は行わない。
4. cross-vowel handoffの採否を全区間基準へ変更し、長い無音跨ぎを拒否する。
5. effective shapeのbase/effective range、handoff、base event admission、provenanceをB4診断へ接続する。Writer adapterの既存tuple APIは変更せず、`main_frame.py`のdebug専用builderで同一revisionのraw/normalized実データ、EffectiveShapePlan、provenance rowsを結合する。
6. silence observationのresult/reason/evaluation statusを新契約へ分類し、通常母音のbase event core競合を`contract_violation`、許可されたlong/manualを`explained`へ分ける。
7. Preview／Writer比較、required-zero、長音decay、短gapbridgeの既存処理を回帰確認する。
8. B4専用テストを追加し、B3・B2・VMD writerの関連テストを実行する。
9. B3計画、MS28-B4計画、`MS20_and_Beyond_Index.md`の参照先・契約・回帰条件・現在地を、実装後の到達状態へ同期する。
10. 実ファイル、GUI、exe、MMD目視確認は実施した範囲だけ別記する。

## 10. 状態遷移 / データ契約

通常解析の失敗・Preview・VMD保存可否の状態遷移はB3以前から変更しない。B4で変更するのは、handoff候補、base event admission、effective shapeの内部契約、およびそれを記録するdebug分類だけである。

~~~text
RMS coverage
  ├─ valid silence core → opening evaluation
  ├─ boundary fringe only → result=clear, reason=boundary_overlap_only
  └─ insufficient/unobserved → not_evaluable

opening evaluation
  ├─ required measurement/provenance unavailable → not_evaluable
  ├─ no positive value → clear
  ├─ positive + handoff/base-event/required-zero contract failure → contract_violation
  ├─ positive + explicit allowed origin → explained
  └─ positive + origin unresolved → suspicious

base event admission
  ├─ regular event positive point in silence core → rejected, required-zero maintained
  ├─ long/hold/manual origin explicitly allowed → explained, enabled
  └─ exact source mapping unavailable → not_evaluable, no implicit enable

cross-vowel candidate
  ├─ full span short and no silence core → enabled
  └─ long span / silence core / missing proof → rejected, no extension
~~~

`contract_violation`は解析結果を失敗扱いにせず、debug artifactへ固定codeで記録する。handoff rejected時は既存のzero境界を維持し、後続処理が別の値を暗黙に生成しない。

candidate契約では、`full_span_start_frame`、`full_span_end_frame`、`silence_core_overlap`、`coverage_status`、`provenance_status`、`rejection_reason_code`を明示する。base event契約では、`base_event_silence_core_overlap`、`positive_core_frame_ranges`、`long_vowel_role`、`manual_adjustment_applied`、`base_event_rejection_reason_code`を明示する。`effective_shape_plan`はこの判定済み情報を消費し、`enabled=False`のhandoffまたはadmissionを範囲延長・core内開口へ使わない。

## 11. テスト方針

### 11.1 handoff回帰

- 前event終了151、長いzero-run、後event開始180相当のfixtureで、前母音のeffective endが187へ延長されない。
- 1〜2frame相当の短い異母音gapではhandoffが従来どおり成立する。
- full spanが既存短gap上限を超える場合、代表ピークが近くてもhandoffを拒否する。
- silence coreを1cellでも跨ぐhandoffは拒否または明示的なcontract violationとして記録する。
- long vowel source/continuation/terminalが存在するケースでは、B1/B2の既存hold/decay契約を壊さない。

### 11.2 suspicious分類

- silence core内の正値制御点は、handoff交差・required-zero欠落・禁止範囲延長が実測された場合は`contract_violation`、それ以外で許可帰属が未解決の場合は`suspicious`へ決定的に分類する。
- handoffが拒否された後も、base event自身のpositive control pointがsilence core内に残るfixtureを別に検証し、通常母音は`base_event_overlaps_silence_core`として拒否する。
- event 65相当のbase event（前eventの終端後に新規開始する正値event）が、前母音のhandoff延長とは別に検出・分類される。
- `EventSilenceAdmission`の拒否後はcore内に正値を出力せず、core外のfringeを保持できる場合だけ保持する。安全な部分形状を作れない場合はrequired-zeroを維持する。
- `long_vowel_role=long_source|intermediate_continuation|terminal_continuation`、`manual_adjustment_applied`、required-zeroの明示的な許可／拒否理由が、通常母音のbase event競合へ誤適用されない。
- silence core内の補間だけを`positive_writer_interpolation_in_silence_core`として記録する。
- boundary fringeだけの正値を本体の`suspicious`と混同しない。
- writer点が対象interval外にしかない場合は、全体点の存在だけで`evaluable`にしない。
- source shape/event/provenanceを解決できない場合は`not_evaluable`へ落とす。
- `provenance.json`で解決可能なpointが、silence observationでも同じshape/event/pointへ対応付けられ、全件が機械的に`provenance_unavailable`へ落ちない。
- clear、suspicious、explained、contract_violation、not_evaluableのreason codeが固定値で保存される。fringe単独は`result=clear`＋`reason_code=boundary_overlap_only`とする。
- B3既存reason codeがB4のresult／reason codeへ決定的に対応付けられ、既存artifactの読解を壊さない。
- 代表ピークだけで長いzero-runを許可していた既存`test_pipeline_peak_values.py`の期待値が修正され、短いbridgeの既存Preview／Writer回帰は維持される。
- `test_observation_marks_cross_vowel_long_zero_interval_as_transition_candidate_via_representative_span`と`test_observation_marks_cross_vowel_long_two_zero_span_as_floor_candidate_via_representative_span`は、長い全区間をhandoff許可しない期待値へ更新される。
- `test_observation_marks_cross_vowel_single_zero_span_with_moderate_right_gap_as_transition_candidate`、`test_observation_marks_cross_vowel_two_event_right_gap_residual_span_as_transition_candidate`、`test_observation_marks_cross_vowel_wide_two_event_right_gap_span_as_floor_candidate`は、full spanが適用上限を超える場合はrejected期待値へ更新し、上限内で既存条件を満たすfixtureは短いhandoffとして維持する。
- `test_cross_vowel_transition_candidate_extends_previous_end_and_advances_next_start`等の短いbridge回帰は維持し、長いzero spanを拡張するケースは拒否側の期待値へ更新される。

### 11.3 入力経路・副作用

- TEXT＋音声、音声のみ、編集済み書き起こし再解析で同じ分類契約を通す。
- B3のPreview／Writer比較は同一revisionで許容差内のまま維持する。
- Debug ON/OFFで、ID、時刻、debug専用payloadを除く解析timeline、EffectiveShapePlan、Preview、Writer、VMD保存可否の正規化比較が一致する。debug判定は通常処理の採否・数値・保存可否へ影響させない。
- debug判定の例外、I/O失敗、provenance不足が通常解析へ再throwされない。
- 実行ログのJSON/CSV/TXTに本文、絶対パス、生例外が漏れない。
- B3の`schema_version=1` envelope、B4の`contract_version`、旧B3 artifactの保持、RMS source fieldからB4 canonical fieldへの写像が同じfixtureで確認され、旧`classification`／`silence_classification`がB4のresultへ混入しない。

### 11.4 検証境界

自動テストでは決定的fixture、全体pytest、既存VMD writer回帰を確認する。実Whisper、native wx操作、exe、実MMDでの見た目は、実施したものだけ別の証拠として扱い、自動テストの代替にはしない。

## 12. 受け入れ条件

- [ ] B4-AC01: FPS=30のcell`[f / 30, (f + 1) / 30)`を基準に、silence core、boundary fringe、unobservedが半開frame cell単位で区別される。
- [ ] B4-AC02: resultが`clear`、`suspicious`、`explained`、`contract_violation`、`not_evaluable`に固定分類され、fringe単独は`clear`＋`boundary_overlap_only`、core内の契約違反は`suspicious`へ降格されない。
- [ ] B4-AC03: silence core内の正値について、morph、frame、値、補間、shape/event/provenanceが追跡できる。
- [ ] B4-AC04: `evaluation_status`が対象intervalの評価可能性を表し、Writer全体の点の有無だけで判定しない。
- [ ] B4-AC05: 長いzero-runまたはsilence coreをまたぐcross-vowel handoffが拒否される。
- [ ] B4-AC06: 5.107〜6.097秒相当のfixtureで前母音が無音をまたいでeffective shape延長されず、required-zeroが維持される。
- [ ] B4-AC07: 短いbridge可能gap、長音decay、manual adjustmentは互いに誤分類されない。
- [ ] B4-AC08: Preview／Writerの同一revision比較、通常解析、VMD保存可否にdebug判定が影響しない。
- [ ] B4-AC09: TEXT＋音声、音声のみ、編集済み再解析で同じ診断契約が成立する。
- [ ] B4-AC10: B3のprivacy、manifest、I/O、例外隔離契約を維持する。
- [ ] B4-AC11: 決定的自動テストと、実施した実ファイル／GUI／exe確認が別々に記録される。
- [ ] B4-AC12: `PeakValueObservation`、`ObservationHandoff`、debug observation record間でfull span、core/fringe、coverage、provenance、rejection reasonが欠落なく伝播し、`silence_observations.json`の`result`が新規artifactの正本フィールドになる。B3の`observations`／`peak_observations.json`に残る`silence_classification`は互換フィールドとしてresultと混同されない。
- [ ] B4-AC13: 代表ピーク基準で長いzero-runを許可していた既存回帰が反転され、通常の短いhandoffと、全区間上限内で既存residual条件を満たすhandoffだけが維持される。上限超過のresidual／floor候補、Preview、Writer、long-vowel除外の期待値が意図どおり固定される。
- [ ] B4-AC14: `build_morph_frames_from_effective_shape_plan()`の既存戻り値・Preview／Writer APIを変更せず、debug専用provenance builderがraw/normalizedの実差分を記録する。
- [ ] B4-AC15: RMS coverageから`PeakValueObservation`、`ObservationHandoff`、`main_frame`のdebug builder、`silence_observations.json`まで同じ解析run／projection revisionの情報が伝播し、main_frameがRMSを再読込せず、旧intervalのstart/endだけで判定しない。
- [ ] B4-AC16: Debug ON/OFFの正規化比較で、ID・時刻・debug専用payloadを除く解析結果、投影値、VMD保存可否が一致する。
- [ ] B4-AC17: B4の新規`silence_observations.json`が`schema_version=1`、`contract_version="ms28-b4-silence-v1"`を持ち、B3 artifactを上書きせず、現行アプリのruntime readを追加しない。旧artifactはread-only検査対象として保持される。
- [ ] B4-AC18: `rms_analysis.json.silence_intervals[].classification`は入力区間のsource labelとして保持され、B4 debug rowでは`candidate_classification`へ写像される。`silence_observations[].result`は5分類器の結果だけで決まり、旧`classification`／`silence_classification`を直接コピーしない。
- [ ] B4-AC19: `stages/*_silence_observations.json`のrecord envelopeとpayload、root canonical、projection canonicalの各JSON pathが固定され、canonical artifactのrootに`schema_version=1`、`contract_version="ms28-b4-silence-v1"`、`observations[].result`が存在する。B3の既存artifactには追加・上書きがない。
- [ ] B4-AC20: `PeakValueObservation`の実行時契約フィールド（既存handoff項目に加え、`base_event_silence_core_overlap`、`positive_core_frame_ranges`、`long_vowel_role`、`manual_adjustment_applied`、`base_event_rejection_reason_code`）が、`span_start_index`→`span_end_index`を含む指定順序で`output_diagnostics._observations_canonical()`とsave-state fingerprintへ含まれ、debug専用の`result`／`evaluation_status`／`reason_code`／`legacy_reason_codes`／`candidate_classification`／`origin_kind`／point-level provenance／`contract_version`は含まれない。`EventSilenceAdmission`は同じruntime契約から決定的に再生成され、final projectionのcanonical payloadへ必要な追跡項目を出す。Debug ON/OFFでruntime契約、effective shape、Preview／Writer、VMD保存可否、identityが一致する。
- [ ] B4-AC21: `EventSilenceAdmission`がbase eventごとに`EffectiveShapePlan.event_silence_admissions`へ生成され、`event_index`、`vowel`、`origin_shape_id`、`positive_point_kinds`、`source_event_indices`、`effective_frame_range`、`required_zero_frame_ranges`を同一projection revisionで追跡できる。最終shape不採用時は`origin_shape_id=None`と候補範囲を記録し、required-zeroはfinal `NormalizationContract.required_zero_frames`へ展開する。対応不能なpointは推測せず`not_evaluable`とする。
- [ ] B4-AC22: 通常母音のbase eventがsilence core内にpositive control pointまたはpositive interpolationを持つ場合、candidate shapeをfinal outputへ流さず、`enabled=False`、`base_event_overlaps_silence_core`、`result=contract_violation`となり、core内の正値をPreview／Writerへ出力しない。
- [ ] B4-AC23: base eventがcoreの外側にも有効範囲を持つ場合、admission拒否後にregular eventを除外してfinal shapeを再構築し、既存zero／normalization契約で安全に分割できる場合だけboundary fringe側を保持する。`required_zero_frame_ranges`が`(vowel, frame)`へ展開され、final `NormalizationContract.required_zero_frames`へunionされることを確認する。必要なzeroがなければ`required_zero_missing`として記録し、後段一律clampで違反を隠さない。
- [ ] B4-AC24: `long_source`／`intermediate_continuation`／`terminal_continuation`、canonical `AdjustmentLayerSnapshot`の非no-op event adjustmentによる`manual_adjustment_applied`、final `NormalizationContract.required_zero_frames`によるrequired-zeroの許可・拒否理由が通常母音のbase event競合と分離され、許可されたcore内開口だけが`explained`になる。
- [ ] B4-AC25: 最新実ファイル相当の`event 65` fixtureで、handoff拒否とbase event core競合が別々に観測され、handoff修正済みをbase event修正済みと誤認しない。
- [ ] B4-AC26: `provenance.json`で解決可能なWriter pointが`silence_observations.json`へ伝播され、coverageが完全なrunで全行が機械的に`provenance_unavailable`へ落ちない。coverage／provenance不足のfixtureでは従来どおり`not_evaluable`となる。

### 12.1 実装・自動検証記録（2026-09-20）

- 実装済み（B4 baselineおよび追加改善）: `src/core/pipeline.py`、`src/core/effective_shape_plan.py`、`src/core/output_diagnostics.py`、`src/gui_wx/main_frame.py`。長いzero-runの全区間判定、silence core／boundary fringe、handoff拒否理由・契約フィールドの伝播、通常base eventのadmission拒否、`EventSilenceAdmission`、required-zero伝播、long/manualの説明分類、同一projection revisionのprovenance照合、B4 debug payloadのschema／contract識別、runtime契約フィールドのcanonical identity包含を反映した。
- 追加・更新テスト: `tests/test_ms28_b4_base_event_silence_core.py`、`tests/test_ms28_b4_contract_identity.py`、`tests/test_pipeline_peak_values.py`、`tests/test_ms28_b3_debug_trace.py`。B4追加改善を含む関連回帰は70件、B4 baseline／debug／pipeline関連の既存回帰は41件、いずれも終了コード`0`。
- 全pytest: `1124 passed, 4 skipped`、終了コード`0`。最終全pytestでは警告は記録されなかった。
- `.venv`内に`ruff`モジュールが存在せず、対象ファイルへのruffチェックは実行不能だった。pytestおよび`git diff --check`は実行済みである。
- 実Whisper再解析、native GUI、EXE、実MMD、正式版build、手動Debug ON/OFF比較は未実施であり、AC01〜AC26のうち自動テストで直接確認できない項目は未検証として残す。バージョン、依存関係、INI／JSON runtime data、spec／build設定は変更していない。

### 12.2 最新ユーザーDebug runの改善課題（2026-09-20）

- 最新run `20260920_154954_973_6624783fc4da455691face1a1e7158a0` はTEXT＋音声、capture completed、Preview ready、Writer completed、projection comparison completedだった。これは追加改善実装前の履歴runである。
- `observation_handoffs`は43件中42件が無効で、cross-vowelの拒否理由は全区間長超過29件、silence core交差13件だった。有効な1件は同母音spanであり、B4のhandoff延長抑止はこのrunで確認できる。
- 9.827〜10.217秒のsilence intervalではframe 304がcore内positive、306がboundary fringeにあり、shapeはbase event 65の`あ`（303〜309）由来だった。前eventの終端からのhandoff延長ではないため、追加のbase event admission契約が必要である。
- `silence_observations.json`は21行すべて`not_evaluable / provenance_unavailable`だった。一方、同一runの`provenance.json`にはframe 304／306とsource event 65の対応があるため、B4改善ではこの伝播欠落をAC21／AC26の対象として修正する。
- 上記runで発見されたbase event admissionとprovenance伝播は実装済みで、決定的fixtureによる自動回帰を追加した。実Whisperでの同一projection revision、event 65相当の実run、GUI／EXEでのDebug ON/OFF比較は未実施である。

### 12.3 受入条件の状態管理

AC01〜AC26のチェックボックスは、追加改善を含むMS28-B4全体の最終受入を示す。§12.1の「実装済み」「自動回帰」は、source／決定的fixtureで確認できる範囲を示す証拠であり、実Whisper／GUI／EXE／MMD確認の完了を意味しない。

| 範囲 | 現在の状態 | 最終受入に必要な条件 |
| --- | --- | --- |
| AC01〜AC20 | B4 baselineの実装・自動回帰で確認可能な範囲は§12.1に記録済み。実ファイル／GUI／EXE／Debug ON/OFFなど外部確認を含む項目は未検証 | 自動回帰の終了コード、実行者、対象run、手動／EXE／MMDの別証拠を項目ごとに記録する |
| AC21〜AC26 | source／test実装と自動回帰を完了。通常母音のadmission拒否、long/manualの説明分類、required-zero、完全／不足provenance、handoffとadmissionの別配列を確認済み | 実runで同一projection revisionの追跡、event 65相当ログ、Debug ON/OFF identity、実Whisper／GUI／EXE／MMDの確認を追加する |

この表と§12.1／§12.2の状態が矛盾する場合は、未検証を完了へ格上げせず、ACチェックボックスを未完了のまま維持する。Indexには「B4 source実装・自動回帰完了」「外部確認未検証」を分けて記録する。

## 13. リスクと対策

| リスク | 対策 |
| --- | --- |
| 正常な短いhandoffまで消える | full span上限、短gap fixture、既存VMD writer回帰で検証 |
| 長音decayを不具合扱いする | long source/continuation/terminalを別identityで記録 |
| 無音境界の1frameだけを過剰検出する | core/fringeを分離し、fringe単独はboundary_overlap_only |
| shape延長を後段clampで隠す | handoff候補段階で拒否し、base/effective rangeを記録 |
| handoff修正済みとbase event修正済みを混同する | handoffと`EventSilenceAdmission`を別fixture・別reasonで検証 |
| 通常母音のcore開口を消す際に長音holdまで壊す | `long_vowel_role`、resolved tail、manual、required-zeroの許可契約を先に確定 |
| 診断結果が保存禁止へ波及する | contract_violationもdebug-onlyとし、既存save policyへ渡さない |
| provenance不足を誤って正常扱いする／全行を機械的に未評価にする | exact shape/event/point mappingを同一revisionから渡し、対応不能な行だけ`not_evaluable`へ分類 |
| B3の既存traceとschemaが競合する | B3のsafe payload、manifest、artifact ownershipを維持 |
| テストfixtureが実ファイルに依存する | timeline/RMS/shapeの決定的fixtureを使用し、実ファイル確認と分離 |

## 14. 実装時の注意

- 本計画の追加改善は修正実装計画であり、今回の計画更新ではソースを変更しない。既存B4実装の到達状態は§12.1、最新ユーザーDebug runの結果は§12.2を正本とする。
- `suspicious`の名称を理由なく削除せず、検出候補としての互換性を維持する。
- `contract_violation`は既存の製品エラーやOutputDiagnosticsへ自動変換しない。
- B1/B2の長音境界契約を変更する場合は、B4のcross-vowel handoff修正と混在させず、変更理由と回帰を別記する。
- `MS20_and_Beyond_Index.md`はMS28の現行routing正本であり、旧`MS17_and_Beyond_Index.md`へMS28の現在地を追記しない。
- バージョン、MS27完了状態、INI、presets、profiles、build設定を変更しない。
- 実装後は、変更ファイル、対象テスト、終了コード、実GUI/exe未検証範囲、残課題を日本語で報告する。

### 14.1 P2/P3再発防止ゲート

- 実装前・実装後の各レビューで、`result`、`classification`、`candidate_classification`、`silence_classification`、`boundary_overlap_only`、`base_event_overlaps_silence_core`、`schema_version`、`contract_version`の全出現箇所を検索し、8.2／8.4／8.7の責任表と一致することを確認する。
- `boundary_overlap_only`をresult列挙へ戻さない。`silence_observations`へ旧fieldの別名を追加しない。代表ピークだけでfull span上限を回避しない。RMSの`classification`をresultへ直接代入しない。
- stage envelope、canonical payload、projection payloadのJSON pathを個別に確認し、「artifactにschemaがある」という曖昧な表現だけで受入れない。`schema_version`と`contract_version`のroot／payload位置をAC19の期待値と突合する。
- 実行時契約フィールドとdebug専用フィールドを別表で照合し、`output_diagnostics._observations_canonical()`、BasePlanIdentity、save-state fingerprintの包含／除外をAC20〜AC26と突合する。新フィールドを追加したのにcanonicalizationを更新しない状態、またはdebug情報だけでidentityが変わる状態をP2として扱う。
- `EventSilenceAdmission`は、`EffectiveShapePlan.event_silence_admissions`への保存、`event_index`ごとの一意性、`vowel`／`origin_shape_id`／`positive_point_kinds`／`source_event_indices`／`effective_frame_range`／`required_zero_frame_ranges`の同一revision対応を、契約表・実装・debug artifact・テストで突合する。AC21に記載した追跡項目を表から省略した状態をP2として扱う。
- `manual_adjustment_applied`のproducerはcanonical `AdjustmentLayerSnapshot.adjustments`の非no-op entry、required-zeroのproducerはfinal `NormalizationContract.required_zero_frames`と固定し、candidate shapeからの推測や後段clampを許可しない。producer、評価時点、欠損時の`not_evaluable`／`required_zero_missing`が1つでも未記載ならP2として扱う。
- B4 baselineの実装済み・自動検証済み、追加改善の未実装、実Whisper／GUI／EXE／MMDの未検証をIndex・計画§12・ACチェックボックスで同じ語彙に揃える。状態を一つの「B4完了」へ圧縮しない。
- AC01〜AC26のうち未検証項目が残る状態で、実Whisper／GUI／EXE／実MMDまで検証済みとは記録しない。Indexの状態更新は、既存B4実装済み範囲、追加改善の未実装範囲、自動テスト終了コード、未検証境界を分けて記録する。
- B3既存テストとB4追加テストの両方で、旧artifact保持、source/canonical field分離、schema／contract識別、ON/OFF不変性を確認し、片方だけの成功を受入根拠にしない。
