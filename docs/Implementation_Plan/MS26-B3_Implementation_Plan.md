# MS26-B3 Implementation Plan

## 1. 文書情報

- 対象: MS26-B3 Windows 11実機・実MMD受入
- 作成日: 2026-09-10
- 基準: `feature/MS26-implementation` / `46a3f32`
- 計画策定時の作業ツリー: クリーン
- 正本: [MS26 Block Breakdown](MS26_Block_Breakdown.md) MS26-B3
- 実MMD操作: ユーザー担当
- 状態: **B3受入完了（2026-09-12、ユーザー報告）**。2026-09-11〜09-12に、手動GUI、AC03 / AC04、MMD Ver 9.32、使用model path、入力 / 出力音声path、日本語・ラテン、4主要ケース、実MMD上の音声・モーフ同期、GUI再生、voice-only編集・再解析、状態・保存可否、delivery保護・復旧、Whisper未配置・no-download、profile / preset適用と復帰が問題なしと確認された（いずれもCodex実施ではない）。一組の生成artifactはread-only確認済み。ユーザー報告をB3受入証拠として採用し、PMX hashの独立取得不可と詳細ログ・画面記録の未添付は制限として記録する。MS26 CloseOut AはB4計画へ記録済み。
- 本計画は、ユーザーとの素材確認後に提示した計画を保存したもの。計画保存はGUI・実MMD操作、コード変更、stage / commit / pushの許可ではない。

## 2. 背景

B2では自動横断回帰と実FFmpegによるWAV検証を完了している。ただし、自動テストはMMDでの読み込み、音声再生、口モーフの対応、リップ同期、見た目の合格を証明しない。

B3では、それらを現在の入力素材・モデル・生成設定に対応付けて確認する。

## 3. 目的

- TEXTあり / voice-onlyの主要GUI導線を確認する。
- 日本語・英字の母音名で生成したVMDを実MMDで確認する。
- 個別保存と一括出力、キャンセル・失敗後の復旧を確認する。
- 自動検証、ユーザーの観測、未検証事項を分離して記録する。

## 4. In Scope

- 実行環境・素材・設定・出力の識別情報の記録。
- 現行開発環境からのGUI起動と手動確認。
- 指定音声・TEXT、既存Whisper `small`、既存preset / profileの利用。
- 実MMDでのVMD・WAV読み込みと再生確認。
- B1 evidence ledgerへの結果記録、B3関連文書の状態同期。
- 発見した問題の分類とB4への引き継ぎ。

## 5. Out of Scope

- production code・テストの追加や修正。
- PMXの編集、存在しないモーフ名の置換。
- runtime JSON / INIの直接編集・コピー。
- モデルのダウンロード、依存更新、ネットワーク処理。
- PyInstallerビルド、MS26 Closeout、MS27。
- stage / commit / push等のGit変更。

## 6. 前提条件・使用素材

使用するファイルは次のとおり。すべて実在を確認し、ユーザーが使用を承認した。

```text
MMD:
D:\Visual Works\MMD Folder\MikuMikuDance64\MikuMikuDance.exe

PMX:
D:\Visual Works\MMD Folder\MikuMikuDance64\UserFile\Model\Kanna\Mobco_V4B\Mobco_v2_2024B3_edit2.pmx

音声:
D:\Visual Works\Kanna Work\Voice\MMD_AutoLipTool説明1_mmd.wav

TEXT:
D:\Visual Works\Kanna Work\Voice\MMD_AutoLipTool説明1.txt
```

確認済み事項:

- 音声: 40.458639秒、`pcm_s16le`、44100Hz、2ch。
- TEXT: UTF-8で読み取り可能。
- `models/small.pt`: 483,617,219 bytes。SHA-256が現行manifestと一致。
- OS取得値: `DisplayVersion=25H2`、build `26200.9445`。
- MMD実行ファイル・PMX・音声・TEXTのSHA-256を取得済み。

計画策定時のSHA-256は以下。B3開始時には再取得し、差があればこの記録を黙って上書きせず、新しい検証対象として記録する。

| 対象 | SHA-256 |
| --- | --- |
| MMD実行ファイル | `07516FD3BF1E6B1339836B6773A156F61BDD6F848EEB621FDDA012375DF313A1` |
| PMX | `9CF5B61F3F63735F73259044BF324D10958AED02AAF2ABA5C8CDF6F33661D423` |
| 音声 | `3CB803D89D475087D955BE1E484AA0D0C7E95F96585284DC8A45EAC0219227D0` |
| TEXT | `B741D7271E1AC24FB3B3B82791AE12BC6D98ED49046DE7E008B222B06CCAE086` |
| `models/small.pt` | `9ECF779972D90BA49C06D968637D720DD632C55BBF19D441FB42BF17A411E794` |

実行開始時に確認する事項:

- Windowsの表示情報。取得コマンドの一部は製品名を「Windows 10 Pro」と返したため、これだけでOS名を確定しない。
- MMD画面のバージョン。実行ファイルのversion resourceは空だった。
- 指定PMXの実際の口モーフ名。日本語・英字双方があることはユーザー確認済みだが、Codexでは未検証。
- GUI・MMD操作を行った実施者と日時。

不足が判明した場合、該当ケースを未検証として止め、別素材への変更はユーザー判断を求める。

## 7. 対象ファイル

| 区分 | 対象 |
| --- | --- |
| 実行入口 | `src/main.py` |
| GUI・状態の照合 | `src/gui_wx/app_controller.py`、`main_frame.py`、`right_pane.py`、`ui_state.py`、`analysis_worker.py` |
| 設定・モデルの照合 | `src/core/model_profile_state.py`、`model_profiles.py`、`morph_name_sets.py`、`generation_presets.py`、`whisper_models.json`、`whisper_model_store.py`、`whisper_model_runtime.py` |
| 出力契約の照合 | `src/core/delivery_package.py`、`mmd_wav_export.py` |
| 読み取り対象 | `profiles.json`、`presets.json`、`MMD_AutoLipTool.ini` |
| B3実施時の記録先 | [B1計画](MS26-B1_Implementation_Plan.md) §16、本計画、[Block Breakdown](MS26_Block_Breakdown.md)、[MS20 Index](../MS20_and_Beyond_Index.md) |

コードは変更しない。設定の選択・適用は既存GUIを通じて行う。

## 8. 実装方針

既存設定から次を推奨する。

| 用途 | profile | preset |
| --- | --- | --- |
| 日本語母音の基準 | プロファイルなし | 標準（長音維持） |
| 英字母音の基準 | 既存「ラテン語」 | 標準（長音維持）を明示適用 |
| 長音減衰の追加確認 | 日本語側 | 長音減衰 |
| ユーザープリセット確認 | 日本語側 | 既存 `PresetTest1` |

- 日本語側は「あ / い / う / え / お」、英字側は「A / I / U / E / O」。
- 上限値は両側で0.82に揃える。日本語側（プロファイルなし）は各ケースの解析前にGUIで0.82を明示設定し、英字側は「ラテン語」適用後の解決値が0.82であることを確認して記録する。
- 「ラテン語」の既定presetは長音減衰なので、基準確認ではprofile適用後に標準presetを適用する。
- 日本語側の「プロファイルなし」を、日本語専用profileの適用確認と同一視しない。今回はprofileを新設しない。
- `PresetTest1` は開口維持2、閉口スムーズ3、長音減衰という現在値を使用し、変更しない。

出力先は、実行時に未使用であることを確認した次の専用フォルダーとする。

```text
D:\Codex\MS26-B3\<実施日時>\
```

ケースごとに別フォルダーを使い、元音声や既存成果物を上書きしない。

## 9. 詳細ステップ

### B3-01: 環境・素材の確定

HEAD、既存差分、OS、MMD表示バージョン、素材hash、モーフ名をB1 ledgerへ記録する。MMD上の英語表示名と、VMDが参照する実モーフ名を取り違えないよう確認する。

実MMD操作はユーザーが行う。GUI操作の担当も開始前に明示し、Codexによる操作手段が利用できなければユーザーに操作を依頼する。未実行の操作をCodex実績としない。B3 material / environment gate未充足の間は、該当素材での受入を開始しない。

Whisper保存先の解決済みpath、selected / active model、profile / presetのIDと表示名、上限値、生成設定を開始時記録へ残す。「ラテン語」は `ceb35f25-587a-43c9-9eed-f7789c54d857`、`PresetTest1` は `55549e81-0b7f-466e-aae5-7f859929e84d`。IDが存在しない、または内容が計画と違う場合は同名で代替せず再確認する。組み込み標準は `builtin:standard-hold`、長音減衰は `builtin:long-vowel-decay` を使用する。

### B3-02: GUI起動・Whisper設定

既存`.venv`から起動する。

```powershell
.\.venv\Scripts\python.exe .\src\main.py
```

保存設定は計画策定時点で「選択中=medium、適用済み=small」。入力を読み込む前にavailability scanの完了を待ち、検証済みの`small`を選択する。active modelとmanifestが既に同じなら再適用は不要であり、適用ボタンの無効化やno-opを失敗としない。異なる場合だけ既存GUIから適用する。選択・適用・ロード・解析使用モデルを区別し、解析成功後には使用モデルが`small`で同じmanifestであることを確認する。起動直後に未ロードでも異常扱いしない。ダウンロードは実行しない。

### B3-03: 主要導線

次の4ケースを確認する。

| ケースID | 入力 | 出力母音 | profile | preset | voice-only編集 | B3-06で使う一括出力 |
| --- | --- | --- | --- | --- | --- | --- |
| B3-T-JP | TEXT＋指定音声 | 日本語 | プロファイルなし | `builtin:standard-hold` | N/A | 基準設定で確定した一括出力 |
| B3-T-LA | TEXT＋指定音声 | 英字 | 既存「ラテン語」 | profile適用後に`builtin:standard-hold`を明示適用 | N/A | 基準設定で確定した一括出力 |
| B3-V-JP | 指定音声のみ | 日本語 | プロファイルなし | `builtin:standard-hold` | `B3-V-EDIT`を必須実施 | 編集適用・再解析後、基準設定で確定した一括出力 |
| B3-V-LA | 指定音声のみ | 英字 | 既存「ラテン語」 | profile適用後に`builtin:standard-hold`を明示適用 | なし | 基準設定で確定した一括出力 |

主要4ケースは、表のprofile / presetを明示適用してから解析し、各ケースの上限値は日本語側では解析前にGUIで0.82を明示設定し、英字側ではprofile適用後の解決値0.82を確認して記録する。ケースごとに別の未使用出力先へ一括出力する。そのdirectoryをB3-06の正本としてpath・size・SHA-256と設定を記録する。`B3-V-JP`だけは`B3-V-EDIT`の編集適用・再解析が成功した後の一括出力を正本とする。B3-04の追加設定ケースは別directoryへ出力し、この4つの正本を上書き・置換しない。

TEXT群からvoice-only群へ進む前に、処理終了を待って `ファイル > 新規作業...` を実行する。TEXTのpathと内容が空であることを確認してから、指定音声だけを読み込む。診断・レポート等の入力modeが`voice_only`であることを確認し、TEXTが残ったままの解析をvoice-onlyの証拠にしない。新規作業ではprofile / presetが保持されるため、ケースごとに上表の設定を明示適用する。

各ケースで解析、波形、Preview、再生、診断、個別保存、一括出力を確認する。個別保存はVMD、MMD用WAV、診断reportの3操作を別々に行い、各path・size・SHA-256を記録する。一括出力の3成果物とは区別し、個別保存の成功を一括出力の成功へ転用しない。

GUI再生は `B3-G-PLAYBACK` として各入力modeで少なくとも1回確認する。再生開始後に再生位置とPreview上の現在位置が進むこと、停止操作で再生が止まり位置が先頭へ戻ることを記録する。MMD上の再生確認とは別の証拠にする。

Info / Warning / ERRORと保存可否は `B3-G-STATE` として、正常解析、`B3-V-EDIT`の再解析待ち、`B3-W-MISSING`のモデル利用不可、復旧後の各状態で確認する。VMD、診断report、一括出力の有効・無効を別々に記録し、正常時にERRORがないことと、失敗時に期待したERRORが表示されることを区別する。

同じ入力mode・同じ有効解析結果を設定変更後も利用できる場合だけ、不要な再解析を省略する。入力mode変更や書き起こし編集後の必要な再解析は省略しない。

voice-onlyの編集・再解析は `B3-V-EDIT` として`B3-V-JP`で必須とする。元の書き起こしを証拠として保持し、実際の音声に即した修正をGUIへ適用する。修正不要なら実際の句読点等の変更を用い、変更が受理されたことを確認する。適用後・再解析前はVMDと一括出力が不可であること、診断レポートが保存可能であること、再解析成功後に保存可へ戻ることを確認する。編集内容、結果、再解析後の出力を区別して記録する。元のTEXTファイルは編集しない。変更を受理させられなかった場合は未検証とし、この必須ケースを無言で省略しない。

### B3-04: 設定変更

- presetは選択だけでは適用されないこと。
- 「長音減衰」「PresetTest1」の適用結果がPreview・診断・出力へ反映されること。
- profile適用中の直接設定変更ロックと、profile解除後の状態。
- 長音の見た目は、実際に長音イベントがある箇所で確認する。該当イベントがなければ未検証とし、素材を黙って書き換えない。

追加設定は次のサブケースとして、主要4ケースとは別に実施する。

| サブケースID | 利用する有効解析結果 | profile / preset | 確認範囲 | B3-06での扱い |
| --- | --- | --- | --- | --- |
| `B3-S-DECAY` | `B3-T-JP` | プロファイルなし / `builtin:long-vowel-decay` | Preview・診断・別directoryへの一括出力 | 主要4ケースの実MMD正本には使用しない |
| `B3-S-PRESET1` | `B3-T-JP` | プロファイルなし / `PresetTest1`（ID `55549e81-0b7f-466e-aae5-7f859929e84d`） | Preview・診断・別directoryへの一括出力 | 主要4ケースの実MMD正本には使用しない |

各サブケースは適用前後の設定identity、生成状態、出力directoryを記録する。既存の有効解析結果を再利用できない状態になった場合は必要な再解析を行い、主要4ケースの正本directoryを上書きしない。

### B3-05: 保護・復旧

一括出力を開始した各ケースでは、既存GUI・ログ・ファイルシステムで観測できた範囲として、terminalの`primary_status`相当（success / cancelled / failed）、表示されたerror、`committed`相当、確定directoryのpathまたは不存在、owned stagingの残留有無、`cleanup_status`相当を記録する。内部の`DeliveryTerminalResult`値が既存表示から確認できない項目は`unobserved`とし、推測値で埋めない。開始前とterminal後に専用出力親directoryのentryを比較し、`.MMD_AutoLipTool.delivery-*.staging`に一致する当該試行由来のdirectoryが残っていないか確認する。opaqueなstaging directoryの生pathは証拠へ転記せず、親directoryと残留有無だけを記録する。

`cleanup_status`が`completed`または`not_required`に相当し、owned stagingが残っていない場合だけcleanup合格とする。GUIに「一時出力cleanup警告」が出た場合、または専用出力親directoryにowned stagingが残った場合は、確定directoryがなくても`partial_output_cleanup_failed`相当のfindingとしてB4へ渡し、そのケースを合格にしない。残留物は確認して記録するだけとし、無断削除しない。

一括出力の保護・復旧は次のケースへ分ける。

- `B3-D-COLLISION`: 成功済み一括出力directoryと同名を指定し、開始前に拒否されること、既存3成果物のsize・SHA-256が変わらないことを確認する。
- `B3-D-CANCEL`: 未使用の出力先で一括出力を開始してキャンセルする。terminal resultを受けるまでBusyが維持され、既存出力を壊さず、不完全な確定directoryもowned stagingも残さず、cleanup警告がなく、終了後に別の未使用出力先へ再試行できることを確認する。確定処理が先に完了した場合はキャンセル成功とせず、競合結果として記録する。cleanup警告またはowned staging残留があればキャンセル成功扱いにしない。
- `B3-D-FAIL`: GUIから安全に再現できる一括出力の失敗またはfail-closed拒否がある場合、その条件、ERROR、3種の保存可否、既存出力保護、再試行結果を記録する。collisionをworker実行後の失敗証拠に転用しない。権限変更、ファイルlock、障害注入等を追加せずに安全な失敗を再現できない場合は、実機のfailure recoveryを未検証とする。
- `B3-W-SELECT`: 未配置モデルの選択だけで暗黙downloadやactive model変更が起きないことを確認する。これは未配置時の解析拒否を確認した証拠とはしない。

キャンセル対象が早く完了して観測できなかった場合、キャンセル成功と記録しない。確認のために既存モデルや成果物を削除しない。

未配置時の適用・解析拒否は、正常系の成果物を確保した後に `B3-W-MISSING` として独立実施する。

1. 元の解決済みモデル保存先と開始時設定を記録する。専用出力先配下に、モデルを含まない新規の空フォルダー `empty_models` を用意する。既存`small.pt`は移動・削除しない。
2. Busy終了後、GUIの `保存先を変更` で空フォルダーへ切り替える。availability scanの完了と`small`未配置を確認する。切替が拒否・失敗した場合は解析を進めず、結果を記録する。
3. 未配置`small`の適用が無効または拒否されることを確認する。「新規作業」から音声のみを読み込み、解析開始が無効またはモデル利用不可で安全に失敗すること、古い結果を新しい成功結果として保存できないことを確認する。両方の拒否を観測し、disabledと実行後失敗を区別する。
4. `Download & Verify`は押さない。操作前後の空フォルダー内容、GUI表示、ログ、保存可否を証拠として残す。これだけで音声の外部送信・background通信なしを証明したとはしない。
5. 通信の確認は、実行時に利用できる既存の読み取り専用監視手段で、対象アプリ・子プロセス、観測時間、接続／送信の記録と限界を残す。新規ツール導入やネットワーク設定変更はしない。監視できない場合、外部送信・通信の観測は未検証として残し、B2の自動証拠やGUI表示だけで実機passにしない。
6. 成功・失敗を問わず、GUIから元の保存先へ戻して再scanし、`small`の検証済み状態を確認する。同一active / manifestなら再適用を強制せず、必要時のみ適用する。正常解析を再試行し、ロード・解析identityと保存復帰を確認する。復帰できなければ後続の正常系を止めて報告する。

保存先の復帰は解決済みpathと動作の復帰を意味する。GUI操作によってINIの空指定が明示pathへ変わる等の差は記録し、直接編集でbyte単位の復元をしない。終了時には開始時のprofile / preset / 生成設定・選択候補もGUIで復帰可能な範囲を戻し、残った差を報告する。検証用フォルダーや成果物は無断削除しない。

`B3-D-CLOSE`は、未配置モデルからの復帰、開始時設定への復帰、上記の再試行確認を終えた後、GUI確認の最後に実施する。正常な解析状態と未使用の出力先で一括出力を開始し、処理中にメインwindowを閉じて終了確認を受け入れる。workerのterminal resultまではwindowが閉じず、terminal後にアプリが終了することを確認する。結果は「3成果物すべてが確定」または「確定directoryなし」のどちらかであり、不完全な確定directoryとowned stagingがなく、cleanup警告がないことを確認する。cleanup警告またはowned staging残留があればclose lifecycleを合格にせず、B4へfindingとして渡す。処理がclose要求より先に完了した場合はclose lifecycleの成功証拠にせず、観測不能として記録する。終了後のファイル確認は行うが、成果物や検証用directoryは削除しない。

### B3-06: 実MMD確認

ユーザーは各ケースで確定した一括出力directory内のVMDとMMD用WAVを、必ず同じ組として読み込む。個別保存の成果物は別フォルダーへ保存し、実MMD受入の入力に代用しない。一括出力のVMD / WAV / reportの実path・size・SHA-256、入力mode、profile / preset、生成状態を記録してから渡し、読み込み時の組み合わせをユーザー報告と照合する。前ケースのモーションが混在しない新規状態で、開始フレームを揃えて確認する。

判定は次を分ける。

1. VMD読み込み
2. WAV読み込み
3. 音声再生
4. 対象モーフの動作
5. 発話の開始・中盤・終端での同期
6. 閉口・開口・長音の見た目

気になる箇所は時刻またはフレームと現象を記録する。手動で位置を補正してから、未補正の結果を合格にしない。

### B3-07: 記録・引き継ぎ

各ケースの実施者、入力、設定、出力path、観測結果、問題、未検証範囲をB1 ledgerへ記録する。コード補修とMS26全体のCloseoutはB4へ引き継ぐ。

ledgerの既存13列を維持し、GUI、実MMD、未配置・復旧、設定変更には別の一意evidence IDを割り当てる。ケースIDは§9のものを参照し、各試行の日時・HEAD / tree identity・実施者・期待結果・実結果・pass / fail / 未検証・証拠所在を対応付ける。再試行で前の失敗を消さない。`MS26-B3-001`は素材・環境gate、`MS26-B3-002`は手動確認の集約行とし、詳細行を参照させる。

## 10. 状態遷移 / データ契約

- 素材・環境確定 → GUI確認 → 実MMD確認 → 証拠照合。
- 入力音声、内部分析WAV、出力MMD用WAVを分離する。
- MMD用WAVはPCM 16-bit / 44100Hz / ステレオを維持する。
- VMD・診断・レポートは同じ有効な生成状態に対応させる。
- B2の「duration差0.05秒以内」は自動回帰条件であり、実MMDの視覚的同期の合格基準へ流用しない。

## 11. テスト方針

B3の必須証拠は、指定素材によるGUI・実MMDの手動結果。

コード・テストが不変なら、成功済みB2全件テストを念のために再実行しない。問題を発見した場合は証拠を保存し、補修後の関連回帰と手動再確認をB4で定める。

B2で観測したWhisper補助スレッドの例外見出しは、B3起動・終了時にも観測対象とする。再現時はログと条件を残し、原因を推測で確定しない。

## 12. 受け入れ条件

- 4主要ケースについて、入力・設定・出力・実MMD結果が追跡可能。
- 日本語・英字それぞれの実モーフ対応が確認できる。
- 読み込み・再生・同期・見た目を別々に判定できる。
- 個別保存、一括出力、collision保護、復旧の結果が記録される。
- 未実施や観測不能を成功へ置き換えない。
- ユーザー報告とCodexによる確認を区別する。
- `B3-G-PLAYBACK`、`B3-G-STATE`、`B3-V-EDIT`、`B3-D-COLLISION`、`B3-D-CANCEL`、`B3-D-FAIL`、`B3-D-CLOSE`、`B3-W-SELECT`、`B3-W-MISSING`と復帰、設定変更について、期待結果に対する実結果と未検証範囲がある。
- `B3-D-CANCEL`、`B3-D-FAIL`、`B3-D-CLOSE`ではterminal観測欄、cleanup警告、確定directory、owned staging残留の有無が記録され、`partial_output_cleanup_failed`相当を合格にしていない。
- 実MMDの4主要ケースは、それぞれの一括出力由来のVMD / WAVで確認されている。

欠落・未検証・期待結果不一致がある場合、B3を全面合格とせず、部分確認と残課題を明示する。手動確認を実施してfindingをB4へ渡せることと、B3受入が全面合格であることを分ける。日本語専用profile適用は今回の検証対象外であり、プロファイルなしの日本語出力の合格をその証拠にしない。

## 13. リスクと対策

- モデルのモーフ名不一致: 実行前にMMD上で確認し、素材を無断改変しない。
- Whisperの選択・適用状態の差: `small`の各identityを記録する。
- 元音声が既にMMD用WAV: 今回指定された入力として扱い、B3でMP3 / M4A入力も確認したとは主張しない。
- 既存設定への影響: 開始時の値を記録し、復帰もGUI経由で行う。JSON / INIを直接復元しない。
- 短い処理でキャンセルを観測できない: 未検証として残し、人工的な障害注入へ勝手に拡張しない。

## 14. 実行時の注意・終了点

### 14.1 手動GUI確認記録（2026-09-11）

- 実施者: ユーザー
- 結果: 手動GUIテスト通過、問題なし（ユーザー報告）
- CodexによるGUI操作: 未実施
- 実MMDでのVMD / WAV読み込み・再生・morph・同期・見た目: 未実施・未検証
- 証拠所在: 本会話のユーザー報告。個別ログ・スクリーンショット・出力artifactの所在は未提示

### 14.2 手動テスト追加報告（2026-09-12）

- 実施者: ユーザー
- 結果: 手動テスト通過、問題なし（ユーザー報告）
- 本報告にはケース別の実施範囲、GUI / 実MMDの区別、操作ログ、スクリーンショット、出力artifactのpath・size・SHA-256は含まれていない。
- したがって、この報告は手動テストの結果報告として記録するが、B3-03〜B3-06の各ケース証拠、実MMDの個別判定、B3全面受入の根拠へは転用しない。

### 14.3 AC03 / AC04ユーザー確認記録（2026-09-12）

- 実施者: ユーザー
- 結果: AC03（B3 material / environment・GUI個別確認）およびAC04（主要4ケースの実MMD確認）をユーザー側でチェックし、問題なしとの報告を受領した。日本語・ラテン、`B3-T-JP`、`B3-T-LA`、`B3-V-JP`、`B3-V-LA`も確認済みと報告された。
- AC03 / AC04はユーザー報告として通過扱いとする。MMD Ver 9.32、使用model path、入力音声path、出力MMD用WAV pathは提示された。実PMX morph一覧、PMX hash、4ケースごとのVMD / WAV対応、操作ログ、スクリーンショットは未提示である。
- CodexによるGUI / 実MMD操作は未実施であり、ユーザー報告の範囲を越えて個別結果や再現性を補わない。

この計画はCodexによる実MMD操作の実施済み記録ではない。ユーザー報告はCodex実施結果と分け、AC03 / AC04の通過を記録しつつ、ケース別証拠の追跡可能性とB4 Closeout条件は未完了として扱う。

### 14.4 実MMDケース・生成物追加報告（2026-09-12）

- 実施者: ユーザー（実MMD）、Codex（外部生成物の読み取り専用確認）
- MMD: `Ver 9.32`
- Model: `D:\Visual Works\MMD Folder\MikuMikuDance64\UserFile\Model\Kanna\Mobco\_V4B\Mobco\_v2\_2024B3\_edit2.pmx`
- 入力音声: `D:\Visual Works\Kanna Work\Voice\MMD_AutoLipTool説明1.wav`
- 出力MMD用WAV: `D:\Visual Works\Kanna Work\Voice\MMD_AutoLipTool説明1B_MMD\MMD_AutoLipTool説明1_mmd.wav`
- ユーザー報告: 日本語・ラテンおよび`B3-T-JP`、`B3-T-LA`、`B3-V-JP`、`B3-V-LA`を確認し、問題なし。
- 外部生成物directory `D:\Visual Works\Kanna Work\Voice\MMD_AutoLipTool説明1B_MMD`にはVMD、MMD用WAV、diagnostic reportの3ファイルが存在した。MMD用WAVはPCM 16-bit / 44.1kHz / stereo、約40.459秒。VMDはVMD 0002、AutoLipTool、morph 681件、`あ / い / う / え / お`、frame 20〜1184を静的確認した。
- このartifact確認はファイル内容のread-backであり、実MMD操作の代替ではない。当時点では個別directory名・PMX hash / morph一覧・reportの`text_audio` / `Custom` / `decay`設定と各ケースの対応を未転記として残した。その後、ユーザーの実MMD上の音声・モーフ同期確認を含む受入報告を§14.6へ反映した。

### 14.5 追加手動確認報告（2026-09-12）

- 実施者: ユーザー
- 結果: 次の項目をすべて確認し、主な不具合は発見せず正常に作動したとの報告を受領した。`B3-G-PLAYBACK`、`B3-G-STATE`、`B3-V-EDIT`、`B3-D-COLLISION`、`B3-D-CANCEL`、`B3-D-FAIL`、`B3-D-CLOSE`、`B3-W-SELECT`、`B3-W-MISSING`、profile / presetの適用と復帰。
- 確認範囲にはGUI再生位置・停止、voice-only編集・再解析前後の保存可否、Info / Warning / ERROR、collision・cancel・failure recovery・close、未配置Whisper modelの安全停止、暗黙downloadなし、設定適用と復帰が含まれる。
- これはユーザー側の手動確認結果であり、CodexによるGUI操作・実MMD操作結果ではない。詳細操作ログ、画面記録、実施回数は本報告に含まれていないため、`MS26-B3-004`としてユーザー報告のPassを記録し、未提示の詳細を推測で補わない。

### 14.6 最終受入確認（2026-09-12）

- ユーザーは、実MMD上で音声と対象モーフの同期状態が良好であることを追加確認した。`B3-T-JP`、`B3-T-LA`、`B3-V-JP`、`B3-V-LA`、日本語・ラテンの確認結果、および追加GUI / recovery / Whisper gateのPass報告と合わせ、B3のAC03 / AC04をユーザー実施の受入結果として確定する。
- 受入証拠は、ユーザー報告、MMD / model / input / outputのpath、ケースID、Codexによる生成artifact一組のread-only確認で構成する。CodexはGUI / 実MMDを操作していないため、実操作の実施者はユーザーとして記録する。
- PMX pathは本環境から独立解決できずhash / morph一覧を取得していない。ユーザーの指定model pathと実MMD上のmorph同期確認を機能受入の根拠とし、未取得情報を推測で補わない。
- B3判定: **受入完了（user-reported pass）**。MS26全体のCloseOut AはB4の最終監査で判定する。
