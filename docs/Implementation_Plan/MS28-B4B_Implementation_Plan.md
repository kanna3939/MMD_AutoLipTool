# MS28-B4B Implementation Plan

## 1. 文書情報

- 対象Block: `MS28-B4B`
- 位置づけ: MS28内のB4修正拡張。B3Cの診断機構とは分離し、検出済みのゼロ幅境界イベントを製品処理へ適切に反映する。
- 文書状態: **B4B correction and diagnostic-output correction implemented / external validation pending**
- 対象branch: `feature/MS28-B1-implementation`
- 前提文書: `MS28-B4_Implementation_Plan.md`、`MS28-B3C_Implementation_Plan.md`
- 実装状態: B3C／B4B関連のソース変更が作業ツリーに存在する。今回の微修正では既存変更を上書きせず、B3CおよびB4Bのruntime契約を維持する。
- 今回の更新: 境界専用debug rowの所属判定、artifact v1/v2移行、runtime identity境界、境界関係の検証・優先順位、固定failure codeの登録範囲を明文化した。さらに、B4B補正後の最新6 runで確認したログ上の残課題を、製品処理の修正とdebug artifactの微修正に分離した。
- 再チェック対応: `PeakValueObservation`の生成元、B4 v1履歴とB4B v2の分離、未所属境界の保存先、debug reason／allowlist、stage・canonical・projection artifact間の同一性を固定した。
- 実装結果（B4B補正）: `EventSilenceAdmission`のboundary-only契約、required-zero伝播、境界関係の固定分類、未所属境界のroot記録、B4B v2 artifact、runtime canonical fieldを実装した。上流`event.peak_value`が正値でも、最終候補shapeが同一frameの`end_zero`だけならboundary-onlyとして扱う補正も実装済みである。B4 v1の履歴テストとpayloadは変更していない。
- 実ログで判明し、今回解消した微修正課題: 最新6 runでは全件が`effective_shape`、Preview、Writer、最終acceptanceまで到達したが、保存済み`silence_observations` artifactには`boundary_admission_checks`が含まれず、`events.csv`のpeak値とadmission decisionを同じ行で照合できなかった。また、`unassigned_boundary_admissions`はprojection反復で同じ境界が複数回記録されるため、固定識別キーが必要だった。`projection_input`の`not_attempted`は事前スナップショットであり最終失敗ではないため、診断スナップショットの対象時点を明示した。今回の実装でこれらのdebug出力を補正した。
- 自動検証結果（今回の実装後）: B4B／B3C対象`21 passed`、関連回帰`187 passed`、全pytest`1158 passed, 4 skipped`はいずれも終了コード`0`。正値`event.peak_value` fixture、artifact伝播、snapshot scopeも回帰対象に含まれる。ruffは`.venv`内に実行ファイルがなく未実施。EXE、実MMD、手動Debug ON/OFF比較は未実施であり、source Debug ONの最新6 runはユーザー実行ログとして別に扱う。

### 1.1 B4B補正前の履歴run

以下は、B4B補正前に発生した失敗の履歴であり、現在の実装状態を示すものではない。

| 入力 | mode | 結果 | 主要事実 |
|---|---|---|---|
| 00 | `text_audio` | failed | event 79 / frame 380 / `admission_range_invalid` |
| 00 | `voice_only` | failed | event 77 / frame 380 / `admission_range_invalid` |
| 01 | `text_audio` | success | `effective_shape=completed`, `preview_projection=ready` |
| 01 | `voice_only` | success | `effective_shape=completed`, `preview_projection=ready` |
| 02 | `text_audio` | failed | event 36 / frame 151 / `admission_range_invalid` |
| 02 | `voice_only` | failed | event 36 / frame 151 / `admission_range_invalid` |

失敗runでは、音声分析・RMS処理・観測処理の後、`silence_admission`で`effective_frame_range`が`[frame, frame]`へ縮退し、`effective_shape`以降が停止していた。対象候補は正の制御点を持たず、`end_zero`だけを持つ境界形状であった。この状態はB4B補正のfixtureと最新のsource runで再検証済みである。

### 1.2 B4B補正後の最新6 run

2026-09-21 JSTにユーザーが実行した`debug/`配下の直近6 runを、実装済みB4Bの境界条件と照合した。いずれもsource実行であり、EXEの証拠ではない。

| run | 入力 | 結果 | B4B関連の記録 |
|---|---|---|---|
| `20260921_125323_990` | `text_audio` | success | 27.808秒。event 79/89/145の境界がroot未所属として記録されたが、最終acceptanceまで完了 |
| `20260921_125355_130` | `voice_only` | success | 27.808秒。event 77/141の境界がroot未所属として記録されたが、最終acceptanceまで完了 |
| `20260921_125419_773` | `text_audio` | success | 31.355秒。未所属境界なし。最終acceptanceまで完了 |
| `20260921_125504_938` | `voice_only` | success | 31.355秒。未所属境界なし。最終acceptanceまで完了 |
| `20260921_125532_622` | `text_audio` | success | 12.333秒。projection 1/3/5でevent 36/frame 151が未所属、他projectionでは所属なし。全projection完了 |
| `20260921_125618_120` | `voice_only` | success | 12.333秒。projection 1/3/5でevent 36/frame 151が未所属、他projectionでは所属なし。全projection完了 |

6 runすべてで`capture_status=completed`、`effective_shape=completed`、`preview_projection=ready`、`writer_projection=completed`、最終`analysis_acceptance=completed`を確認した。B4B v2 artifactも全件で生成され、旧来の`admission_boundary_invalid`による処理停止は再現していない。

実装前のログでは、保存済み`silence_observations`に`boundary_admission_checks`が出力されていなかった。今回の実装で、`events.csv`との後付け結合なしに、成功・失敗の境界判定をartifact rowから追跡できる形へ補正した。`unassigned_boundary_admissions`には`admission_key`と`assignment_status`を付与し、projection反復による観測と製品イベントを区別できるようにした。cross-vowelの固定reasonは最新6 runで`not_evaluable`へfallbackしておらず、今回も処理ロジックを変更していない。

## 2. 背景

B3Cにより、今回の失敗は次の状態まで確認できるようになった。

- RMS後の低ピーク・疑わしいイベントが1フレーム幅へ縮退する。
- `EventSilenceAdmission`は半開区間として`end > start`を要求するため、ゼロ幅値を通常区間として受け付けない。
- 00ではframe 380、02ではframe 151で同じ構造が発生する。
- 候補形状は開口を維持する正値点ではなく、終了時の`end_zero`だけを持つ。
- 01では同じ入力経路の組合せでも正常にPreviewまで到達する。

したがって、今回必要なのはRMS閾値やWhisperの再設計ではなく、ゼロ幅の境界記録を有効区間と混同しない契約変更である。

## 3. 目的

1. ゼロ幅イベントを通常の有効区間と境界キーフレームへ明確に分離する。
2. `end_zero`だけを持つ境界イベントを、解析失敗にせずクローズ境界として保持する。
3. 長音終端と後続同母音開始が同一フレームの場合、同一点のクローズ用キーフレームを維持する。
4. 正値点を含む不正なゼロ幅イベントや、終了点の根拠が無いイベントはfail-closedで拒否する。
5. PreviewとWriterが同一の修正済み`EffectiveShapePlan`とrequired-zero契約を使用する状態を維持する。
6. 上流`event.peak_value`が正値でも、最終候補shapeが`end_zero`だけで正値出力を持たない実ケースをboundary-onlyとして安全に受理する。
7. 実ログで発生したboundary拒否理由とcross-vowel診断reasonの欠落・fallbackを、固定enumとsafe serializerの回帰で防ぐ。

## 4. In Scope

- `EventSilenceAdmission`の境界イベント契約追加。
- ゼロ幅候補の判定、境界専用admissionへの変換。
- 上流`event.peak_value`と最終候補shapeの正値証拠を分離したboundary-only受理条件への補正。
- `NormalizationContract.required_zero_frames`への境界ゼロ点の伝播。
- 同一フレームの同母音handoffで、明示的なゼロキーフレームを保持する処理。
- 00/02相当の実ログを固定した決定的fixtureと回帰テスト。
- B4 debug artifactへの境界処理結果の記録。
- B3/B3Cの既存診断、legacy failure、Debug ON/OFF identityとの整合確認。
- 実ログ相当の正値`event.peak_value`、`end_zero`のみのshape provenance、cross-vowel固定reasonを含む回帰fixture。
- `admission_boundary_invalid`のfailure context domain／fieldと、cross-vowel handoff reasonのsafe allowlist補正。
- 成功時の`boundary_admission_checks`を、resolver診断だけでなくB4Bの`silence_observations` artifactへ安全に複製すること。
- `unassigned_boundary_admissions`の重複観測を判別できる固定`admission_key`と、interval所属状態を示す固定値を追加すること。
- `projection_input`などの事前スナップショットと、最終stage結果を混同しないための診断スナップショット範囲を記録すること。
- 上記のdebug出力補正がruntime identity、Preview／Writer入力、VMD保存可否を変更しないことの回帰確認。
- 関連するB4契約文書・受入条件の更新。

## 5. Out of Scope

- Whisper、音声分析、RMS閾値、RMS窓計算そのものの再設計。
- `suspicious`分類の廃止または名称変更。
- 長音hold/decayの基本アルゴリズムの全面変更。
- Preview／Writer APIの公開戻り値変更。
- GUIのデバッグモード、ログ保存先、manifest全体の再設計。
- VMD形式、FPS、モーフ名、設定ファイル形式の変更。
- exeビルド、実MMD目視、リリース作業。
- `unassigned_boundary_admissions`を理由としたboundary-only処理の再拒否、または未所属境界の別intervalへの自動割当。
- B4B補正で確認済みの`event.peak_value`と最終候補shapeの判定ロジックの再変更。

## 6. 前提条件

- frame rangeは引き続き半開区間として扱い、通常区間では`end > start`を維持する。
- ゼロ幅を1フレーム区間へ人工的に拡張して、音声タイミングを変えない。
- 境界キーフレームは区間ではなく、`boundary_frame`と`boundary_point_kind`で表現する。
- `end_zero`の根拠となる候補形状・control pointが確認できる場合だけ境界イベントを許可する。
- 正値control point、正値補間、reversed range、終了点根拠の欠落がある場合は通常の契約違反として拒否する。
- Debug artifactはruntime処理の入力ではなく、同一runの決定結果を記録する。

## 7. 対象ファイル

### 7.1 主変更

| ファイル | 役割 |
|---|---|
| `src/core/effective_shape_plan.py` | admission契約、ゼロ幅境界の分類、required-zero伝播、同一点handoff処理 |
| `src/core/pipeline.py` | `PeakValueObservation`の境界runtime fieldと、解析中の全observation生成箇所 |
| `src/gui_wx/main_frame.py` | B4 debug artifactへのboundary admission/actionの記録 |

### 7.2 関連確認・必要時変更

| ファイル | 確認内容 |
|---|---|
| `src/vmd_writer/writer.py` | required-zeroで保護された同一点のゼロフレームが、冗長zero pruningで失われないこと |
| `src/core/preview_transform.py` | 境界zeroを含む同一planのPreview変換が失敗しないこと |
| `src/core/effective_shape_diagnostics.py` | 新しい境界failure code/actionをB3Cの固定enumとprivacy境界へ追加する場合の整合 |
| `src/core/output_diagnostics.py` | runtime契約フィールドのcanonicalizationとDebug ON/OFF identityの確認 |
| `src/core/analysis_debug_store.py` | stage／canonical／projection複製時に、追加したdebug payloadとsnapshot scopeを欠落させないことの確認 |
| `src/core/analysis_debug_trace.py` | capture status、snapshot scope、B4 artifactの固定contract versionとsafe serializationを確認する。B3 envelopeはschema v1のまま維持 |
| `docs/MS20_and_Beyond_Index.md` | B4Bの契約version、旧artifact方針、実装・検証状態の記録 |
| `docs/Implementation_Plan/MS28-B4_Implementation_Plan.md` | B4のbase admission・required-zero・受入条件との同期 |
| `docs/Implementation_Plan/MS28-B3C_Implementation_Plan.md` | B3Cは診断基盤、B4Bは製品処理修正である境界の明記 |

### 7.3 テスト

| ファイル | 役割 |
|---|---|
| `tests/test_ms28_b4b_boundary_admission.py` | B4Bの新規契約、境界分類、同一点zero、fail-closed fixture |
| `tests/test_ms28_b4b_debug_artifact_contract.py` | stage／canonical／projection artifactの全境界field、未所属境界配列、固定reason、contract versionの回帰 |
| `tests/test_ms28_b4_base_event_silence_core.py` | 既存admission、long/manual、required-zeroとの回帰 |
| `tests/test_ms28_b4_contract_identity.py` | runtime契約、Debug ON/OFF identity、payload互換 |
| `tests/test_ms20_b2_output_diagnostics.py` | `PeakValueObservation`のcanonical field追加と既存fingerprint回帰 |
| `tests/test_ms21_b3_pipeline_preview_integration.py` | observation生成からPreview入力までの境界field伝播 |
| `tests/test_ms28_b3c_resolver_diagnostics.py` | `admission_boundary_invalid`追加後の固定code／legacy detail回帰 |
| `tests/test_preview_transform.py` | 境界zeroを含むPreview生成 |
| `tests/test_vmd_writer_intervals.py` | required-zero、zero pruning、同一frame keyframeの保持 |
| `tests/test_ms21_b2_effective_shape_plan.py` | EffectiveShapePlanの既存shape・tail回帰 |
| `tests/test_ms22_b2_long_vowel_resolver.py` | 長音terminal・hold・decay回帰 |

## 8. 実装方針

### 8.1 EventSilenceAdmissionの契約

通常区間と境界点を同じフィールドへ格納しない。

```text
normal admission:
  effective_frame_range = (start, end), end > start
  boundary_only = false
  boundary_frame = None
  boundary_point_kind = None

boundary-only admission:
  effective_frame_range = None
  boundary_only = true
  boundary_frame = non-negative int
  boundary_point_kind = "end_zero"
  positive_point_kinds = ()
  positive_core_frame_ranges = ()
  enabled = true
  rejection_reason_code = None
```

追加する固定値は次の範囲に限定する。

- `boundary_only`: `bool`
- `boundary_frame`: `int | None`
- `boundary_point_kind`: `None | "end_zero"`
- `boundary_relation`: debug payload上の固定値。`same_vowel_same_frame`、`silence_gap`、`different_vowel_boundary`、`not_applicable`
- `boundary_action`: `preserved_zero_keyframe`、`not_applicable`

runtime契約へ含めるのは`boundary_only`、`boundary_frame`、`boundary_point_kind`、required-zeroへの反映結果とし、`boundary_relation`と`boundary_action`はdebug専用説明情報とする。

### 8.2 ゼロ幅境界の許可条件

`_build_event_silence_admissions`でcandidate shapeとeffective rangeを計算した後、`EventSilenceAdmission`生成前に次を判定する。

1. `effective_frame_range`がゼロ幅である。
2. `positive_point_kinds`が空である。
3. `positive_core_frame_ranges`が空である。
4. 境界frame上の正値point kindが空である。
5. 対象shapeのcontrol pointに、同じframeの`end_zero`が存在する。
6. shape provenanceが存在し、終了点の根拠を追跡できる。
7. 既存のevent順序・shape provenanceから、次のいずれかの境界関係を検証できる。
   - 同母音の終端と後続開始が同一frameで接続する`same_vowel_same_frame`。
   - 異母音への遷移点として、現在母音の終了と後続母音の開始関係が確認できる`different_vowel_boundary`。
   - 後続開始まで正のgapがあり、現在母音の終了点が無音側の境界として確認できる`silence_gap`。
8. reversed range、shape未生成、point kind不正、正値補間の根拠欠落がない。

#### B4B補正条件

boundary-onlyの受理可否は、上流イベントの観測値ではなく、最終候補shapeが実際に表現できる正値形状を持つかどうかで決定する。`event.peak_value`は診断用の上流メタデータとして保存するが、単独でboundary-onlyを拒否する条件にはしない。したがって、次のケースは受理対象に含める。

- `event.peak_value`が正値でも、候補rangeがゼロ幅である。
- `positive_point_kinds`、境界frame上の正値point kind、`positive_core_frame_ranges`がすべて空である。
- shape provenanceがあり、同一boundary frameの`end_zero`だけが最終候補shapeとして存在する。
- 境界関係が検証済みで、通常区間へ変換しなくてもクローズ点として意味を持つ。

反対に、正値control point、正値補間、正値core rangeのいずれかが最終候補shapeに存在する場合は、上流`event.peak_value`の値にかかわらずboundary-onlyを受理せず、fail-closedとする。これにより、正値イベントを誤って消すことと、正値出力を持たない終端ゼロ点を誤って解析失敗にすることを分離する。受理・拒否の各チェック結果と`event.peak_value`はdebug detailへ記録し、runtime identityには追加しない。

すべて満たす場合、通常区間の検査へ渡さず、境界only admissionへ変換する。`long_vowel_role`は必須条件にせず、今回のように`not_applicable`でも安全な境界処理を可能にする。境界関係を検証できない場合は`boundary_only`へ変換せず、fail-closedとする。関係の判定はdebug文字列や波形の見た目から推測せず、event index、前後event、shape provenance、control pointから決定する。`event.peak_value`が正値であることだけでは、候補shapeの正値証拠とはみなさない。

次の状態は許可しない。

- ゼロ幅なのに正値control pointがある。
- ゼロ幅なのにpositive core rangeがある。
- `end_zero`のframeが対象境界と一致しない。
- shape provenanceがなく、終了点を確認できない。
- reversed rangeや型不正をゼロ幅境界として扱う。

拒否時は、通常rangeの型・順序違反には既存の`admission_range_invalid`を使い、境界条件（end_zero不一致、関係不明、provenance不備）には固定code`admission_boundary_invalid`を使う。`admission_boundary_invalid`は、`src/core/effective_shape_diagnostics.py`の固定code／safe serializer、`src/gui_wx/main_frame.py`のadmission safe code allowlist、B3C診断回帰テストへ同じ変更単位で追加し、自由文字列をreason codeとして出力しない。例外を握り潰さない。`boundary_interval_unassigned`はadmission failure codeではなく、debug artifact rootの未所属境界reasonとして別allowlistへ固定する。

### 8.3 required-zeroへの伝播

境界only admissionの`boundary_frame`を、対象母音の`NormalizationContract.required_zero_frames`へ追加する。

- 境界フレームは半開rangeへ変換せず、単一frameとして保持する。
- 同一母音・同一frameの重複は集合化する。
- required-zeroがあるため、後段の冗長zero削除で境界zeroを除去しない。
- required-zeroは正値を消すためだけに使い、隣接する正値shapeを不必要に延長しない。

### 8.4 同一点handoffと無音gap

- 長音終端と後続同母音の開始が同一frameの場合、終端側の`end_zero`を明示的に保持する。
- 同じframeに同じ母音のzeroが複数生成される場合は、VMD出力上は1つへ統合してよい。ただし、そのframeのzero keyframeが存在することを受入条件とする。
- 次イベントが別母音または後続までgapがある場合も、現在母音のzero境界を保持し、次イベントの開始を前倒ししない。
- `boundary_only`を理由にshapeのhold、softness、ピーク値を再計算しない。

境界関係の固定分類は次の優先順位で決定する。複数条件が成立する場合も、この順序以外で分類しない。

1. `same_vowel_same_frame`
2. `different_vowel_boundary`
3. `silence_gap`
4. `not_applicable`（この値になった場合はboundary-only admissionを許可しない）

### 8.5 Debug artifact

B4の`base_event_admissions`へ、次を追加する。

- `boundary_only`
- `boundary_frame`
- `boundary_point_kind`
- `boundary_relation`
- `boundary_action`

`base_event_admissions`への記録対象は、通常admissionの区間重なりだけで決めない。通常admissionは従来どおりframe range／positive core rangeの重なりで記録し、boundary-only admissionは`boundary_frame`が当該silence observationの`silence_core_frame_ranges`または`boundary_fringe_frame_ranges`に含まれる場合に、そのframeを所属境界として記録する。`effective_frame_range=None`やpositive range空tupleだけを理由に除外しない。各行には、同一境界をprojection反復から識別するための`admission_key`と、`assignment_status="assigned_interval"`を固定値で記録する。

boundary-onlyのdebug rowでは、`boundary_action`を必ず`preserved_zero_keyframe`、`boundary_relation`を8.4の優先順位で固定する。通常admissionでは両値を`not_applicable`とする。これにより、境界処理の成功と、silence observationの`result`／`reason_code`を混同しない。

各boundary rowには、resolver側で生成した`boundary_admission_checks`を同じ固定構造で複製する。`events.csv`の`peak_evaluation`を後から推測して結合するのではなく、admission候補、最終候補shapeの正値証拠、`event_peak_value`、decisionを同一rowで追跡できる状態を契約とする。

所属intervalが存在しないboundary-only admissionは、interval内の`base_event_admissions`へ捏造して追加しない。stage payloadおよび同じ内容を持つcanonical／projection payloadのrootへ、次の固定配列を追加する。

```text
unassigned_boundary_admissions: [
  {
    ...same admission payload fields...,
    "admission_key": "event:<index>|vowel:<vowel>|frame:<frame>|shape:<shape_id>",
    "assignment_status": "unassigned",
    "boundary_action": "not_applicable",
    "boundary_relation": "<original verified relation>",
    "reason_code": "boundary_interval_unassigned"
  }
]
```

配列要素には`event_index`、`vowel`、`boundary_only`、`boundary_frame`、`boundary_point_kind`、`admission_key`、`assignment_status`、provenance、`required_zero_frame_ranges`、`boundary_admission_checks`を含め、原因調査に必要な情報を省略しない。`boundary_relation`は境界イベント自体の検証結果として保持し、`boundary_action`は未所属intervalでは実際に適用していないため`not_applicable`とする。対象intervalの推測、自由文の原因記録、別intervalへの付け替えは行わない。`boundary_interval_unassigned`はdebug artifact上の所属状態であり、通常のsilence observationの`result`／`reason_code`へ混在させない。未所属であることだけを理由に、すでに有効化されたruntime boundary-only admissionを再拒否したり、Preview／Writerの結果を変更したりしない。

同一run内で同じ`admission_key`が複数回記録されることは許可する。これはintervalまたはprojectionごとの観測を保持するためであり、ログ生成時に意味を変えずに重複排除しない。解析側は`run_id`、`projection_id`、`admission_key`で一意境界を集計する。

`projection_input`などstage開始前に採取された診断には、`diagnostic_snapshot_scope="pre_stage"`と`authoritative_for_stage=false`を付与する。stage完了後の最終diagnosticsには`diagnostic_snapshot_scope="post_stage"`と`authoritative_for_stage=true`を付与する。これにより、事前値の`preview_projection=not_attempted`を最終失敗と誤読しない。

debug payloadのJSON envelopeおよびpayload rootの`schema_version=1`は維持する。B4Bで新規生成するartifactの`contract_version`は`ms28-b4-silence-v2`へ更新する。producerは`src/gui_wx/main_frame.py`とし、genericなcanonical／projection複製は`src/core/analysis_debug_store.py`の既存経路を使用する。`src/core/analysis_debug_trace.py`はsafe serializationの確認対象とする。B4の既存v1 artifact、`tests/test_ms28_b4_contract_identity.py`のv1回帰、B4の完了記録は書き換えない。B4Bのv2期待値は`tests/test_ms28_b4b_debug_artifact_contract.py`、B4B計画、`docs/MS20_and_Beyond_Index.md`のB4B追記へ分離する。v1 artifactは履歴資料として保持し、上書き・再生成・runtime readは行わない。v1を読めることはB4Bのruntime受入条件に含めず、外部のread-only検査で旧root fieldを扱えることだけを互換性条件とする。

### 8.6 Runtime identityとdebug専用情報の境界

B4で定義済みのidentity境界を継承し、`EventSilenceAdmission`自体を`BasePlanIdentity`へ直接埋め込まない。循環を避けるため、`src/core/pipeline.py`の`PeakValueObservation`へ次の実行時入力を追加し、`output_diagnostics._observations_canonical()`へB4指定フィールドの後に固定順序で追加する。

- `boundary_only`
- `boundary_frame`
- `boundary_point_kind`

これらの値から`EventSilenceAdmission`と最終`NormalizationContract.required_zero_frames`を決定的に再生成できることを契約とする。`required_zero_frames`の最終値は、既存のEffectiveShapePlan／final projection canonical payloadで比較し、境界frameの変更を同一identityとして扱わない。`boundary_relation`、`boundary_action`、`boundary_interval_unassigned`の説明、`contract_version`、`unassigned_boundary_admissions`のdebug配列、自由文はdebug専用であり、BasePlanIdentity／save-state fingerprintへ含めない。

Debug ON/OFFで同一入力を処理した場合、上記runtime canonical field、admission enabled／拒否理由、final required-zero、EffectiveShapePlan、Preview／Writer入力、VMD保存可否は一致しなければならない。debug専用fieldだけの差分はidentity不一致にしてはならない。これを`tests/test_ms28_b4_contract_identity.py`で、境界only受理・境界拒否の両ケースについて固定する。

### 8.7 B4B補正時の診断情報

境界判定の結果を後から再現できるよう、debug専用detailへ次の固定項目を記録する。値は固定enum、bool、数値、frame範囲だけで表し、自由文を判定根拠にしない。

```text
boundary_admission_checks: {
  candidate_range: "zero_width" | "non_zero" | "reversed" | "not_available",
  positive_point_kinds_empty: bool | "not_available",
  boundary_positive_point_kinds_empty: bool | "not_available",
  positive_core_frame_ranges_empty: bool | "not_available",
  matching_end_zero: bool | "not_available",
  shape_provenance_available: bool | "not_available",
  boundary_relation_verified: bool | "not_available",
  event_peak_value: number | "not_available",
  decision: "accepted_boundary_only" | "rejected_boundary_invalid" | "not_applicable"
}
```

`event_peak_value`は、正値の上流観測と正値の最終候補shapeを区別するために必須とする。`decision`は製品処理のadmission結果と一致させるが、このdetail自体はruntime identityへ含めない。`admission_boundary_invalid`はfailure contextで固定domain／fieldへ写像し、`boundary_frame`と`boundary_point_kind`をunknownへ落とさない。cross-vowel handoffの固定reason `cross_vowel_handoff_crosses_silence_core`、`cross_vowel_handoff_exceeds_full_span_limit`はdebug safe allowlistに登録し、`not_evaluable`へfallbackさせない。未登録のreasonは従来どおり安全な固定値へ縮退させる。

このdetailは失敗時だけでなく、boundary-onlyを受理した成功時にも、`base_event_admissions`および`unassigned_boundary_admissions`へ保存する。候補shapeまたは上流値を取得できない場合、キーを省略せず、値を`not_available`として固定する。これにより、成功ログでも「値がない」のか「判定が記録されていない」のかを区別できる。`admission_key`、`assignment_status`、`diagnostic_snapshot_scope`はdebug artifactの追跡用であり、runtime identityへ含めない。

## 9. 詳細ステップ

1. 00/02のframe 380・151を再現する最小in-memory fixtureを、raw range、RMS後range、shape provenance、前後event付きで作成する。
2. `EventSilenceAdmission`へ境界onlyフィールドと不変条件を追加する。
3. `_build_event_silence_admissions`に境界判定ヘルパーを追加し、通常range検査の前に境界onlyへ振り分ける。
4. `_required_zero_frames_from_admissions`とnormalization contractへ境界frameを伝播する。
5. 同一点handoff、別母音境界、無音gapのshape/control pointを確認し、必要なzeroを保持する。
6. `main_frame.py`のadmission payloadとsilence observation分類へ境界結果を反映する。所属interval内のboundary-onlyは開口違反として扱わず、`boundary_action="preserved_zero_keyframe"`と8.4の固定`boundary_relation`で記録する。通常silence observationのroot `result`／`reason_code`は境界actionの説明で上書きしない。
7. Preview変換、Writerのrequired-zero保護、冗長zero削除を確認する。必要な場合だけ最小変更する。
8. `base_event_admissions`の所属判定をboundary frame対応へ更新し、interval未所属時は`unassigned_boundary_admissions`へ全fieldを保存する。所属状態、`admission_key`、boundary relation／action、固定reason、stage／canonical／projectionの同一内容をテストする。未所属状態はdebug上の所属情報であり、runtime admissionの再拒否条件にしない。
9. `pipeline.PeakValueObservation`の全生成箇所へruntime境界fieldを伝播し、`output_diagnostics._observations_canonical()`へ追加する。debug専用fieldをidentityから除外する。
10. B4 v1の既存テスト・完了記録を保持したまま、B4B v2のproducer・artifact・履歴方針を別テストで固定する。
11. 固定code／reason allowlistとsafe serializerを更新し、`admission_boundary_invalid`と`boundary_interval_unassigned`を自由文字列化しないことを確認する。
12. B4/B3Cの契約文書、受入条件、Indexの現在状態を実装結果に合わせて更新する。
13. source自動テスト、sampleスクリプト、ユーザー手動確認を別の証拠として記録する。

### 9.1 B4B補正の実装順

1. 実ログのframe 380／420と同じ構造を、`value=0.0`かつ明示的な正値`peak_value`（`0.2181`／`0.2755`）を持つゼロ幅fixtureとして追加する。候補shapeは同一frameの`end_zero`のみとし、前後に別母音eventを置く。
2. boundary-only判定から`event.peak_value <= MORPH_FRAME_OPEN_EPSILON`の単独拒否条件を除去し、候補shapeの正値point、境界正値point、正値core rangeを拒否根拠とする。
3. 正値候補shapeがある同型fixtureは引き続きfail-closedとし、上流peak値の正負だけで受理・拒否が逆転しないことを確認する。
4. `boundary_admission_checks`とfailure contextの固定fieldを記録し、`admission_boundary_invalid`のdomain／field、cross-vowel reasonのsafe allowlistを同じ変更単位で補正する。
5. B4Bの対象回帰、関連回帰、全pytestを順に実行し、00相当fixtureが`effective_shape`、Preview、Writer入力まで到達することを確認する。
6. その後にユーザー側のDebug ON/OFF、GUI、EXE、MMD確認を別証拠として実施し、ログ上の受理と最終表示・出力を分けて記録する。

### 9.2 今回の微修正・debug出力補正の実装順

1. B4B補正済みのruntime判定、required-zero、Preview／Writer入力を変更しないことを先に固定する。
2. `main_frame.py`のadmission payloadへ`boundary_admission_checks`、`admission_key`、`assignment_status`を追加し、成功時にも同じ構造を保存する。
3. 未所属rootでは、`boundary_relation`を元の検証結果として保持し、`boundary_action`は実際に適用していないことを示す`not_applicable`とする。`boundary_interval_unassigned`は所属理由だけに使用する。
4. stage、canonical、projectionの全artifactで上記fieldの欠落・自由文字列化・値の改変がないことを確認する。
5. stage開始前／完了後のdiagnosticsにsnapshot scopeとauthorityを追加し、既存の`not_evaluable`を単純に成功・失敗へ読み替えない。
6. artifact契約テストへ、同一`admission_key`の複数観測、boundary-only受理、boundary invalid拒否、`not_available`固定値、Debug ON/OFF identity不変を追加する。
7. source自動テストと最新sample再実行で、B4Bの処理成功とdebug出力の完全性を別々に確認する。

## 10. 状態遷移 / データ契約

```text
effective range valid
  └─ normal admission → existing processing

effective range zero-width
  ├─ no positive point + matching end_zero
  │    └─ boundary-only admission
  │         ├─ boundary zero → required_zero_frames
  │         ├─ same-vowel same-frame → explicit close keyframe preserved
  │         └─ gap/different vowel → close boundary preserved, no extension
  └─ positive point / provenance missing / malformed
       └─ fail-closed admission failure
```

境界onlyは解析失敗、Preview失敗、VMD保存禁止へ昇格させない。境界処理自体が失敗した場合は、既存のresolver failure・downstream skip契約を維持する。

## 11. テスト方針

### 11.1 決定的fixture

- 00相当: RMS後`(380, 380)`、`value=0.0`・明示的な`peak_value=0.2181`、前shape終端zero、同一frameの後続境界。別母音境界のため、実ログと同じ`different_vowel_boundary`を再現する。
- 00 TEXT＋音声相当: RMS後`(420, 420)`、`value=0.0`・明示的な`peak_value=0.2755`、前後別母音event、shape provenanceは同一frameの`end_zero`のみ。
- 02相当: RMS後`(151, 151)`、`peak_value=0`、`end_zero`のみ、後続までgapあり。
- 正常区間: `end > start`の通常event。
- 不正ゼロ幅: 上流`peak_value`が正値でも、正値control point、境界正値point、または正値core rangeがある。
- provenance欠落: shapeなし、またはend_zero frame不一致。
- reversed range: 既存fail-closed。
- 長音source/continuation/terminalと同一点同母音handoff。
- manual adjustmentとrequired-zeroが共存する既存ケース。

### 11.2 回帰

- B4 base event admission、handoff、required-zero、suspicious分類。
- B1/B2の長音hold・decay・terminal順序。
- PreviewとWriterの同一EffectiveShapePlan利用。
- VMD frameの同一母音・同一frameのzero保持。
- Debug ON/OFFでruntime契約、Preview、Writer、VMD保存可否、identityが一致すること。
- B3C failure detailのallowlist、legacy details、`details_availability`を変更しないこと。
- boundary-only admissionが所属silence intervalのdebug rowへ現れ、interval未所属時は別intervalへ付け替えず、固定reasonと`assignment_status`付きでrootへ記録されること。未所属だけでruntime結果を再拒否しないこと。
- runtime境界fieldはcanonical identityへ含まれ、debug専用fieldは含まれないこと。Debug ON/OFFの受理・拒否、required-zero、EffectiveShapePlan、Preview／Writer入力、保存可否が一致すること。
- 新規artifactは`schema_version=1`＋`contract_version=ms28-b4-silence-v2`、既存v1 artifactは保持され、runtimeで読み替え・上書きされないこと。
- stage／canonical／projectionの各`silence_observations` payloadが、`base_event_admissions`内のboundary rowとrootの`unassigned_boundary_admissions`を欠落なく同じ内容で保持すること。
- `base_event_admissions`と`unassigned_boundary_admissions`の各boundary rowが、`boundary_admission_checks`、`admission_key`、`assignment_status`を持ち、`events.csv`との後付け結合なしにadmission decisionを追跡できること。
- 上流`event.peak_value`が正値でも、最終候補shapeが同一frameの`end_zero`だけならboundary-onlyとして受理されること。
- 最終候補shapeに正値point、境界正値point、正値core rangeがある場合は、`event.peak_value`の値にかかわらずfail-closedとなること。
- 00相当のframe 380／420 fixtureが`effective_shape`、Preview入力、Writer入力まで到達し、`sync_context_build_failed`へ短絡しないこと。
- `boundary_admission_checks`に`event_peak_value`と各判定結果が記録され、`admission_boundary_invalid`がunknown domain／fieldへ落ちないこと。
- cross-vowel handoff固定reasonが`not_evaluable`へfallbackせず、未知reasonだけが既存のsafe fallback対象となること。
- stage開始前とstage完了後のdiagnosticsがsnapshot scopeとauthorityを持ち、事前の`not_attempted`と最終の`ready`／`completed`を区別できること。

### 11.3 実ファイル手動確認（未実施）

今回確認できたのは、ユーザー側source実行によるDebug ON解析6件である。native GUIの目視、EXE、実MMDでの最終表示・出力確認は別証拠として残す。

- 00/02: `admission_boundary_invalid`によるPreview停止が発生しない。
- 00/02: 問題箇所の無音区間で対象母音がクローズされる。
- 01: 既存のPreview表示とタイムラインを維持する。
- source 6 runの成功だけでEXE・MMDまで修正完了とはせず、ログ・Preview・VMD結果を分離して記録する。

## 12. 受け入れ条件

- [x] B4B-AC01: 通常の`effective_frame_range`は引き続き半開区間で、`end > start`を満たす。
- [x] B4B-AC02: `end_zero`のみを持つ安全なゼロ幅候補は、上流`event.peak_value`が正値でもboundary-only admissionとして受理される。fixtureと最新source runで確認済み。
- [x] B4B-AC03: boundary-only admissionは`effective_frame_range=None`、`boundary_frame`あり、正値範囲なしで保存される。
- [x] B4B-AC04: boundary frameが`NormalizationContract.required_zero_frames`へ伝播する。
- [x] B4B-AC05: 同一点同母音handoffの境界分類と、同一frameのzero keyframe保持をfixtureで確認した。
- [x] B4B-AC06: gapまたは別母音境界で、現在母音のzeroを維持し、後続shapeを前倒し・延長しない。
- [x] B4B-AC07: 正値point、provenance欠落、end_zero不一致、reversed rangeはfail-closedとなる。
- [x] B4B-AC08: 00/02相当fixtureと最新source runでresolverが失敗せず、`effective_shape`、Preview入力、Writer入力まで到達する。EXE／MMDでの確認はAC14に分離する。
- [x] B4B-AC09: 01相当fixtureと既存long/manual fixtureの出力が変わらない。
- [x] B4B-AC10: PreviewとWriterが同一修正済みEffectiveShapePlanを使用し、無音部の開口を残さないことを自動回帰で確認した。
- [x] B4B-AC11: B4 debug artifactにboundary actionとrelationが固定値で記録される。
- [x] B4B-AC12: B3/B3Cのlegacy payload、例外隔離、privacy、runtime identity回帰を維持した。
- [x] B4B-AC13: 自動テストは終了コード0で完了し、skip・未実施の手動／EXE／MMD確認を別記した。
- [ ] B4B-AC14: 実ファイル・GUI・exe・MMDの確認結果を、自動テストの成功と混同しない。
- [x] B4B-AC15: boundary-only admissionは`boundary_frame`を含む所属silence intervalの`base_event_admissions`へ記録され、通常の区間重なり判定だけで欠落しない。所属intervalが無い場合は別intervalへ付け替えず、`boundary_interval_unassigned`としてrootへ記録する。
- [x] B4B-AC16: 所属intervalがないboundary-only admissionは、root `unassigned_boundary_admissions`へ全必須fieldと`reason_code="boundary_interval_unassigned"`を保存し、どのintervalの`base_event_admissions`にも混在させない。未所属だけでruntime admissionを再拒否しない。
- [x] B4B-AC17: B4Bの新規artifactは`schema_version=1`と`contract_version="ms28-b4-silence-v2"`を持つ。B4の既存v1 artifact・テスト・完了記録は保持され、v1のruntime read・上書き・再生成は行わない。
- [x] B4B-AC18: `pipeline.PeakValueObservation`から`boundary_only`、`boundary_frame`、`boundary_point_kind`がruntime canonical identityへ固定順序で含まれ、`boundary_relation`、`boundary_action`、未所属境界配列、contract version、自由文はdebug専用として除外される。
- [ ] B4B-AC19: Debug ON/OFFでboundary受理・拒否、required-zero、EffectiveShapePlan、Preview／Writer入力、VMD保存可否が一致し、境界関係の分類は固定優先順位に従う。自動fixtureとidentity回帰は確認済みだが、実Debug ON/OFF比較は未実施。
- [x] B4B-AC20: `admission_boundary_invalid`と`boundary_interval_unassigned`が固定allowlist／safe serializerを通り、未知文字列・例外文字列・自由文がreason codeとして保存されない。最新6 runではcross-vowel固定reasonの`not_evaluable` fallbackも確認されない。
- [x] B4B-AC21: stage、canonical run artifact、projection artifactの`silence_observations` payloadで、境界row・未所属境界配列・schema／contract version・固定reasonが一致する。
- [x] B4B-AC22: 正値の上流`event.peak_value`と、同一frameの`end_zero`だけを持つ最終候補shapeを分離して判定し、boundary-only admissionを受理する。
- [x] B4B-AC23: 00相当のframe 380／420 fixtureと最新source runが`effective_shape`、Preview入力、Writer入力まで到達し、`sync_context_build_failed`へ短絡しない。
- [x] B4B-AC24: 同じゼロ幅・正値peak条件でも、正値control point、境界正値point、正値core rangeのいずれかがあればfail-closedとなる。
- [x] B4B-AC25: `boundary_admission_checks`へ`event_peak_value`、候補shape、境界関係、decisionがB4Bの保存artifactへ固定値で記録され、failure contextのdomain／fieldがunknownへ落ちない。未取得値は`not_available`で固定する。
- [x] B4B-AC26: cross-vowel handoffの固定reasonがsafe allowlistに保持され、最新6 source runで`not_evaluable` fallbackが解消されている。
- [x] B4B-AC27: B4B artifactの各boundary rowへ`boundary_admission_checks`、`admission_key`、`assignment_status`を保存し、未取得値を`not_available`で固定する。
- [x] B4B-AC28: stage開始前／完了後のdiagnosticsにsnapshot scopeとauthorityを保存し、事前の`not_attempted`と最終の`ready`／`completed`を区別できる。

### 12.1 現在の判定

B4Bの製品処理補正は実装済みで、fixtureおよび直近6件のsource Debug runで、正値`event.peak_value`と`end_zero`だけの最終候補shapeを分離し、`effective_shape`、Preview、Writer、最終acceptanceまで到達することを確認した。したがって、旧来のboundary admissionによる処理停止は現時点で未再現である。

今回の追加作業は製品処理の再設計ではなく、成功時を含めたdebug artifactの追跡性補正であり、実装と自動回帰を完了した。残る受入条件はB4B-AC19（実Debug ON/OFF、native GUI、EXE、MMDの境界）である。`unassigned_boundary_admissions`は最新ログで確認された診断上の所属状態であり、それ自体を製品処理失敗またはboundary-only拒否とは判定しない。

## 13. リスクと対策

| リスク | 対策 |
|---|---|
| 不正なゼロ幅を受理して開口を残す | 正値点なし、end_zero一致、provenanceありを必須化 |
| 同一点zeroを冗長削除する | required-zeroへ伝播し、Writer pruningの保護テストを追加 |
| 長音hold/decayを短縮する | long roleの既存分岐を変更せず、boundary-onlyを別分岐にする |
| PreviewとWriterで結果が分かれる | 同一EffectiveShapePlanとNormalizationContractの使用を確認 |
| Debug artifact変更でidentityが変わる | runtime契約とdebug説明項目を分離し、ON/OFF比較を行う |
| boundary-onlyがsilence observationのdebug rowから抜ける | boundary frameをcore/fringeへ所属付けし、区間重なりとは別に記録する |
| v1/v2 artifactの期待値が混在する | 新規producer・テスト・Index・B4計画をv2へ同期し、v1は履歴read-onlyとする |
| observation生成箇所とcanonicalizationの片方だけを更新する | `pipeline.py`の全constructor、`output_diagnostics.py`、pipeline／diagnostic回帰を同じ変更単位で更新する |
| 未所属境界がログから欠落する | root `unassigned_boundary_admissions`へ全fieldを保存し、stage／canonical／projectionの同一性を検証する |
| 未所属境界の反復記録を別イベントと誤認する | `run_id`、`projection_id`、固定`admission_key`、`assignment_status`で観測単位と集計単位を分離する |
| 成功したboundary-onlyの判定根拠をログから再現できない | `boundary_admission_checks`を成功・失敗の両方で同じartifact rowへ保存し、`events.csv`との推測結合を不要にする |
| projection開始前の`not_attempted`を最終失敗と誤読する | snapshot scopeとauthorityを固定値で保存し、最終diagnosticsを別の証拠として扱う |
| B3Cの失敗診断を壊す | B3C serializer、legacy details、failure codeを後方互換で維持 |
| 上流peak値を最終shapeの正値証拠と誤認して、安全な境界zeroを拒否する | 00相当の正値`peak_value`＋`end_zero`のみfixtureを必須化し、候補shapeのpoint／core evidenceで判定する |
| 正値候補shapeまでboundary-onlyとして受理する | 正値point、境界正値point、正値core rangeを明示的なfail-closed条件として回帰する |
| safe allowlist不足で固定reasonが`not_evaluable`に隠れる | cross-vowel reasonを固定allowlistへ追加し、reason fallbackの回帰を追加する |
| 失敗contextのfieldがunknownへ落ち、再現条件を追跡できない | `admission_boundary_invalid`のdomain／fieldとboundary fieldの固定写像を受入条件に含める |
| 00/02だけを通して別ケースを壊す | 正常01、long/manual、reversed、positive zero-widthを同時に回帰する |

## 14. 実装時の注意

- `zero_width`を単純に有効rangeへ変換しない。
- `boundary_only`を長音判定の別名にしない。`long_vowel_role=not_applicable`でも成立する一般境界契約とする。
- `suspicious`ログを製品処理の失敗理由として再利用しない。
- 既存の`admission_range_invalid`を、境界処理の成功状態へ書き換えない。成功時は例外を発生させず、失敗時だけ従来のfailure契約を使う。
- `admission_boundary_invalid`は採用固定とし、coreの固定code enum、GUI safe allowlist、serializer、回帰テストを同じ変更単位で更新する。通常range違反の`admission_range_invalid`とは混同しない。
- 同一frameの同一母音について、VMD仕様上の重複フレームを増やすことではなく、zero keyframeが最終出力に存在することを保証する。
- `boundary_relation=not_applicable`のままboundary-onlyを許可しない。分類はevent順序とprovenanceで決定し、debug自由文から境界関係を推測しない。
- `event.peak_value`を最終候補shapeの正値証拠として単独利用しない。正値point、境界正値point、正値core rangeを候補shapeから検査する。
- `boundary_admission_checks`は原因追跡用であり、runtime identityや製品入力を直接決定する追加状態にしない。debug ON/OFFの製品結果を変えない。
- `base_event_admissions`は`effective_frame_range`の有無だけで除外しない。boundary frameのinterval所属を先に判定する。
- `boundary_interval_unassigned`はroot `unassigned_boundary_admissions`だけに保存し、通常intervalの`reason_code`や`contract_violation_reasons`へ混在させない。
- stage、canonical run、projectionの3経路で、境界row・未所属配列・固定reason・versionを同じ内容で保持する。いずれか一つでも欠落した場合はデバッグ機構の受入失敗とする。
- B3C診断の「原因記録」とB4Bの「製品処理修正」を同一の完了判定にしない。
- B4B補正の自動テストが通っても、実ファイルのPreview表示、EXE、MMD上の見た目を自動的に完了扱いにしない。
- 実装後は変更ファイル、テスト終了コード、実ファイル再現、GUI／exe／MMD確認の未実施範囲を分けて報告する。
