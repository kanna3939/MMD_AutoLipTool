# MMD_AutoLipTool 音声入力・MMD用WAV互換仕様書

## 1. 文書情報

- 文書名: `docs/MMD_Audio_WAV_Compatibility_Specification.md`
- 対象プロジェクト: `MMD_AutoLipTool`
- 対象バージョン系: Ver0.4.x 以降
- 主対象マイルストーン: MS17 以降
- 対象機能:
  - wav / mp3 / m4a 入力
  - FFmpeg / ffprobe による音声正規化
  - 解析用WAV生成
  - MMD用WAV出力
  - 波形表示用音声データ
- 主対象環境: Windows 11
- 主GUI: wxPython
- 配布想定: PyInstaller onefile 形式の実行用 ZIP

---

## 2. 文書目的

本書は、`MMD_AutoLipTool` における音声入力、解析用WAV、MMD用WAV出力の仕様を定義する。

MMDはレガシーツールであり、形式上は正しいWAVであっても、チャンク構造、bit depth、sample rate、WAVE_FORMAT_EXTENSIBLE、metadata chunk などの条件により読み込めない場合がある。

そのため、本ツールでは以下を分離して扱う。

1. ユーザーが読み込む入力音声
2. AutoLipTool内部で解析に使う解析用WAV
3. MMDに読み込ませるためのMMD用WAV

本書の目的は、入力の利便性とMMD互換性を両立することである。

---

## 3. 基本方針

### 3.1 入力は広く受ける

ユーザー入力では、利便性を優先する。

MS17初期対応対象は以下とする。

```text
.wav
.mp3
.m4a
````

以下はMS17初期対象外とする。

```text
.ogg
.aiff
.aif
.flac
.wma
.mp4
.mov
その他動画・音声形式
```

ただし、将来必要になった場合は、FFmpeg対応状況とテスト負荷を確認したうえで拡張を検討する。

### 3.2 内部処理は固定形式へ正規化する

解析用WAVは、内部処理の安定性を優先して固定形式へ変換する。

解析用WAV仕様:

```text
PCM signed 16-bit little-endian
44100 Hz
mono
RIFF/WAVE
余分なchunkなしを目標
```

解析用WAVは、Whisper、RMS、波形表示、timing plan生成の正本として扱う。

### 3.3 MMD用WAVはMMD互換性を優先する

MMD用WAVは、MMDで読み込めることを優先して、レガシー互換の単純なPCM WAVとして出力する。

MMD用WAV仕様:

```text
PCM signed 16-bit little-endian
44100 Hz
stereo
RIFF/WAVE
fmt chunk size 16
audio format 1 = PCM
data chunkあり
JUNK / bext / iXML / fact / cue / smpl 等の余分なchunkは原則含めない
WAVE_FORMAT_EXTENSIBLE は使わない
float WAV は使わない
24bit / 32bit WAV は使わない
```

MS17-B7実装では、FFmpegのWAV出力に `LIST` chunk が混入して検証に失敗するケースを確認した。
MMD互換性を優先するため、MMD用WAV出力では `-bitexact` を指定し、`fmt` chunk の直後に `data` chunk が来る単純構造へ寄せる。

### 3.4 音声内容は加工しない

本ツールは、リップモーション生成支援ツールであり、音声編集ツールではない。

そのため、以下は行わない。

```text
音量正規化
loudness normalize
peak normalize
compressor
limiter
無音トリム
自動フェード
自動ノイズ除去
```

入力音声の時間軸と音量感は、可能な限り維持する。

---

## 4. 入力音声仕様

### 4.1 対応拡張子

MS17初期対応の入力音声拡張子は以下とする。

| 拡張子 | 扱い |
| ---------------- | --- |
| `.wav` | 対応 |
| `.mp3` | 対応 |
| `.m4a` | 対応 |
| `.ogg` | 非対象 |
| `.aiff` / `.aif` | 非対象 |
| `.flac` | 非対象 |
| その他 | 非対象 |

`.m4a` は、スマートフォン録音や一般ユーザーの音声素材として出てくる可能性があるため、初期対応対象に含める。

### 4.2 入力音声の多様性

ユーザー入力では、以下のような音声が存在することを前提とする。

* 16bit WAV
* 24bit WAV
* 32bit WAV
* float WAV
* 44.1kHz
* 48kHz
* 96kHz
* mono
* stereo
* 3ch以上の多チャンネル音声
* TTS出力WAV
* スマートフォン録音m4a
* metadata付き音声
* JUNK / LIST / bext / iXML 等のchunkを含むWAV

これらを直接MMD互換とみなさず、FFmpeg / ffprobe による検査と変換を経由する。

### 4.3 入力ファイルサイズ上限

入力音声ファイルのサイズ上限は以下とする。

```text
500MB
```

500MBを超える場合は、処理対象外としてエラーにする。

この上限は、セキュリティ上の絶対限界ではなく、Windows向け個人制作ツールとして応答性と安定性を守るための運用上限である。

### 4.4 音声長上限

音声長上限は、既存仕様に合わせて以下とする。

```text
15分
```

15分を超える音声は、原則としてエラー停止する。

---

## 5. チャンネル数の扱い

### 5.1 基本方針

本ツールでは、入力音声、解析用WAV、MMD用WAVでチャンネル数の扱いを分ける。

### 5.2 入力時

入力音声のチャンネル数は以下のように扱う。

| 入力チャンネル数 | 扱い |
| -------- | -------------------------------- |
| mono | そのまま有効 |
| stereo | ch1 / ch2 を有効対象とする |
| 3ch以上 | ch1 / ch2 のみ有効対象とし、ch3以降は無視または破棄 |

3ch以上の音声は、MMD向けの通常用途から外れるため、ch3以降を解析対象にもMMD用出力対象にも含めない。

### 5.3 解析用WAV

解析用WAVは常に mono とする。

| 入力 | 解析用WAV |
| ------ | ----------------------------- |
| mono | monoのまま |
| stereo | ch1 / ch2 をモノミックス |
| 3ch以上 | ch1 / ch2 のみをモノミックスし、ch3以降は無視 |

解析用mono mixの概念は以下とする。

```text
mono = (ch1 + ch2) / 2
```

実際の変換処理はFFmpegの仕様に従うが、3ch以上を全チャンネルmixしないことを重視する。

### 5.4 MMD用WAV

MMD用WAVは、MMD互換性とB7実装範囲を優先し、入力チャンネル数に関わらず stereo で出力する。

| 入力 | MMD用WAV |
| ------ | ----------------------- |
| mono | stereo |
| stereo | stereo |
| 3ch以上 | ch1 / ch2 のみを残した stereo |

MMD用WAVでは、3ch以上の多チャンネルWAVを出力しない。

---

## 6. 解析用WAV仕様

### 6.1 目的

解析用WAVは、AutoLipTool内部で以下に使う。

* Whisper解析
* RMS解析
* timing plan生成
* peak_value評価
* 波形表示
* Preview生成の前提となる音声時間軸

解析用WAVは、MMDに読み込ませる出力音声ではない。

### 6.2 固定仕様

解析用WAVは以下に固定する。

```text
PCM signed 16-bit little-endian
44100 Hz
mono
RIFF/WAVE
```

### 6.3 波形表示との関係

波形表示は、解析用WAVを正本とする。

つまり、stereo入力であっても、GUI上の波形表示は解析に使ったmono mix後の波形を表示する。

MMD用WAVがstereoで出力される場合でも、波形表示は解析用mono音声を示す。

この仕様により、表示波形とリップ解析結果の対応を優先する。

### 6.4 一時ファイル扱い

解析用WAVは内部処理用の一時ファイルとして扱う。

方針:

* ユーザーに直接案内しない
* MMDに読み込ませる出力ファイルとして扱わない
* 処理完了後または失敗後に削除してよい
* 保存する場合でも内部キャッシュとして扱う
* onefileの一時展開先を永続保存先として扱わない

---

## 7. MMD用WAV出力仕様

### 7.1 目的

MMD用WAVは、ユーザーがMMDに読み込ませるための音声ファイルである。

mp3 / m4a / MMD非互換WAVを入力した場合でも、MMD側で読み込みやすいWAVを専用導線から出力することを目的とする。

### 7.2 固定仕様

MMD用WAVは以下を基本仕様とする。

```text
RIFF / WAVE
fmt chunk size 16
audio format 1 = PCM
PCM signed 16-bit little-endian
44100 Hz
channels: 2
data chunk あり
```

### 7.3 chunk方針

MMD用WAVでは、MMD互換性を優先し、余分なchunkを原則含めない。

原則として含めないchunk:

```text
JUNK
bext
iXML
fact
cue
smpl
acid
cart
その他metadata系chunk
```

`LIST` chunk も、MMD互換性を優先する場合は含めない方針とする。

MS17-B7実装では、`LIST` chunk を含むFFmpeg出力をMMD用WAV検証失敗として扱い、`-bitexact` を使って `LIST` chunk を出さない方針を採用した。

### 7.4 chunk順序

MMD用WAVでは、可能な限り単純なchunk順序を目標とする。

推奨構造:

```text
RIFF
WAVE
fmt
data
```

少なくとも、`fmt` chunk より前に `JUNK` / `bext` / `iXML` 等の追加chunkを置かない。

### 7.5 非対応WAV形式

MMD用WAVとして以下は出力しない。

```text
WAVE_FORMAT_EXTENSIBLE
float WAV
24bit WAV
32bit WAV
96kHz WAV
3ch以上の多チャンネルWAV
metadata chunk付き高機能WAV
```

---

## 8. 音声時間軸の保持

### 8.1 基本方針

入力音声、解析用WAV、MMD用WAVの時間軸は可能な限り一致させる。

VMDは音声時間軸に基づいて生成されるため、音声長や開始位置が変わると、MMD上でVMDと音声がずれる。

### 8.2 禁止事項

以下は禁止する。

```text
先頭無音の自動トリム
末尾無音の自動トリム
自動フェードイン
自動フェードアウト
自動無音追加
自動テンポ変更
自動速度変更
```

無音部分は、ユーザーが意図して入れている可能性があるため、勝手に削除しない。

### 8.3 長さ保持

解析用WAVとMMD用WAVは、入力音声と同じ開始位置・同じ長さを維持することを基本とする。

ただし、エンコード形式やコンテナ仕様により、ごく小さなduration差が発生する可能性はある。

この場合は、許容差を定義して検証する。

初期仕様では以下を目安とする。

```text
解析用WAVとMMD用WAVのduration差:
0.05秒以内を許容
```

より厳密に扱う必要がある場合は、1 frame相当である約0.033秒を基準に再検討する。

---

## 9. FFmpeg / ffprobe 利用方針

### 9.1 基本方針

FFmpeg / ffprobe は、入力音声の読み取り、メタ情報取得、WAV変換に使用する。

ただし、任意コマンド実行導線として扱ってはならない。

### 9.2 ffprobe

ffprobeでは、少なくとも以下を確認する。

* 音声ストリームが存在する
* duration
* sample rate
* channel count
* codec
* bit depth または sample format
* ファイルが読み取れるか

音声ストリームが存在しない場合はエラーとする。

### 9.3 音声ストリームのみ使用

本ツールでは音声ストリームのみを扱う。

以下は使用しない。

* 動画ストリーム
* カバー画像
* subtitle stream
* attachment stream
* chapter
* metadata tag

mp3 / m4a に埋め込まれたカバー画像やタグ情報は無視する。

MMD用WAVへmetadataを引き継がない。

### 9.4 FFmpeg呼び出しの安全条件

FFmpegを呼び出す場合は以下を守る。

* 引数配列で呼び出す
* `shell=True` を前提にしない
* ユーザー入力をシェル文字列へ連結しない
* タイムアウトを設定する
* exit code を確認する
* 変換後ファイルを検証する
* 失敗時に不完全ファイルを削除する
* Python例外種別またはエラーメッセージを確認可能にする

---

## 10. 変換後検証

### 10.1 基本方針

FFmpegが成功終了しても、変換結果が本ツール仕様に適合しているとは限らない。

解析用WAVとMMD用WAVは、それぞれ変換後に検証する。

### 10.2 解析用WAV検証

解析用WAVでは以下を確認する。

* ファイルが存在する
* ファイルサイズが0ではない
* RIFFで始まる
* WAVEである
* `fmt` chunk が存在する
* `audio format = 1` PCM
* 16bit
* 44100 Hz
* mono
* `data` chunk が存在する
* `data` size が0ではない

### 10.3 MMD用WAV検証

MMD用WAVでは以下を確認する。

* ファイルが存在する
* ファイルサイズが0ではない
* RIFFで始まる
* WAVEである
* 最初の有効chunkが `fmt` である
* `fmt` chunk size が 16
* `audio format = 1` PCM
* 16bit
* 44100 Hz
* channel count が 2（stereo固定）
* `data` chunk が存在する
* `data` size が0ではない
* `fmt` chunk より前に `JUNK` / `bext` / `iXML` 等が存在しない
* WAVE_FORMAT_EXTENSIBLE ではない
* `fact` chunk が必須になる形式ではない

### 10.4 最初のchunkチェック

MMD用WAVでは、`RIFF` / `WAVE` の直後に来る最初の有効chunkを確認する。

原則として、最初の有効chunkは `fmt` とする。

以下のような構造はMMD非互換の可能性があるため、MMD用WAVとしては不合格とする。

```text
RIFF
WAVE
JUNK
fmt
data
```

推奨構造:

```text
RIFF
WAVE
fmt
data
```

---

## 11. エラー分類

音声入力・変換・出力では、以下のエラー分類を使用する。

| 分類 | 意味 |
| --------------------------- | -------------- |
| `input_file_not_found` | 入力ファイルが存在しない |
| `audio_file_not_found` | 音声ファイルが存在しない |
| `audio_path_is_directory` | フォルダが指定されている |
| `audio_file_too_large` | 入力ファイルサイズ上限超過 |
| `unsupported_audio_extension` | 対応外拡張子 |
| `ffprobe_not_found` | ffprobeが見つからない |
| `ffprobe_permission_error` | ffprobe実行権限不足 |
| `ffprobe_timeout` | ffprobe実行タイムアウト |
| `ffprobe_execution_failed` | ffprobe実行失敗 |
| `ffprobe_invalid_json` | ffprobe結果(JSON)不正 |
| `audio_stream_not_found` | 音声ストリームが存在しない |
| `audio_duration_missing` | 音声長が取得できない |
| `audio_duration_too_long` | 音声長上限超過 |
| `ffmpeg_not_found` | FFmpegが見つからない |
| `ffmpeg_timeout` | FFmpeg処理タイムアウト |
| `ffmpeg_execution_failed` | FFmpeg変換失敗 |
| `analysis_wav_generation_failed` | 解析用WAV生成失敗 |
| `analysis_wav_output_failed` | 解析用WAV出力失敗 |
| `mmd_wav_validation_failed` | MMD用WAV検証失敗 |
| `output_permission_denied` | 出力先への書き込み権限がない |

### 11.1 エラー表示

エラー時は、利用者向けメッセージと詳細情報を分ける。

最低限、詳細情報として以下を確認可能にする。

```text
エラー分類
処理フェーズ
Python例外種別
エラーメッセージ
対象ファイル
```

---

## 12. GUIとの関係

### 12.1 波形表示

波形表示は解析用WAVを正本とする。

したがって、stereo入力や3ch以上入力でも、表示される波形は解析用mono mix後の波形である。

### 12.2 Preview

Previewは、解析用WAVから生成された timing plan を基準に表示する。

MMD用WAVがstereoの場合でも、Previewは解析用mono音声に基づく。

### 12.3 ユーザーへの説明

stereo入力時は、必要に応じて以下の説明を表示してよい。

```text
解析と波形表示には、左右チャンネルをミックスしたmono音声を使用します。
MMD用WAVはstereoで出力されます。
```

3ch以上入力時は、必要に応じて以下の説明を表示してよい。

```text
3チャンネル以上の音声は、ch1/ch2のみを使用します。ch3以降は解析・MMD用出力の対象外です。
```

---

## 13. 出力時の上書きと失敗処理

### 13.1 内部一時ファイル

解析用WAVなどの内部一時ファイルは、自動上書きしてよい。

ただし、失敗時には可能な限り削除する。

### 13.2 MMD用WAV

MMD用WAVはユーザー向け出力である。

同名ファイルが存在する場合は上書き確認を行う。

黙って上書きしてはならない。

### 13.3 不完全ファイル

変換途中または出力途中で失敗した場合、不完全なファイルを可能な限り削除する。

失敗したファイルを成功扱いしない。

---

## 14. MS17実装時の受け入れ条件

MS17で音声入力拡張を実装する場合、以下を受け入れ条件とする。

### 14.1 入力

* `.wav` を受け付ける
* `.mp3` を受け付ける
* `.m4a` を受け付ける
* `.ogg` / `.aiff` / `.flac` は初期対象外
* 500MB超のファイルを拒否する
* 15分超の音声を拒否する
* 音声ストリームがないファイルを拒否する

### 14.2 解析用WAV

* 16bit / 44.1kHz / mono に変換される
* stereo入力はch1/ch2からmono mixされる
* 3ch以上入力はch1/ch2のみ使われる
* ch3以降は解析対象外
* 波形表示は解析用WAVを使う

### 14.3 MMD用WAV

* 16bit / 44.1kHz / PCMで出力される
* mono入力もstereoで出力される
* stereo入力はstereoで出力される
* 3ch以上入力はch1/ch2のみのstereoで出力される
* 余分なchunkが含まれない
* 最初の有効chunkが `fmt` である
* WAVE_FORMAT_EXTENSIBLEではない
* data chunk が存在する
* MMDで読み込みやすい単純構造である
* MS17-B7実装では、FFmpeg出力に `-bitexact` を指定して `LIST` chunk 混入を避ける

### 14.4 音声加工

* 音量正規化を行わない
* 無音トリムを行わない
* 自動フェードを行わない
* metadataを引き継がない
* カバー画像を引き継がない

### 14.5 エラー

* 提案済みエラー分類に従う
* Python例外種別またはエラーメッセージを確認できる
* 失敗時にBusy状態が解除される
* 不完全ファイルが可能な限り削除される

---

## 15. 変更履歴

### 2026-05-01 / 初版

* MS17以降の音声入力拡張に向けて、音声入力・解析用WAV・MMD用WAVの仕様を分離して定義。
* 入力対応形式を `.wav` / `.mp3` / `.m4a` とし、`.ogg` / `.aiff` / `.flac` は初期対象外とした。
* 解析用WAVを 16bit / 44.1kHz / mono 固定とした。
* MMD用WAVを 16bit / 44.1kHz / stereo の単純PCM WAVとした。
* stereo入力は解析時にmono mix、MMD用WAVではstereo出力とした。
* 3ch以上入力は ch1/ch2 のみを使用し、ch3以降は破棄または無視する方針を定義。
* 音量正規化、無音トリム、自動フェードを行わない方針を明記。
* 入力ファイルサイズ上限を500MBとした。
* 解析用WAVのフォーマット、ヘッダ、最初のchunk検証を必須化。
* 音声ストリームのみを扱い、metadataやカバー画像を引き継がない方針を定義。
* 音声系エラー分類を定義。
