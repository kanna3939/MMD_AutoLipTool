# MMD_AutoLipTool Pipeline データ契約仕様書

## 1. 文書情報

- 文書名: `docs/Pipeline_Data_Contract_Specification.md`
- 対象プロジェクト: `MMD_AutoLipTool`
- 対象バージョン系: Ver0.4.x 以降
- 現行基準: MS15 closeout 後 / MS16 以降の拡張準備
- 主対象領域:
  - `src/core/`
  - `src/vmd_writer/`
  - `src/gui_wx/`
- 主対象データ:
  - TEXT処理結果
  - 母音列
  - 音声解析結果
  - RMS / peak評価
  - timing event
  - VowelTimingPlan
  - observation
  - fallback情報
  - Preview data
  - VMD writer input
  - GUI通知用データ
- 主GUI: wxPython
- 主開発環境: Codex
- Coding AI 前提: Codex
- 関連文書:
  - `docs/Specification_Prompt_v4.md`
  - `docs/Security_Safety_Specification.md`
  - `docs/Error_Handling_Specification.md`
  - `docs/GUI_State_Theme_Specification.md`
  - `docs/VMD_Output_Specification.md`
  - `docs/MMD_Audio_WAV_Compatibility_Specification.md`
  - `docs/repo_milestone.md`
  - `docs/Version_Control.md`

---

## 2. 文書目的

本書は、`MMD_AutoLipTool` の pipeline において、各処理層の間で受け渡されるデータの意味・責務・不変条件を定義する。

本書は、アルゴリズムの完全な解説書ではない。

本書の目的は以下である。

- pipeline 内で何を正本データとするかを明確にする
- Preview data と VMD writer input を正本と混同しない
- TEXT、音声、解析結果、timing plan、observation の責務境界を明確にする
- `peak_value`、zero peak、fallback、bridge、smoothing の意味を固定する
- 入力変更・パラメータ変更時に、どのデータを無効化するかを明確にする
- worker / GUI / writer 間で古い結果が混入する事故を防ぐ
- Preview と VMD 出力の意味的整合を保つ
- Codex による実装・修正・レビュー時の判断基準にする

本書の中心方針は以下である。

```text
Pipeline の正本は、解析時点の入力TEXT・解析用音声・パラメータセットに対応する timing plan である。
Preview data と VMD writer input は、この timing plan から派生するデータであり、正本ではない。
```

---

## 3. 適用範囲

本書は、以下に適用する。

- TEXT読込後の正規化
- かな化
- 母音列生成
- 音声解析入力
- 解析用WAV
- Whisper結果
- segment / word 情報
- RMS系列
- peak評価
- timing event
- VowelTimingPlan
- observation
- fallback情報
- bridge / smoothing判断材料
- Preview data生成
- VMD writer input生成
- GUI state への通知
- worker結果
- late callback discard
- pipeline_result_invalid の判定
- パラメータ変更時の結果無効化

---

## 4. 非対象

本書では、以下を主対象としない。

- VMDバイナリフォーマットの詳細
- MMD用WAVのチャンク仕様
- FFmpeg / ffprobe の呼び出し詳細
- Whisper内部アルゴリズム
- wxPython GUI レイアウト詳細
- テーマ追従の詳細
- エラーダイアログの表示仕様
- PyInstaller配布仕様
- Qt / PySide6 旧GUIの仕様
- MMD本体の内部仕様

ただし、上記が pipeline data の意味や無効化条件に影響する場合は、本書の契約を優先して参照する。

---

## 5. 基本方針

### 5.1 データ契約を優先する

本書では、実装上のクラス名・関数名・フィールド名の完全固定よりも、各データが満たすべき意味・責務・不変条件を優先する。

実装上の型名やファイル構成は現行コードに従う。

ただし、実装が変わっても、以下は維持する。

- どのデータが正本か
- どのデータが派生物か
- どの入力に対応した結果か
- どの条件で無効化されるか
- Preview と writer がどの情報を共有すべきか
- fallback や warning をどう保持するか

### 5.2 正本と派生物を分ける

pipeline の正本は、解析時点の入力TEXT・解析用音声・パラメータセットに対応する timing plan である。

派生物:

- Preview data
- Waveform表示用データ
- VMD writer input
- GUI表示用要約
- Status表示
- InfoPanel表示

これらは正本ではない。

### 5.3 GUI表示を正本にしない

Preview や Waveform は、ユーザー確認のための表示である。

GUI表示が正しいかどうかは重要だが、pipeline の正本ではない。

以下は禁止する。

- Preview表示を元に writer 出力を再構成する
- Waveform表示用に間引いたデータを解析正本として扱う
- GUI表示上の状態だけで timing plan の有効性を判断する

### 5.4 writer出力を正本にしない

VMD writer は、timing plan から VMD key を生成する最終出力層である。

VMD writer が生成した keyframe 列は出力結果であり、pipeline の中間正本ではない。

### 5.5 observation は補助情報である

observation は、event や timing plan がどのように補正・評価されたかを説明する補助情報である。

observation は timeline event の代替正本ではない。

### 5.6 古い結果を現在結果にしない

TEXT、音声、解析用WAV、Whisper timing、または解析結果に影響する`morph_upper_limit`が変更された場合、既存のtiming plan、Preview data、VMD保存可能状態は無効化する。`closing_hold_frames`、`closing_softness_frames`、`long_vowel_mode`は生成時のbaseを再解析するparameterではなく、現在のbaseへeffective shapeを再解決するoutput-only設定である。

### 5.7 MS19 音声のみ入力の正本

音声のみ入力では、TEXT pathを必須としない。Whisper書き起こし本文、書き起こし元、Whisper timing result、解析用WAVを入力正本として `VowelTimingPlan` を生成する。

書き起こし編集を適用した時点で既存の `VowelTimingPlan` は無効化し、保持済みWhisper timing resultを使った再解析が成功するまでPreview操作とVMD保存を不可とする。再解析成功後のVMD writer inputは、TEXT pathではなく現在の `VowelTimingPlan` から生成する。

解析失敗時は書き起こし編集内容を保持する。解析開始時にcaptureした旧planが同一audio、
同一base identity、同一morph upper limitで再利用可能な場合は、
旧`VowelTimingPlan`、adjustment history、selectionを確認用に復元する。ただし新しい
diagnostic ERRORを保持し、VMD保存は禁止する。再利用不能な場合は
`analysis_result_valid = False`、`current_timing_plan = None`、
`analysis_pending_rebuild = True` とする。VMD保存だけが失敗した場合は、有効な解析結果と
`VowelTimingPlan` を失わない。

### 5.8 MS19-B8 作業状態reset

`新規作業...` は、現在の入力・書き起こし・解析結果に対するsession参照を破棄し、未入力の `text_audio` / `IDLE` 状態へ戻す操作である。`analysis_pending_rebuild = False` とし、古い `VowelTimingPlan`、Preview、VMD保存可能状態を次作業へ引き継がない。

この操作は `UiState` 全体を置換しない。recent files、最後に使った各フォルダ、theme、解析パラメータは保持する。source TEXT / audio、保存済みVMD・MMD用WAV、解析用WAV cacheの実体を削除してはならない。

audio / analysis job IDは単調に進め、reset前のcallbackを現在作業へ反映してはならない。Busy中はresetを実行せず、既存のキャンセル導線完了後に実行する。

---

## 6. pipeline 全体フロー

本ツールの pipeline は、概念上以下の流れを持つ。

```text
TEXT
↓
TEXT正規化
↓
かな化
↓
母音列生成
↓
音声入力
↓
解析用WAV
↓
Whisper解析
↓
RMS / peak評価
↓
timing event生成
↓
VowelTimingPlan
↓
observation付与
↓
fallback / warning付与
↓
Preview data生成
↓
VMD writer input生成
↓
VMD出力
```

MS16以降で mp3 / m4a 入力を扱う場合は、音声入力前段に以下が入る。

```text
mp3 / m4a / wav
↓
ffprobe
↓
FFmpeg変換
↓
解析用WAV
```

MMD用WAV出力は、VMD出力とは別の出力系統として扱う。

### 6.1 MS25 MMD一括出力の正本境界

MMD一括出力は、現在の有効な`EffectiveShapePlan`、入力音声のsource identity、
同一時点の`OutputDiagnosticsSnapshot`を開始contextとして固定する。個別に保存済みの
VMD、MMD用WAV、診断レポートを入力や再利用元にしてはならない。

一括出力では、同一親directory内のtemporary / staging directoryへVMD、MMD用WAV、
診断レポートを生成・検証する。3成果物と入力音声identityの検証が完了し、commit直前の
current state fingerprintが開始時fingerprintと一致した場合だけ、既存destinationを
置換しない形で専用directoryへ確定する。失敗、cancel、stale、collisionでは既存出力を
変更せず、stagingだけをcleanup対象とする。

一括出力の`DeliveryStartContext`はVMD / MMD用WAV / reportの共通入力契約であり、
`DeliveryTerminalResult`はcommit成否、primary error、cleanup statusの正本である。

---

## 7. データ正本と派生データ

### 7.1 正本データ

正本データとは、後段処理が信頼すべき基準データである。

本ツールでは、主な正本を以下とする。

| データ | 正本性 |
| --- | --- |
| 入力TEXT内容 | TEXT処理の正本 |
| 解析用WAV | 音声解析・波形表示の正本 |
| 母音列 | TEXT由来の発声単位の正本 |
| timing plan | Preview / writer の正本 |
| parameter set | 解析結果の前提条件 |
| input identity | 結果がどの入力に対応するかの識別情報 |

### 7.2 派生データ

派生データとは、正本から生成される表示用・出力用・説明用データである。

| データ | 派生元 |
| --- | --- |
| Preview data | timing plan |
| VMD writer input | timing plan |
| VMD keyframes | VMD writer input |
| Waveform表示データ | 解析用WAV |
| Status表示 | UiState / 処理結果 |
| InfoPanel表示 | 入力情報 / 変換情報 |
| warning表示 | fallback / error info |

### 7.3 派生データの禁止事項

派生データは正本を上書きしてはならない。

禁止事項:

- Preview data から timing plan を復元して正本化する
- VMD keyframes から timing plan を逆生成して正本化する
- GUI表示用の短縮情報を writer に渡す
- Waveform描画用に間引いたデータをRMS正本として扱う

---

## 8. input identity と結果無効化

### 8.1 input identity の目的

input identity は、解析結果がどの入力とパラメータに対応しているかを識別するための概念である。

これにより、古いworker結果や古いtiming planが現在状態へ混入することを防ぐ。

### 8.2 input identity の候補

実装上、以下の全部または一部を用いて input identity を構成してよい。

- text path
- text content hash
- audio input path
- analysis wav path
- analysis wav hash
- audio duration
- audio sample rate
- audio channel policy
- parameter set
- morph upper limit
- closing hold
- closing softness
- job id
- pipeline version

完全なhash実装は必須ではない。

ただし、少なくとも「現在の入力に対応した結果か」を判定できる仕組みを持つ。

### 8.3 無効化条件

以下が変更された場合、既存の timing plan、Preview data、VMD保存可能状態を無効化する。

- TEXTファイル
- TEXT内容
- 音声ファイル
- 解析用WAV
- mp3 / m4a 変換元
- 解析用WAV生成方針
- morph upper limit
- closing hold
- closing softness
- pipeline結果に影響するパラメータ
- Whisper解析結果
- RMS / peak評価結果
- timing plan生成ロジック
- writer契約に影響するshape仕様

### 8.4 late callback discard

worker結果が返ってきた時点で、input identity または job id が現在状態と一致しない場合、その結果を破棄する。

破棄した結果は以下へ反映しない。

- UiState
- Preview
- Waveform
- VMD保存可能状態
- Statusの成功表示
- InfoPanelの解析結果

---

## 9. TEXT処理データ契約

### 9.1 目的

TEXT処理は、入力テキストをリップ生成に使える文字列データへ整える。

### 9.2 入力

- TEXTファイルパス
- 読込文字列
- 文字コード情報
- 読込時警告
- TEXT安全性検証結果

### 9.3 出力

- 正規化済みテキスト
- 読み処理対象テキスト
- 警告情報
- エラー情報

### 9.4 不変条件

TEXT処理出力は以下を満たす。

- 文字列として扱える
- コードとして評価されない
- コマンドとして実行されない
- 制御文字の扱いが安全性仕様に従う
- 文字数上限を満たす
- 行長上限を満たす
- 文字化けした内容を成功扱いしない

### 9.5 エラー時

TEXT処理に失敗した場合は、後段へ進まない。

エラー分類:

- `text_decode_failed`
- `text_validation_failed`
- `text_to_vowel_failed`

状態復帰は `Error_Handling_Specification.md` に従う。

---

## 10. 母音列データ契約

### 10.1 目的

母音列は、TEXT由来の発声単位を、MMDの母音モーフへ対応づけるための中間データである。

### 10.2 入力

- 正規化済みテキスト
- かな化結果
- 読み変換結果

### 10.3 出力

- 母音列
- 母音イベント候補
- 元テキストとの対応情報
- fallback情報

### 10.4 対象母音

対象母音は原則として以下に限定する。

```text
あ
い
う
え
お
```

### 10.5 不変条件

母音列は以下を満たす。

- 空でないことが望ましい
- 各要素は対象母音のいずれかへ対応する
- 元TEXTとの対応を追跡できることが望ましい
- 不明な読みがある場合は fallback または warning として扱う
- MMDモーフ名と混同しない

### 10.6 no_vowel_events

母音イベントが生成できない場合は、以下のいずれかとして扱う。

- `no_vowel_events`
- `text_to_vowel_failed`

処理継続できない場合、timing plan を生成してはならない。

---

## 11. 音声解析入力データ契約

### 11.1 目的

音声解析入力は、Whisper / RMS / waveform / timing plan生成のための音声正本である。

MS16以降では、解析用WAVを音声解析入力の正本とする。

### 11.2 入力

- ユーザー音声ファイル
- ffprobe結果
- FFmpeg変換結果
- 解析用WAVパス
- 解析用WAV検証結果

### 11.3 出力

- 解析用WAV
- duration
- sample rate
- channel count
- waveform source
- 音声メタ情報
- warning情報

### 11.4 解析用WAV固定仕様

解析用WAVは以下に固定する。

```text
PCM signed 16-bit little-endian
44100 Hz
mono
```

### 11.5 不変条件

音声解析入力は以下を満たす。

- ファイルが存在する
- 読込可能である
- 解析用WAV仕様を満たす
- duration が有効である
- duration が上限内である
- data chunk が存在する
- data size が0ではない

### 11.6 Waveformとの関係

Waveform表示は解析用WAVを正本とする。

stereo入力や3ch以上入力であっても、表示波形は解析用mono音声を基準にする。

### 11.7 AudioProbeResult (MS17追加)

ffprobe による検査結果を保持するデータ契約。

```python
@dataclass(frozen=True)
class AudioStreamInfo:
    codec_name: str | None
    sample_rate_hz: int | None
    channel_count: int | None
    duration_sec: float | None

@dataclass(frozen=True)
class AudioProbeResult:
    source_path: Path
    file_size_bytes: int
    duration_sec: float
    format_name: str | None
    audio_stream: AudioStreamInfo
```

役割:
- 入力音声の基本メタデータを保持する
- 入力制限（ファイルサイズ、音声長）の合格を証明する
- 解析用WAV生成（FFmpeg）や、解析処理（Whisper）への入力情報の基準とする

### 11.8 AnalysisWavResult (MS17追加)

FFmpeg による変換結果とキャッシュ情報を保持するデータ契約。

```python
@dataclass(frozen=True)
class AnalysisWavSpec:
    """解析用WAVの固定仕様"""
    sample_rate_hz: int = 44100
    sample_fmt: str = "s16"
    channels: int = 1
    codec: str = "pcm_s16le"

@dataclass(frozen=True)
class AnalysisWavResult:
    """変換結果"""
    wav_path: Path
    spec: AnalysisWavSpec
    duration_sec: float
    is_cached: bool
```

役割:
- 変換済み解析用WAVがどこにあり、どのような仕様（16bit/44.1kHz/mono）であるかを保証する
- 既存の解析処理（Whisper / RMS）への入力パスを提供する
- キャッシュ利用の有無を記録する
- 失敗時にはこの結果自体が生成されないか、無効な状態として扱われる

---

## 12. Whisper結果データ契約

### 12.1 目的

Whisper結果は、音声内の発話タイミングを推定するための補助情報である。

Whisper結果は timing plan 生成に使うが、必ずしも唯一の正本ではない。

### 12.2 入力

- 解析用WAV
- Whisperモデル
- transcribe設定
- job id
- cancellation flag

### 12.3 出力

- segment情報
- word情報
- confidence相当情報
- start / end
- fallback可能性
- warning情報

### 12.4 不変条件

Whisper結果は以下を満たすことが望ましい。

- segment が時系列順である
- start <= end
- start / end が音声duration範囲内である
- word情報がある場合、segment範囲と矛盾しない
- 空結果の場合は fallback判断へ渡す
- 例外を握りつぶさない

### 12.5 word / segment fallback

Whisper word情報がない場合でも、segment情報が使えるなら segment fallback を行ってよい。

segment情報も不十分な場合は、均等配分 fallback を検討する。

### 12.6 Whisper結果不足

以下は、必ずしも致命的エラーではない。

- `whisper_no_words`
- `whisper_no_segments`
- `whisper_result_invalid`

fallback可能な場合は warning として扱う。

fallback不可の場合は解析エラーとする。

---

## 13. RMS / peak評価データ契約

### 13.1 目的

RMS / peak評価は、各母音イベントの開口強度や補正判断に使う。

### 13.2 入力

- 解析用WAV
- timing候補
- sample rate
- event interval
- RMS window設定

### 13.3 出力

- RMS系列
- local peak
- global peak
- peak window
- peak_value候補
- fallback情報
- observation用情報

### 13.4 peak_value

`peak_value` は、該当母音イベントの最大モーフ値候補である。

不変条件:

```text
0.0 <= peak_value <= 1.0
```

### 13.5 zero peak

`peak_value == 0.0` 相当のイベントは、通常発声イベントとは区別する。

方針:

- zero-only shape の原因として記録してよい
- zero-only shape を最終VMDに残してはならない
- zero peak を通常発声の peak と混同しない
- Preview / writer に zero peak であることを伝えられることが望ましい

### 13.6 RMS失敗時

RMS系列生成に失敗しても、fallback可能な場合は処理継続してよい。

分類:

```text
rms_series_failed
→ fallback可能なら warning
→ fallback不可なら error
```

fallbackした場合は、observation または warning に記録する。

---

## 14. timing event データ契約

### 14.1 目的

timing event は、1つの母音発声単位を表す。

timing event は、VowelTimingPlan を構成する基本単位である。

### 14.2 必須概念

timing event は、概念上以下を持つ。

- morph_name
- vowel
- start_sec
- end_sec
- duration_sec
- time_sec
- peak_value
- source_text_index
- source_vowel_index
- fallback情報
- observation参照

実装上のフィールド名は現行コードに従う。

### 14.3 morph_name

`morph_name` は原則として以下のいずれかとする。

```text
あ
い
う
え
お
```

### 14.4 時刻条件

timing event は以下を満たす。

- `start_sec >= 0`
- `end_sec >= 0`
- `start_sec <= end_sec`
- `duration_sec >= 0`
- `time_sec >= 0`
- `time_sec` はイベント代表時刻として使える
- 音声duration範囲から大きく逸脱しない

### 14.5 peak条件

timing event の `peak_value` は以下を満たす。

```text
0.0 <= peak_value <= 1.0
```

### 14.6 short span

短すぎるeventは short span として扱ってよい。

short span は、通常shapeではなく short fallback の対象になる可能性がある。

### 14.7 エラー条件

以下は invalid event として扱う。

- morph_name が対象外
- start_sec > end_sec
- 負の時刻
- peak_value が範囲外
- durationが異常
- input identity と対応しない

invalid event が存在する場合、pipeline_result_invalid として扱う。

---

## 15. VowelTimingPlan データ契約

### 15.1 目的

VowelTimingPlan は、pipeline の中心正本である。

Preview data と VMD writer input は、VowelTimingPlan から派生する。

### 15.2 入力

- 母音列
- Whisper結果
- RMS / peak評価
- fallback情報
- パラメータセット
- input identity

### 15.3 出力

- timing event list
- observation list または observation mapping
- warning list
- fallback list
- input identity
- parameter snapshot
- duration情報
- plan生成メタ情報

### 15.4 不変条件

VowelTimingPlan は以下を満たす。

- 現在のTEXTに対応する
- 現在の解析用音声に対応する
- 現在のパラメータセットに対応する
- timing event list を持つ
- event は時系列として解釈可能である
- 各eventは対象morph_nameを持つ
- 各eventの時刻は妥当である
- 各eventのpeak_valueは0.0〜1.0である
- observationはeventと対応可能である
- fallback使用時はwarningまたはmetadataとして追跡できる

### 15.5 空plan

有効な母音イベントが存在しない場合、有効なVowelTimingPlanとして扱わない。

この場合:

- `no_vowel_events`
- `timing_plan_build_failed`
- `pipeline_result_invalid`

のいずれかとして扱う。

### 15.6 parameter snapshot

VowelTimingPlan は、生成時点の主要パラメータを保持または参照できることが望ましい。

対象:

- morph upper limit
- closing hold
- closing softness
- audio identity
- text identity
- pipeline version
- shape policy version

`morph_upper_limit`が変更された場合、既存planは無効化する。`closing_hold_frames`、
`closing_softness_frames`、`long_vowel_mode`の変更はoutput-onlyであり、既存baseを保持したまま
Preview / writer / diagnosticsが同じeffective shape planを再解決する。

### 15.7 MS22 generation state / effective output

`GenerationState`は、常に値を持つ`GenerationSettings`と、組み込みまたはユーザーpresetのstable IDを
保持するbase-lessな設定状態である。解析成功後は、これを`OutputEditState`のgeneration stateとして
base identity、canonical adjustment snapshot、output historyへ一体化する。

- modeの優先順位は、terminal eventの明示override > active generation settings > application default `hold`
- Preview、VMD writer、diagnostics、fingerprintは同じ`EffectiveShapePlan`を参照する
- presetの表示名変更やactive IDだけの変更はeffective morph outputを変更せず、fingerprintを変えない
- `presets.json`はユーザーpresetだけを保存し、built-in、active selection、base、adjustment、historyは保存しない
- INIはgeneration settingsとactive preset IDを保存するが、sessionのbase、history、selectionは保存しない
- workspace resetはgeneration / active presetを保持し、input、base、history、selection、failureをclearする

### 15.8 MS23 model profile / resolved morph-name state

`ModelProfileState`は、active model profile ID、baseline preset ID、resolution status、resolution reasonを
保持する。profileの解決順位は、`event adjustment > model profile > preset > application default`とし、
profileが未選択の場合は従来どおり日本語5母音を application default とする。

- 組み込みのモーフ名セットは日本語 `あ / い / う / え / お` と Latin `A / I / U / E / O` に限定し、任意のモデル固有マッピングは扱わない
- profileは `morph_upper_limit`、nullableなhold / softness / long-vowel設定、default preset IDを持つ。upper limitの変更は既存baseを無効化し、output-only設定は既存baseを保持してeffective shape planを再解決する
- active profileは、値・モーフ名セット・default presetの直接編集と削除を禁止する。baseline presetは値の更新・削除を禁止し、名前変更だけを許可する。profileが参照するpresetの削除も禁止する
- profile persistenceはINIと同じ保存場所のversioned `profiles.json`（schema version 1、初期上限100件）を使い、書込み失敗時は旧ファイルと旧状態を保持する。壊れた入力はpartial importせず、no-profileへfail closedする
- INIはactive profile IDとbaseline preset IDだけを保存し、profile本体・base・history・selectionは保存しない。`profiles.json`、`presets.json`、INIはruntime user dataであり、package成果物へ含めない
- writer、Preview、diagnostics、diagnostic reportは最終解決済みの同じordered morph-name tupleを受け取る。profileの設定変更はanalysis / output-only分類に従って反映し、profile表示名だけの変更ではframe/value/count/order、VMD 30fps、timing、fingerprintを変えない
- text-only / voice-onlyを含む全入力経路で、profile適用後の同じ名前順を使う。解析失敗・空出力・cancel・rollback・stale result discardでは、旧profile状態と旧outputの原子性を崩さない
- workspace resetはprofile projection、generation、active presetを保持し、input、base、history、selection、diagnostics、failureをclearする。Undo/Redoはprofile stateとoutput stateを同じ履歴取引として再投影する

---

## 16. observation データ契約

### 16.1 目的

observation は、timing event の生成・補正・評価理由を説明する補助情報である。

observation は、Preview や writer が shape判断や表示説明に利用できる。

### 16.2 位置づけ

observation は正本ではない。

正本は timing event / VowelTimingPlan である。

observation は以下を補足する。

- なぜこの区間になったか
- どのfallbackが使われたか
- RMS / peakがどのように評価されたか
- short span かどうか
- bridge候補かどうか
- smoothing候補かどうか
- zero peakかどうか

### 16.3 入力

- timing event
- RMS / peak評価結果
- Whisper結果
- fallback情報
- 補正前interval
- 補正後interval
- window情報

### 16.4 出力

observation は、概念上以下を含んでよい。

- event id
- original interval
- refined interval
- peak window
- local peak
- global peak
- peak_value source
- fallback_reason
- sample count
- short_span flag
- zero_peak flag
- bridge candidate
- smoothing candidate
- warning

### 16.5 不変条件

observation は以下を満たす。

- eventと対応可能である
- eventより強い正本として扱わない
- observationだけでVMD出力を決定しない
- eventの不正を隠さない
- fallback理由を破棄しない
- warningを消さない

### 16.6 observation欠落時

observation が欠落しても、timing event が妥当であれば処理継続できる場合がある。

ただし、以下のような機能が observation に依存している場合は注意する。

- bridge
- smoothing
- top-end shaping
- short span 判断
- zero peak判断
- Preview詳細表示

observation欠落により判断不能な場合は、保守的fallbackを使う。

---

## 17. fallback / warning データ契約

### 17.1 目的

fallback / warning は、処理が理想経路ではないが継続可能であることを示す。

fallback は失敗ではない。

ただし、ユーザーや開発者が後から確認できるように記録する。

### 17.2 代表 fallback_reason

代表的な fallback_reason は以下である。

```text
whisper_no_words
whisper_no_segments
segment_fallback
uniform_distribution
rms_unavailable
short_span
zero_peak
peak_window_too_small
audio_too_quiet
anchor_assignment_failed
observation_missing
```

### 17.3 warning と error の違い

| 種別 | 意味 |
| --- | --- |
| warning | 処理継続可能。結果は生成される |
| error | 処理継続不可。結果は無効 |

### 17.4 fallback使用時の契約

fallback を使用した場合は以下を満たす。

- fallback理由を保持する
- timing plan が妥当なら処理継続してよい
- Preview生成へ進んでよい
- VMD保存可能としてよい
- ただし、fallback結果が不変条件を満たすこと
- 必要に応じてStatusや詳細情報に表示する

### 17.5 fallback禁止条件

以下の場合、fallbackで処理継続してはならない。

- TEXTが読めない
- 母音列が生成できない
- 解析用WAVが存在しない
- 音声durationが不正
- timing eventが全て不正
- peak_valueが範囲外
- input identity が一致しない
- pipeline_result_invalid と判定された

---

## 18. Preview data への変換契約

### 18.1 目的

Preview data は、VowelTimingPlan をGUI上で確認するための表示用データである。

Preview data は正本ではない。

### 18.2 入力

- VowelTimingPlan
- timing event
- observation
- fallback / warning
- Viewport
- theme情報
- shape policy

### 18.3 出力

- 母音レーン情報
- 発声区間
- peak_value表示情報
- shape表示情報
- bridge / smoothing表示情報
- closing hold / softness表示情報
- warning表示情報

### 18.4 不変条件

Preview data は以下を満たす。

- VowelTimingPlanに対応する
- input identity が現在状態と一致する
- eventの意味を変えない
- peak_valueの意味を変えない
- shape_kindを不正に変えない
- VMD writer と意味的に整合する
- 表示負荷軽減のための省略が正本を破壊しない

### 18.5 完全一致しなくてよい部分

Previewは表示用であるため、以下はVMD出力と完全一致しなくてよい。

- ピクセル単位の形状
- 線幅
- 色
- viewport clipping
- 表示上の省略
- 拡大縮小時の描画解像度

ただし、意味は一致する必要がある。

### 18.6 禁止事項

以下は禁止する。

- Previewだけ新shapeでwriterが旧shapeのまま
- writerだけ新shapeでPreviewが旧shapeのまま
- PreviewだけbridgeされてVMDではbridgeされない
- closing softness がPreviewだけに存在する
- VMDに出力しない発声をPreviewに正本のように表示する
- 古いtiming plan由来のPreviewを現在結果として表示する

---

## 19. VMD writer input への変換契約

### 19.1 目的

VMD writer input は、VowelTimingPlan からVMD keyframe生成へ渡すためのデータである。

### 19.2 入力

- VowelTimingPlan
- timing event
- observation
- peak_value
- shape policy
- closing hold
- closing softness
- bridge / smoothing判断
- morph upper limit
- parameter snapshot

### 19.3 出力

- writer用event列
- shape生成用情報
- morph key生成用情報
- warning / fallback情報
- input identity

### 19.4 不変条件

writer input は以下を満たす。

- VowelTimingPlanと対応する
- 現在input identityと一致する
- morph_nameは `あ / い / う / え / お`
- start_sec <= end_sec
- peak_valueは0.0〜1.0
- zero peakの扱いが保持される
- short span情報が失われない
- closing hold / softness情報が渡る
- bridge / smoothing判断材料が必要に応じて渡る

### 19.5 writerの責務

writer は、writer input からVMD keyframe列を生成する。

writer は以下を行う。

- 秒からframeへの変換
- shape生成
- zero key処理
- duplicate normalization
- zero-only shape除去
- morph upper limit適用
- VMD出力

### 19.6 禁止事項

以下は禁止する。

- writer input生成時にobservationだけを正本としてeventを置き換える
- GUI表示用データをwriterへ直接渡す
- peak_value範囲外をwriterへ渡す
- input identity不一致の結果をwriterへ渡す
- パラメータ変更後の古いwriter inputで保存可能にする

---

## 20. GUI / worker との受け渡し契約

### 20.1 worker result

pipeline処理がworkerで行われる場合、worker結果は成功・失敗を明示する。

推奨構造:

```text
success: bool
result: optional pipeline result
error: optional error info
warnings: optional warning list
job_id: worker job id
input_identity: input identity
```

### 20.2 成功結果

成功結果には以下を含めることが望ましい。

- VowelTimingPlan
- observation
- fallback / warning
- Preview生成に必要な情報
- writer input生成に必要な情報
- input identity
- parameter snapshot

### 20.3 失敗結果

失敗結果には以下を含める。

- error_code
- phase
- exception_type
- exception_message
- traceback
- job_id
- input_identity

### 20.4 GUI反映条件

worker結果をGUIへ反映する前に以下を確認する。

- job id が現在状態と一致する
- input identity が現在状態と一致する
- result が不変条件を満たす
- error でない
- cancellation flag が立っていない

### 20.5 warning表示

warnings が存在する場合、処理成功であっても詳細情報に残す。

必要に応じてStatusに短く表示してよい。

例:

```text
Whisper結果が不十分だったため、fallbackを使用しました。
```

### 20.6 MS20 output diagnostics state

GUIは、現在workspaceの入力、`VowelTimingPlan`、writer parameter、failure、解析中止状態から単一の `OutputDiagnosticsSnapshot` を再構築する。

- `current_diagnostic_failure`
- `current_output_diagnostics_snapshot`
- `confirmed_warning_save_state_fingerprint`
- `analysis_cancelled`

input変更、parameter変更、解析成功、workspace resetでは、旧workspaceに由来する上記状態を
一括clearする。解析開始時は表示snapshotとWARNING確認済みfingerprintをclearする一方、
current job専用rollback payloadには開始直前の`DiagnosticFailureInput`だけを保持してよい。
解析失敗時はcurrent failureを設定し、旧planを復元した場合もERRORにより保存禁止とする。
GUI同期後は表示snapshotを現在状態から再構築する。

解析中止要求だけではterminal状態を確定しない。current jobのterminal callbackで旧planが
再利用可能ならbase、adjustment history、selectionを復元する。prior failureがなければ
`analysis_cancelled=True`としてcancel INFOと現在の保存可否を両立する。prior failureが
あれば既存ERRORを復元し、cancel INFOを抑止して保存禁止を維持する。

analysis terminalはcurrent job IDとactive状態、audio worker terminalはcurrent job ID、
expected kind、`RUNNING`状態をすべて満たす最初のcallbackだけを受理する。job ID不一致、
audio worker kind不一致、shutdown中、または既にterminalのlate / duplicate callbackは、
timing plan、failure、snapshot、fingerprint、確認済み状態、cancel状態を変更しない。

解析開始時のmorph upper limit / hold / softnessはimmutable snapshotとして保持し、terminal時に
base identityとは別に完全一致を検証する。不一致の場合はsuccess resultをcommitせず、
failure / cancelでもrollbackせず、再解析待ち・保存不可へ移行する。

---

## 21. 不変条件一覧

### 21.1 全体不変条件

pipeline出力全体は以下を満たす。

- 現在のTEXTと対応する
- 現在の解析用音声と対応する
- 現在のパラメータセットと対応する
- input identity が現在状態と一致する
- timing event が妥当である
- Preview data は timing plan から派生している
- writer input は timing plan から派生している

### 21.2 timing event不変条件

- morph_name は `あ / い / う / え / お`
- start_sec >= 0
- end_sec >= 0
- start_sec <= end_sec
- duration_sec >= 0
- time_sec >= 0
- peak_value は0.0〜1.0
- 音声durationから大きく逸脱しない

### 21.3 VowelTimingPlan不変条件

- event list を持つ
- event list は空でないことが望ましい
- event list は時系列として解釈可能
- observation と対応可能
- warning / fallback が保持される
- parameter snapshot と対応する

### 21.4 observation不変条件

- eventと対応可能
- eventの代替正本ではない
- fallback理由を保持できる
- peak評価情報を保持できる
- bridge / smoothing判断材料を保持できる

### 21.5 Preview不変条件

- timing planと対応する
- writerと意味的に整合する
- input identityが一致する
- 古い結果ではない

### 21.6 writer input不変条件

- timing planと対応する
- morph_nameが対象範囲内
- peak_valueが範囲内
- closing hold / softness 情報を保持する
- zero peak情報を失わない
- input identityが一致する

### 21.7 MS21 adjustment / effective shape契約

解析結果のbase timing planと、単イベント編集を保持するcanonical adjustment snapshotは
分離する。Preview、diagnostics、VMD保存は、両者からcore resolverが生成した同じ
`EffectiveShapePlan` を派生元とする。

単イベントの正方向終了offset、event別closing hold、event別closing softnessは、
直後の非0・異母音shapeに限定したmanual crossfade intentになり得る。global parameter、
peak、start offset、slope ratioだけではmanual crossfadeを有効にしない。

`EffectiveShapePlan.manual_crossfades` は、manual intentを除いたcomparison outputと
final outputが異なり、実際の非0重複がある場合だけ生成する。metadataにはsource / target
base event index、母音、整数frame overlap、重複内で値0.95以上のtarget明示control pointを
保持する。補間値や複数morph合計は推定せず、metadataやnotice文面をsave-state
fingerprintへ直接含めない。effective frameまたはeffective tailが変化した場合は、既存の
effective output identityによりfingerprintが変化する。

GUI同期では、1回の同期に対して`BaseTimingPlanInput`、base identity、
`EffectiveShapePlan`をそれぞれ最大1回だけ構築し、diagnostics、Preview、selected editor、
action stateへ同じimmutable contextを渡す。edit / reset selectedで得た検証済み
`AdjustmentUpdateResult.effective_plan`は、base identityとcanonical snapshotが一致する場合だけ
同期hintとして再利用する。Undo / Redo等のadjustment-only同期ではplayback context、
ParameterPanel、PlaceholderContainer全体を不要に再描画しない。

---

## 22. エラー時の扱い

### 22.1 pipeline_result_invalid

pipeline出力が本書の不変条件を満たさない場合、`pipeline_result_invalid` として扱う。

この場合:

- Preview生成へ進まない
- VMD保存可能状態にしない
- 解析結果を無効化する
- Busy状態を解除する
- エラー詳細を表示可能にする

### 22.2 timing_plan_build_failed

timing plan を生成できない場合は `timing_plan_build_failed` として扱う。

状態復帰:

- TEXT入力は保持
- 音声入力は保持
- Waveformは保持してよい
- Previewはクリア
- VMD保存不可
- 再実行可能

### 22.3 observation_build_failed

observation生成に失敗した場合、処理継続可否を分ける。

- observationなしでも安全にwriter出力可能なら warning
- observation必須のshape判断ができないなら error
- 保守的fallbackで処理可能なら warning

### 22.4 peak_evaluation_failed

peak評価失敗時は以下とする。

- fallback可能なら warning
- peak_valueが決定できないなら error
- zero peakとして扱う場合は理由をobservationに記録する

### 22.5 fallback使用時

fallback使用時は、エラーではなく warning とする。

ただし、fallback後の結果が不変条件を満たすことが必要である。

---

## 23. テスト観点

### 23.1 TEXT / 母音列

- UTF-8 TEXTから母音列が生成される
- 空TEXTが適切に拒否される
- 母音イベントなしが `no_vowel_events` になる
- 不明読みがfallbackまたはwarningになる

### 23.2 input identity

- TEXT変更で既存planが無効化される
- 音声変更で既存planが無効化される
- パラメータ変更で既存planが無効化される
- 古いjob idのworker結果が破棄される
- input identity不一致の結果が保存可能にならない

### 23.3 Whisper / fallback

- word情報ありで通常plan生成
- word情報なしでsegment fallback
- segmentなしで均等配分fallback
- Whisper失敗で解析結果無効
- fallback使用時にwarningが保持される

### 23.4 RMS / peak

- RMS系列からpeak_valueが生成される
- peak_valueが0.0〜1.0に収まる
- RMS失敗時にfallbackされる
- zero peakが通常peakと区別される

### 23.5 observation

- eventとobservationが対応する
- fallback_reasonが保持される
- short_spanが記録される
- bridge候補が記録される
- observation欠落時に保守的fallbackになる

### 23.6 Preview / writer整合

- Preview dataがtiming planから生成される
- writer inputがtiming planから生成される
- Previewとwriterでshape意味が一致する
- closing hold / softnessが両方へ反映される
- bridge / smoothingが両方へ反映される
- manual crossfadeがPreviewとwriterの両方へ同じcontrol pointとして反映される
- output-equivalentなmanual intentではmanual metadataとfingerprintが変化しない

### 23.7 pipeline_result_invalid

- peak_value範囲外でinvalid
- morph_name対象外でinvalid
- start_sec > end_sec でinvalid
- input identity不一致でinvalid
- invalid時にPreview生成へ進まない
- invalid時にVMD保存可能にならない

---

## 24. 実装変更時の禁止事項

### 24.1 正本破壊

以下は禁止する。

- Preview dataを正本として扱う
- writer keyframesを正本として扱う
- observationをtimeline eventの代替正本として扱う
- GUI表示用データをpipeline正本として扱う

### 24.2 無効化漏れ

以下は禁止する。

- TEXT変更後に古いtiming planを保存可能にする
- 音声変更後に古いPreviewを残す
- パラメータ変更後に古いwriter inputでVMD保存可能にする
- job id不一致の結果を反映する

### 24.3 fallback情報破棄

以下は禁止する。

- fallbackを使用したのに理由を残さない
- warningを握りつぶす
- Whisper結果不足を成功通常経路のように扱う
- RMS失敗を記録せずに固定値へ置き換える

### 24.4 Preview / writer乖離

以下は禁止する。

- writerだけ新shape対応する
- Previewだけ新shape対応する
- bridge / smoothing の判断がPreviewとwriterで分岐する
- closing hold / softness の片方だけ反映する

### 24.5 不変条件無視

以下は禁止する。

- peak_value範囲外を許容する
- 対象外morph_nameをwriterへ渡す
- start_sec > end_sec のeventを許容する
- input identity不一致を許容する
- pipeline_result_invalidを保存可能にする

---

## 25. 実装報告の必須項目

pipeline またはデータ契約に関わる変更を行った場合、実装報告には以下を含める。

### 25.1 基本項目

- 確認したファイル
- 変更したファイル
- 変更したデータ構造
- 変更した入力契約
- 変更した出力契約
- 変更した不変条件

### 25.2 timing plan

- timing eventへの影響
- VowelTimingPlanへの影響
- input identityへの影響
- parameter snapshotへの影響
- 無効化条件への影響

### 25.3 observation / fallback

- observationへの影響
- fallback_reasonへの影響
- warningへの影響
- bridge / smoothing判断への影響
- zero peakへの影響

### 25.4 Preview / writer

- Preview dataへの影響
- VMD writer inputへの影響
- Previewとwriterの整合確認
- VMD出力仕様への影響

### 25.5 テスト

- 実行した自動テスト
- 実行した手動確認
- 未確認のデータ経路
- fallback経路の確認有無
- invalid経路の確認有無

---

## 26. 関連文書

### 26.1 `docs/Specification_Prompt_v4.md`

アプリ全体仕様を定義する。

本書は、pipelineで受け渡されるデータ契約を補完する。

### 26.2 `docs/Error_Handling_Specification.md`

pipeline エラー、fallback、worker失敗、late callback、pipeline_result_invalid の扱いを定義する。

本書の不変条件違反は、エラー仕様書の L5: Pipeline / Timing Plan レイヤーに対応する。

### 26.3 `docs/GUI_State_Theme_Specification.md`

GUI状態、Preview / Waveform更新、late callback反映、表示無効化の扱いを定義する。

本書の input identity と GUI state は、この文書と併せて参照する。

### 26.4 `docs/VMD_Output_Specification.md`

VMD出力仕様を定義する。

本書の VMD writer input は、この文書の writer契約に従う。

### 26.5 `docs/MMD_Audio_WAV_Compatibility_Specification.md`

音声入力、解析用WAV、MMD用WAV出力仕様を定義する。

本書の音声解析入力は、この文書の解析用WAV仕様に従う。

### 26.6 `docs/Security_Safety_Specification.md`

入力安全性、出力安全性、外部ツール安全性を定義する。

pipelineの入力検証や失敗時の安全停止は、この文書と整合させる。

### 26.7 `docs/repo_milestone.md`

マイルストーン履歴と現在地を記録する。

pipeline契約に関わる大きな変更は必要に応じて記録する。

### 26.8 `docs/Version_Control.md`

変更履歴を記録する。

本書の作成・更新、およびpipeline契約変更も記録対象とする。

---

## 27. 変更履歴

### 2026-09-03 / MS25-B5

- MMD一括出力の開始context、staging生成、current fingerprintによるcommit guard、既存出力保護、`DeliveryTerminalResult`のデータ境界を追加。

### 2026-08-20 / MS23-B6 cross regression同期

- model profile state、precedence、profile persistence、resolved morph-name tuple、Undo / Redo / reset境界を追加。
- writer、Preview、diagnostics、reportの名前契約と、profile failure / mutation guardのfail-closed境界を明記。

### 2026-08-11 / MS22-B6 lifecycle同期

- generation state、preset persistence、output-only設定、mode precedence、workspace resetの境界を追加。
- `morph_upper_limit`だけをanalysis terminal parameter guardとし、hold / softness / long-vowel modeはeffective output再解決へ整理。
- Preview、VMD writer、diagnosticsの共通`EffectiveShapePlan`参照と、session stateをINI / JSONへ保存しない契約を明記。

### 2026-07-26 / MS21-B5追加補正

- base timing plan、canonical adjustment、shared `EffectiveShapePlan` の境界を追加。
- manual crossfade metadata、0.95判定、effective output fingerprintとの関係を固定。

### 2026-07-19 / MS20-B7

- output diagnosticsのworkspace stateと一括clear対象を固定。
- analysis cancelのterminal確定、旧plan再利用、ERROR優先契約を追加。
- late / duplicate callbackによるdiagnostics上書き禁止を明記。

### 2026-05-01 / 初版

- `MMD_AutoLipTool` の pipeline データ契約を独立文書化。
- pipeline の正本を、解析時点の入力TEXT・解析用音声・パラメータセットに対応する timing plan と定義。
- Preview data と VMD writer input を timing plan からの派生データとして定義。
- input identity と結果無効化条件を定義。
- TEXT処理、母音列、音声解析入力、Whisper結果、RMS / peak評価、timing event、VowelTimingPlan、observation の契約を整理。
- observation を timeline event の代替正本ではなく補助情報として定義。
- fallback / warning を処理継続可能な契約状態として定義。
- peak_value、zero peak、short span、bridge / smoothing の扱いを整理。
- Preview data と VMD writer input の意味的整合を定義。
- pipeline_result_invalid の条件とエラー時の扱いを整理。
- worker result、job id、late callback discard、GUI反映条件を定義。
- 実装変更時の禁止事項と実装報告の必須項目を追加。
