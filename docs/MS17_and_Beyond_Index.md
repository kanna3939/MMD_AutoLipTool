# MS17 and Beyond Document Index

> [!WARNING]
> **Legacy / Historical Routing Index**
> 本書はMS17からMS19の履歴routing用である。MS20以降の現行routingは [MS20 and Beyond Index](MS20_and_Beyond_Index.md)、番号と計画は [MS20 and Beyond Roadmap](MS20_and_Beyond_Roadmap.md) を使用する。本書の旧MS番号と完了記録は置換しない。

> [!IMPORTANT]
> **AI Coding Assistant Directives (for Codex):**
> 1. **Do not read massive historical logs or legacy specifications unless explicitly requested.**
>    Avoid parsing `repo_milestone.md` (119KB) or `Version_Control.md` (179KB) fully, as it consumes huge amounts of context tokens.
> 2. **Always start by reading this index file** to understand the current milestone state, active document locations, and the minimal files you need to examine.
> 3. **Do not execute commands in parallel in this repository.**
>    Run exactly one command at a time, wait for its result, then decide the next command. This also applies to read-only commands such as `git status`, `rg`, and `Get-Content`.
> 4. Use targeted file reads with specific line ranges whenever possible.

---

## 1. 現在の開発ステータス概要 (MS17基点)

MS17 (音声入力・音声変換拡張マイルストーン) は **MS17-B9 closeout まで完了** しています。
MS18 (Release Readiness / Refactor / Security Hardening) は **CloseOut済み** です。
現在は、`main / origin/main` の `d876397 Close out MS18` を分岐元とする `feature/MS19` で、**MS19 (Voice-only Input)** を進行してきました。MS19-B1からMS19-B9まで完了し、B3からB9のユーザー確認対象も通過・問題なしです。B9では既存wxテストの終了処理access violationを補修して再発しないことを確認し、MS19 CloseoutをA判定としました。
`feature/MS17` は非正本の古いブランチとして扱います。

| ブロックID | ブロック名・テーマ | ステータス | 主な成果・対象ファイル |
| :--- | :--- | :--- | :--- |
| **MS17-B1** | Repo / MS16 closeout 後状態確認 | **完了** | MS16成果の整合性検証、開始条件の整理 |
| **MS17-B2** | FFmpeg/ffprobe 配布・ライセンス方針整理 | **完了** | `FFmpeg\bin\` 優先探索・外部導入両用ポリシーの確定 |
| **MS17-B3** | 音声入力拡張の前提基盤 | **完了** | 音声形式判別、timing plan/Preview無効化規則の維持 |
| **MS17-B4** | ffprobe検査・入力制限・エラー分類基盤 | **完了** | 500MB/15分上限、ffprobeラッパー、エラー区分 (`audio_errors.py`) |
| **MS17-B5** | 解析用WAV生成基盤 | **完了** | ffmpegによる正規化WAV (PCM 16bit, 44.1kHz) 一時ファイル生成 |
| **MS17-B6** | wav/mp3/m4a 入力導線統合 | **完了** | GUIファイルダイアログ拡張、波形表示・解析パイプライン統合 |
| **MS17-B7** | MMD用WAV出力基盤 | **完了** | 専用の「MMD用WAV出力」導線、stereo固定MMD用WAV生成、ch1/ch2選択、`-bitexact` による単純chunk出力、上書き確認、失敗時cleanup |
| **MS17-B8** | GUI状態・worker結果破棄統合 | **完了** | ffprobe/解析用WAV/MMD用WAV出力のworker化、Busy制御、キャンセル導線、300秒確認、late callback破棄、ユーザー手動テスト通過 |
| **MS17-B9** | 統合テスト・docs補正・MS17 closeout | **完了** | B3〜B8限定テスト確認、README / 配布用readme / pyproject / ライセンス・配布関連文書同期、実FFmpeg確認、実音声MMD用WAV生成確認、生成済みexeスモーク通過、ユーザー手動テスト通過、MS17 closeout記録 |

MS18 関連文書は、MS18 実施・CloseOut済みの記録です。
MS18-B1 / B2 / B3 は、実装変更を行わず、repo状態確認、Security Preflight、MS18-B4の実装範囲定義まで完了しています。
MS18-B4 は、FFmpeg / ffprobe探索元説明性改善、未検出時メッセージの小規模整理、解析用WAV再生エラー修正まで完了しています。
MS18-B5 は、`build.ps1 -SmokeLaunch` の停止待機・残留確認と `-Clean` 時の旧onefile成果物削除まで完了し、ユーザーテスト通過が報告されています。
MS18-B6 は、Release / Packaging / License Preflightまで完了しています。B6で記録したpackage化前P2は、2026-07-03のユーザー判断によりクリア扱いとしました。
MS18-B7 Actual MMD Manual Verification Closeout は、実MMDユーザー確認通過・問題なしとして完了しています。MS18全体のcloseout判定はAです。MS18はCloseOut済みです。

MS19 は、Voice-only Input として実装・CloseOutを完了しました。
MS19-B1 では、実装に入る前に TEXTあり / TEXTなしの状態契約を固定し、既存TEXTあり導線を壊さないことを前提に、音声のみ入力の入力正本・書き起こし結果・ひらがな・母音列・VMD保存契約を整理しました。
MS19-B2 では、既存 `whisper_timing.py` のraw result保持、書き起こし本文抽出候補、timing anchor契約、エラー分類、既存テスト不足を確認し、B3への引き継ぎを整理しました。
MS19-B3 では、Whisper raw resultから書き起こし本文を抽出し、既存 `build_vowel_timing_plan()` へTEXTファイルなしで接続するためのcore契約を追加しました。
MS19-B4 では、wxPython GUI上でTEXTなしでも音声のみ入力モードへ入り、既存の解析実行ボタンからvoice_only解析を開始できるようにしました。`AnalysisWorker` のvoice_only分岐、InfoPanelへの書き起こし本文・ひらがな・母音列の最小反映、TEXTなしVMD保存無効化、Whisper実行時のrepo-local `FFmpeg\bin` PATH補正まで完了し、ユーザー側音声のみ解析スモークテストも通過しています。
MS19-B5では、音声のみ解析で得た書き起こし結果の確認・編集、編集後のひらがな / 母音列preview更新、編集前timing planの誤用防止、保持済み `WhisperTimingResult` を使った編集済みテキスト再解析の最小導線を実装しました。ユーザー側のB5確認は通過・問題なしです。編集済み再解析で `current_timing_plan` を更新した場合、既存Previewの追従再描画はB5の許容範囲とし、Preview操作・VMD保存有効化はB6で扱います。
MS19-B6では、既存TEXTあり保存導線を維持しつつ、TEXT pathなしの音声のみ入力でも `current_timing_plan` からVMD保存できるようにしました。`generate_vmd_from_timing_plan()`、voice_only保存可否判定、保存分岐、ステータス文言更新、B4/B5由来テストのB6後期待値更新を実装し、対象自動スモーク36件とユーザー側B6確認は通過・問題なしです。編集適用直後の未再解析状態では引き続きVMD保存不可です。
MS19-B7では、音声のみ入力に固有の失敗条件、テスト実行状態、README / 配布用readme / 関連docs同期を扱う実装プランを作成済みです。B7では新機能追加ではなく、Whisper失敗、書き起こし空、読み変換失敗、母音列なし、編集済みテキスト空、VMD保存失敗の表示・状態復帰・テスト・docs整理を対象にします。
2026-07-10 にB7を実装し、voice_only解析エラー分類、解析失敗時のtiming plan無効化と編集済み書き起こし保持、VMD保存失敗時の解析結果保持、通常pytestのimport path安定化、旧MS14 fixture更新、README / 配布用readme / 関連仕様docs同期を完了しました。通常の `pytest tests` は360件すべてpass表示まで完走し、既存wx終了処理由来のprocess exit code 1のみ継続記録しています。同日にユーザー確認通過・問題なしと報告されました。
MS19-B8では、ファイルメニューの `新規作業... Ctrl+N` で現在のTEXT・音声・書き起こし・解析結果・表示・再生状態を初期化し、設定・履歴を保持したまま次素材へ移れるようにしました。確認キャンセル時の完全不変、Busy中無効、audio / analysis job IDによるlate callback破棄、source / output / cacheファイル非削除を実装・テストし、2026-07-11のユーザースモークテストも通過・問題なしです。MS19 CloseoutはB9で完了しました。
2026-07-12 にMS19-B9実装プランを作成し、2026-07-13 にB1からB9の成果、テスト、ユーザー確認、文書を再照合した。`test_wx_ms14_b6_closeout.py` の終了処理を補修したうえでMS19 CloseoutをA判定とした。

| ブロックID | ブロック名・テーマ | ステータス | 主な成果・対象ファイル |
| :--- | :--- | :--- | :--- |
| **MS18-B1** | Repo / Release Readiness / Risk Inventory | **完了** | `main / origin/main` 同期確認、MS17 closeout反映確認、`cache/`追跡対象外化確認、README / NOTICE / THIRD_PARTY_LICENSES.md / Release_Package_Manifest確認、P1/P2/P3 risk inventory、MS18-B2以降への引き継ぎ整理 |
| **MS18-B2** | Security Preflight Review | **完了** | 外部ファイル入力、ffprobe / ffmpeg、subprocess、temp / cache、GUI worker、PyInstaller onefile、release package、FFmpeg license notice を確認。Security P1なし。対象テスト42件通過。P2/P3をMS18-B3以降へ引き継ぎ |
| **MS18-B3** | Refactor Scope Definition | **完了** | B2のP2/P3を分類し、B4で扱う項目をPATH fallback説明性・診断ログ扱いの小規模改善候補に限定。SmokeLaunch / license / 実MMDはB5/B6/B7へ分離 |
| **MS18-B4** | Safe Refactor Implementation | **完了** | FFmpeg / ffprobe探索結果の説明補助、未検出時メッセージへの探索元説明反映、MCI向け解析用WAV再生パス補正、対象テスト20件通過、ユーザーテスト通過 |
| **MS18-B5** | SmokeLaunch / Process Residual Investigation | **完了** | `build.ps1 -SmokeLaunch` の停止後最大30秒待機、同一exeパス限定の残留検出・停止、`-Clean` 時の旧 `dist\MMD_AutoLipTool.exe` 明示削除、build / SmokeLaunch確認通過、ユーザーテスト通過 |
| **MS18-B6** | Release / Packaging / License Preflight | **完了** | 実行用ZIP同梱物・除外物、FFmpeg license notice、PyInstaller依存関係、`sample/` 同梱判断を確認。B6で記録したpackage化前P2は2026-07-03のユーザー判断によりクリア扱い |
| **MS18-B7** | Actual MMD Manual Verification Closeout | **完了** | 実MMDでのVMD / MMD用WAV読み込み・再生・リップ同期目視確認について、ユーザー確認通過・問題なしを記録。README / readme追加修正は不要と判断。MS18 closeoutはA判定。MS18 CloseOut済み |
| **MS19-B1** | Voice-only Input Requirements / State Contract | **完了** | TEXTあり / TEXTなし状態契約、音声のみ入力の入力正本、書き起こし結果・ひらがな・母音列保持方針、VMD保存時のTEXT path依存確認、B2への引き継ぎ整理 |
| **MS19-B2** | Transcription Pipeline Pre-check | **完了** | Whisper raw result保持、transcription本文抽出候補、timing anchor契約、エラー分類、既存テスト不足確認、B3への引き継ぎ整理、対象テスト21件通過 |
| **MS19-B3** | Textless Pipeline Integration Foundation | **完了** | Whisper raw resultからのtranscription本文抽出helper、既存Whisper timing結果を再利用する `build_vowel_timing_plan()` 拡張、core単体テスト追加、対象テスト27件通過、ユーザースモークテスト通過 |
| **MS19-B4** | GUI Entry Point and State Handling | **完了** | TEXTなし音声入力時の解析ボタン有効化、voice_only GUI状態、`AnalysisWorker` 分岐、InfoPanel最小反映、TEXTなしVMD保存無効化、Whisper実行時の `FFmpeg\bin` PATH補正、B4用GUI状態/workerテスト追加、ユーザー側スモーク通過 |
| **MS19-B5** | Review / Edit Transcription Result Flow | **完了** | 音声のみ解析結果の書き起こし編集UI、編集後preview更新、編集前timing plan誤用防止、保持済み `WhisperTimingResult` と明示的な worker 入力契約による編集済みテキスト再解析、B5用テスト追加、ユーザー側確認通過 |
| **MS19-B6** | VMD / Preview / Save Integration | **完了** | TEXT pathなし音声のみ入力のVMD保存有効化、`current_timing_plan` からのVMD保存入口、Preview追従確認、既存TEXTあり保存導線維持、対象自動スモーク36件通過、ユーザー側B6確認通過 |
| **MS19-B7** | Error Handling / Tests / Docs | **完了** | 音声のみ入力の失敗条件分類、状態復帰、VMD保存失敗時の結果保持、全360件pass表示、README / 配布用readme / 関連docs同期、ユーザー確認通過 |
| **MS19-B8** | Workspace Reset / New Session Flow | **完了** | `新規作業... Ctrl+N`、作業データ限定reset、設定・履歴保持、確認キャンセル、Busy制御、late callback破棄、B8専用8件pass、ユーザースモーク通過。MS19 CloseoutはB9で完了 |
| **MS19-B9** | MS19 Closeout | **完了（A）** | MS19固有33件、計画指定回帰62件、全体368件がpass表示。`test_wx_ms14_b6_closeout.py` の終了処理を補修し、ユーザーチェック通過・問題なし。 |

---

## 2. アクティブドキュメント・レジストリ

MS17以降の開発において、参照すべき「生きた仕様・計画」の一覧です。
**タスクの目的に応じて、以下のファイルのみをピンポイントで参照してください。**

| ドキュメント名とリンク | サイズ | 参照すべき目的・トリガー (いつ読むべきか) |
| :--- | :--- | :--- |
| [MS18_and_Beyond_Roadmap.md](file:///d:/Kanna_Works/MMD_AppWork/MMD_AutoLipTool-dev/MMD_AutoLipTool_Antigravity/docs/MS18_and_Beyond_Roadmap.md) | ~27KB | MS18以降のロードマップ正本候補。MS18〜MS20の順序、MS18の非新機能方針、MS19/MS20へ進む条件を確認するとき。 |
| [MS18_Block_Breakdown.md](file:///d:/Kanna_Works/MMD_AppWork/MMD_AutoLipTool-dev/MMD_AutoLipTool_Antigravity/docs/Implementation_Plan/MS18_Block_Breakdown.md) | ~29KB | MS18全体のブロック分解、In/Out of Scope、依存関係、closeout判定を確認するとき。 |
| [MS18-B1_Implementation_Plan.md](file:///d:/Kanna_Works/MMD_AppWork/MMD_AutoLipTool-dev/MMD_AutoLipTool_Antigravity/docs/Implementation_Plan/MS18-B1_Implementation_Plan.md) | ~24KB | MS18-B1のrepo状態確認、release readiness棚卸し、risk inventory手順を実施するとき。 |
| [MS18-B2_Implementation_Plan.md](file:///d:/Kanna_Works/MMD_AppWork/MMD_AutoLipTool-dev/MMD_AutoLipTool_Antigravity/docs/Implementation_Plan/MS18-B2_Implementation_Plan.md) | ~34KB | MS18-B2のSecurity Preflight Review、外部入力・subprocess・cache/temp・GUI worker・packaging/licenseリスク棚卸しを確認するとき。 |
| [MS18-B3_Implementation_Plan.md](file:///d:/Kanna_Works/MMD_AppWork/MMD_AutoLipTool-dev/MMD_AutoLipTool_Antigravity/docs/Implementation_Plan/MS18-B3_Implementation_Plan.md) | ~34KB | MS18-B3のRefactor Scope Definition、MS18-B4で変更してよい範囲・禁止範囲・テスト方針を確認するとき。 |
| [MS18-B4_Implementation_Plan.md](file:///d:/Kanna_Works/MMD_AppWork/MMD_AutoLipTool-dev/MMD_AutoLipTool_Antigravity/docs/Implementation_Plan/MS18-B4_Implementation_Plan.md) | ~20KB | MS18-B4のSafe Refactor Implementation、PATH fallback探索元説明性改善、診断ログ扱いの小規模整理、限定テスト方針を確認するとき。 |
| [MS18-B5_Implementation_Plan.md](file:///d:/Kanna_Works/MMD_AppWork/MMD_AutoLipTool-dev/MMD_AutoLipTool_Antigravity/docs/Implementation_Plan/MS18-B5_Implementation_Plan.md) | ~26KB | MS18-B5のSmokeLaunch / Process Residual Investigation、`build.ps1 -SmokeLaunch` の残留原因調査、最小修正または手順化判断を行うとき。 |
| [MS18-B6_Implementation_Plan.md](file:///d:/Kanna_Works/MMD_AppWork/MMD_AutoLipTool-dev/MMD_AutoLipTool_Antigravity/docs/Implementation_Plan/MS18-B6_Implementation_Plan.md) | ~27KB | MS18-B6のRelease / Packaging / License Preflight、実行用ZIP同梱物・除外物、FFmpeg license notice、PyInstaller依存関係、package化可否判定を確認するとき。 |
| [MS18-B7_Implementation_Plan.md](file:///d:/Kanna_Works/MMD_AppWork/MMD_AutoLipTool-dev/MMD_AutoLipTool_Antigravity/docs/Implementation_Plan/MS18-B7_Implementation_Plan.md) | ~26KB | MS18-B7のActual MMD Manual Verification Closeout、実MMDでのVMD / MMD用WAV読み込み・再生・リップ同期目視確認、MS18 closeout判定を行うとき。 |
| [MS19_Block_Breakdown.md](file:///d:/Kanna_Works/MMD_AppWork/MMD_AutoLipTool-dev/MMD_AutoLipTool_Antigravity/docs/Implementation_Plan/MS19_Block_Breakdown.md) | ~20KB | MS19全体のブロック分解、Voice-only InputのIn/Out of Scope、TEXTあり / TEXTなし状態契約、各Block依存関係を確認するとき。 |
| [MS19-B1_Implementation_Plan.md](file:///d:/Kanna_Works/MMD_AppWork/MMD_AutoLipTool-dev/MMD_AutoLipTool_Antigravity/docs/Implementation_Plan/MS19-B1_Implementation_Plan.md) | ~22KB | MS19-B1のVoice-only Input Requirements / State Contract、音声のみ入力実装前の状態契約固定、現行TEXT必須導線確認、B2以降への引き継ぎを確認するとき。 |
| [MS19-B2_Implementation_Plan.md](file:///d:/Kanna_Works/MMD_AppWork/MMD_AutoLipTool-dev/MMD_AutoLipTool_Antigravity/docs/Implementation_Plan/MS19-B2_Implementation_Plan.md) | ~24KB | MS19-B2のTranscription Pipeline Pre-check、Whisper raw result保持、書き起こし本文抽出候補、timing anchor契約、エラー分類、既存テスト不足を確認するとき。 |
| [MS19-B3_Implementation_Plan.md](file:///d:/Kanna_Works/MMD_AppWork/MMD_AutoLipTool-dev/MMD_AutoLipTool_Antigravity/docs/Implementation_Plan/MS19-B3_Implementation_Plan.md) | ~18KB | MS19-B3のTextless Pipeline Integration Foundation、Whisper raw resultからの本文抽出helper、既存Whisper timing結果を再利用するcore契約、core単体テスト方針を確認するとき。 |
| [MS19-B4_Implementation_Plan.md](file:///d:/Kanna_Works/MMD_AppWork/MMD_AutoLipTool-dev/MMD_AutoLipTool_Antigravity/docs/Implementation_Plan/MS19-B4_Implementation_Plan.md) | ~20KB | MS19-B4のGUI Entry Point and State Handling、TEXTなし音声入力時の解析ボタン有効条件、voice_only GUI状態、`AnalysisWorker` 分岐、InfoPanel最小反映、TEXTなしVMD保存無効化、B4テスト/ユーザー確認結果を確認するとき。 |
| [MS19-B5_Implementation_Plan.md](file:///d:/Kanna_Works/MMD_AppWork/MMD_AutoLipTool-dev/MMD_AutoLipTool_Antigravity/docs/Implementation_Plan/MS19-B5_Implementation_Plan.md) | ~26KB | MS19-B5のReview / Edit Transcription Result Flow、音声のみ解析結果の書き起こし編集、編集後preview更新、編集前timing plan誤用防止、保持済み `WhisperTimingResult` と worker 入力契約による編集済みテキスト再解析実装を確認するとき。 |
| [MS19-B6_Implementation_Plan.md](file:///d:/Kanna_Works/MMD_AppWork/MMD_AutoLipTool-dev/MMD_AutoLipTool_Antigravity/docs/Implementation_Plan/MS19-B6_Implementation_Plan.md) | ~24KB | MS19-B6のVMD / Preview / Save Integration、音声のみ入力のVMD保存有効化、TEXT pathなし保存入口、Preview追従、既存TEXTあり保存導線維持を確認するとき。 |
| [MS19-B7_Implementation_Plan.md](file:///d:/Kanna_Works/MMD_AppWork/MMD_AutoLipTool-dev/MMD_AutoLipTool_Antigravity/docs/Implementation_Plan/MS19-B7_Implementation_Plan.md) | ~24KB | MS19-B7のError Handling / Tests / Docs、音声のみ入力の失敗条件分類、テスト実行状態、README / 配布用readme / 関連docs同期を確認するとき。 |
| [MS19-B8_Implementation_Plan.md](file:///d:/Kanna_Works/MMD_AppWork/MMD_AutoLipTool-dev/MMD_AutoLipTool_Antigravity/docs/Implementation_Plan/MS19-B8_Implementation_Plan.md) | ~25KB | 完了済みMS19-B8のWorkspace Reset / New Session Flow、作業データ限定reset、ファイルメニュー導線、確認・Busy・設定履歴保持・late callback契約、検証結果を確認するとき。 |
| [MS19-B9_Implementation_Plan.md](file:///d:/Kanna_Works/MMD_AppWork/MMD_AutoLipTool-dev/MMD_AutoLipTool_Antigravity/docs/Implementation_Plan/MS19-B9_Implementation_Plan.md) | ~16KB | MS19-B9 Closeoutの成果監査、テスト再実行、ユーザー確認証拠、文書同期、P1 / P2 / P3分類、A / B / C判定を確認するとき。 |
| [MS17_Block_Breakdown.md](file:///d:/Kanna_Works/MMD_AppWork/MMD_AutoLipTool-dev/MMD_AutoLipTool_Antigravity/docs/Implementation_Plan/MS17_Block_Breakdown.md) | ~27KB | MS17全体のロードマップ、各ブロック of In/Out of Scope、依存関係を確認したいとき。 |
| [MS17-B9_Implementation_Plan.md](file:///d:/Kanna_Works/MMD_AppWork/MMD_AutoLipTool-dev/MMD_AutoLipTool_Antigravity/docs/Implementation_Plan/MS17-B9_Implementation_Plan.md) | ~50KB | MS17 closeout、限定テスト、README/docs/ライセンス・配布関連文書の最終整合確認を行うとき。 |
| [MS17-B6_Implementation_Plan.md](file:///d:/Kanna_Works/MMD_AppWork/MMD_AutoLipTool-dev/MMD_AutoLipTool_Antigravity/docs/Implementation_Plan/MS17-B6_Implementation_Plan.md) | ~58KB | 直近で完了した音声入力導線統合の具体的な設計、テスト方針、`AppController` 連携仕様を参照したいとき。 |
| [MMD_Audio_WAV_Compatibility_Specification.md](file:///d:/Kanna_Works/MMD_AppWork/MMD_AutoLipTool-dev/MMD_AutoLipTool_Antigravity/docs/MMD_Audio_WAV_Compatibility_Specification.md) | ~19KB | 完了済みの「MMD用WAV出力 (MS17-B7)」に関して、MMD互換性のあるWAVのコンテナ・コーデック・chunk方針等の仕様を確認したいとき。 |
| [Error_Handling_Specification.md](file:///d:/Kanna_Works/MMD_AppWork/MMD_AutoLipTool-dev/MMD_AutoLipTool_Antigravity/docs/Error_Handling_Specification.md) | ~47KB | 音声処理（ffprobe/ffmpegエラー、ファイル制限オーバーなど）のエラーハンドリング、ユーザー通知、ログ分類ポリシーを確認・拡張するとき。 |
| [Pipeline_Data_Contract_Specification.md](file:///d:/Kanna_Works/MMD_AppWork/MMD_AutoLipTool-dev/MMD_AutoLipTool_Antigravity/docs/Pipeline_Data_Contract_Specification.md) | ~38KB | 「入力音声」「解析用WAV」「MMD用WAV」「Preview Shape」などのデータ境界、およびパイプライン状態遷移（無効化ルールなど）を確認するとき。 |
| [GUI_State_Theme_Specification.md](file:///d:/Kanna_Works/MMD_AppWork/MMD_AutoLipTool-dev/MMD_AutoLipTool_Antigravity/docs/GUI_State_Theme_Specification.md) | ~34KB | GUIのBusy制御、テーマ定義、ダイアログ表示ルール、wxPython状態遷移を確認するとき。 |

---

## 3. MS17の超重要設計ルール（概要）

以下の設計ルールは、各仕様書の根底にある「崩してはならない前提」です。

### 3.1 音声データの三権分立 (正本分離)
パイプライン内で以下の3つの音声を混同しないこと。
1. **入力音声 (User Input)**: ユーザーが読み込んだファイル (`.wav`, `.mp3`, `.m4a` 等)。
2. **解析用WAV (Internal Analysis WAV)**: ツール内部で波形表示・Whisper解析の正本として使用する一時WAV (`PCM signed 16-bit, 44100Hz`)。
3. **MMD用WAV (Export MMD WAV)**: 専用の出力導線で保存する、MMD読み込み互換性を最優先したWAV。

### 3.2 音声制限値とエラー分類
* **ファイルサイズ制限**: 500MB超は読み込み拒否。
* **音声長さ制限**: 15分 (900秒) 超は読み込み拒否。
* **エラーハンドリング**: `audio_errors.py` に集約。UIスレッドをブロックせず、過度に技術的すぎないメッセージでユーザーに通知する。

### 3.3 FFmpeg/ffprobe 探索ポリシー
1. アプリ実行パス下の `FFmpeg\bin\ffmpeg.exe` (および `ffprobe.exe`) を最優先探索。
2. 検出できない場合は、環境変数 `PATH` から探索。
3. いずれも見つからない場合は、FFmpeg未検出エラーとして明確にユーザーに通知する（自動ダウンロードはセキュリティおよびライセンス上の懸念から絶対に行わない）。

---

## 4. エージェント向け：トークン節約のための「目的別」最小参照ガイド

タスクを実行する際、エージェントは以下のガイドに従って必要なファイルのみを閲覧してください。

* **音声変換やFFmpegの動作を修正したい場合**:
  * [src/core/audio_convert.py](file:///d:/Kanna_Works/MMD_AppWork/MMD_AutoLipTool-dev/MMD_AutoLipTool_Antigravity/src/core/audio_convert.py)
  * [src/core/ffmpeg_runner.py](file:///d:/Kanna_Works/MMD_AppWork/MMD_AutoLipTool-dev/MMD_AutoLipTool_Antigravity/src/core/ffmpeg_runner.py)
* **GUIの音声読み込み導線や状態遷移を修正したい場合**:
  * [src/gui_wx/app_controller.py](file:///d:/Kanna_Works/MMD_AppWork/MMD_AutoLipTool-dev/MMD_AutoLipTool_Antigravity/src/gui_wx/app_controller.py)
  * [src/gui_wx/ui_state.py](file:///d:/Kanna_Works/MMD_AppWork/MMD_AutoLipTool-dev/MMD_AutoLipTool_Antigravity/src/gui_wx/ui_state.py)
* **エラーメッセージや例外処理を拡張したい場合**:
  * [src/core/audio_errors.py](file:///d:/Kanna_Works/MMD_AppWork/MMD_AutoLipTool-dev/MMD_AutoLipTool_Antigravity/src/core/audio_errors.py)
  * [docs/Error_Handling_Specification.md](file:///d:/Kanna_Works/MMD_AppWork/MMD_AutoLipTool-dev/MMD_AutoLipTool_Antigravity/docs/Error_Handling_Specification.md)

これらのガイドを遵守し、`repo_milestone.md` などの巨大ファイルへの無駄なアクセスを徹底的に排除すること。

---

## 5. ソースコード・目録 (src/)

MS17以降の設計・開発に関連する `src` 配下の主要モジュール一覧です。

### 5.1 コアロジック系 (`src/core/`)

| ファイル名とリンク | サイズ | 役割・概要とMS17における位置づけ |
| :--- | :--- | :--- |
| [audio_input.py](file:///d:/Kanna_Works/MMD_AppWork/MMD_AutoLipTool-dev/MMD_AutoLipTool_Antigravity/src/core/audio_input.py) | ~1.3KB | 音声入力ファイル情報を管理するデータ構造。拡張子 (`.wav`/`.mp3`/`.m4a`) の判定等。 |
| [audio_probe.py](file:///d:/Kanna_Works/MMD_AppWork/MMD_AutoLipTool-dev/MMD_AutoLipTool_Antigravity/src/core/audio_probe.py) | ~5.4KB | ffprobe を使った入力音声ファイルの長さ、サイズ等の制限検査。 |
| [audio_convert.py](file:///d:/Kanna_Works/MMD_AppWork/MMD_AutoLipTool-dev/MMD_AutoLipTool_Antigravity/src/core/audio_convert.py) | ~3.6KB | ffmpeg を用いた「解析用WAV」の生成と、一時ファイルの出力制御。 |
| [audio_errors.py](file:///d:/Kanna_Works/MMD_AppWork/MMD_AutoLipTool-dev/MMD_AutoLipTool_Antigravity/src/core/audio_errors.py) | ~2.0KB | 音声制限違反、FFmpeg未検出、ファイル破損等の独自例外定義。 |
| [ffmpeg_locator.py](file:///d:/Kanna_Works/MMD_AppWork/MMD_AutoLipTool-dev/MMD_AutoLipTool_Antigravity/src/core/ffmpeg_locator.py) | ~2.6KB | アプリ内 `FFmpeg\bin\` または環境変数 `PATH` からの実行バイナリ探索ロジック。 |
| [ffmpeg_runner.py](file:///d:/Kanna_Works/MMD_AppWork/MMD_AutoLipTool-dev/MMD_AutoLipTool_Antigravity/src/core/ffmpeg_runner.py) | ~2.0KB | ffmpeg.exe プロセスの実行および非同期制御・停止。 |
| [mmd_wav_export.py](file:///d:/Kanna_Works/MMD_AppWork/MMD_AutoLipTool-dev/MMD_AutoLipTool_Antigravity/src/core/mmd_wav_export.py) | ~8.0KB | 元音声ファイルからMMD用WAVを生成する専用出力処理。`pcm_s16le / 44100Hz / stereo`、一時ファイル経由保存、検証、失敗時cleanupを担当。 |
| [ffprobe_runner.py](file:///d:/Kanna_Works/MMD_AppWork/MMD_AutoLipTool-dev/MMD_AutoLipTool_Antigravity/src/core/ffprobe_runner.py) | ~1.9KB | ffprobe.exe プロセスの実行とJSON出力取得。 |
| [pipeline.py](file:///d:/Kanna_Works/MMD_AppWork/MMD_AutoLipTool-dev/MMD_AutoLipTool_Antigravity/src/core/pipeline.py) | ~75.8KB | **【巨大ファイル注意】** 全体の解析タイミングパイプラインの制御ロジック。 |
| [preview_transform.py](file:///d:/Kanna_Works/MMD_AppWork/MMD_AutoLipTool-dev/MMD_AutoLipTool_Antigravity/src/core/preview_transform.py) | ~21.7KB | プレビューの台形変形、プレビュー形状データコントラクト（MS16-B5固定）。 |
| [settings_store.py](file:///d:/Kanna_Works/MMD_AppWork/MMD_AutoLipTool-dev/MMD_AutoLipTool_Antigravity/src/core/settings_store.py) | ~19.0KB | アプリケーション設定の永続化。 |
| [whisper_timing.py](file:///d:/Kanna_Works/MMD_AppWork/MMD_AutoLipTool-dev/MMD_AutoLipTool_Antigravity/src/core/whisper_timing.py) | ~6.4KB | Whisperを活用した音声タイミングの解析・同期。 |

### 5.2 GUI表示・コントローラ系 (`src/gui_wx/`)

| ファイル名とリンク | サイズ | 役割・概要とMS17における位置づけ |
| :--- | :--- | :--- |
| [app_controller.py](file:///d:/Kanna_Works/MMD_AppWork/MMD_AutoLipTool-dev/MMD_AutoLipTool_Antigravity/src/gui_wx/app_controller.py) | ~15.0KB | 状態遷移と非同期タスクのコーディネーター。音声入力の検証・パイプライン接続を統括。 |
| [ui_state.py](file:///d:/Kanna_Works/MMD_AppWork/MMD_AutoLipTool-dev/MMD_AutoLipTool_Antigravity/src/gui_wx/ui_state.py) | ~4.1KB | UIの有効・無効状態や音声情報などのステートストア。 |
| [audio_worker.py](file:///d:/Kanna_Works/MMD_AppWork/MMD_AutoLipTool-dev/MMD_AutoLipTool_Antigravity/src/gui_wx/audio_worker.py) | ~2.0KB | MS17-B8で追加。ffprobe / 解析用WAV生成 / MMD用WAV出力をGUIスレッド外で実行し、wx.CallAfterで結果通知する。 |
| [worker_state.py](file:///d:/Kanna_Works/MMD_AppWork/MMD_AutoLipTool-dev/MMD_AutoLipTool_Antigravity/src/gui_wx/worker_state.py) | ~3.0KB | MS17-B8で追加。AudioWorkerKind / AudioWorkerStatus / AudioWorkerState / CancelToken と terminate→kill 補助を定義。 |
| [main_frame.py](file:///d:/Kanna_Works/MMD_AppWork/MMD_AutoLipTool-dev/MMD_AutoLipTool_Antigravity/src/gui_wx/main_frame.py) | ~43.1KB | wxPython メインフレーム。ファイルダイアログ、ステータスバー等。 |
| [waveform_panel.py](file:///d:/Kanna_Works/MMD_AppWork/MMD_AutoLipTool-dev/MMD_AutoLipTool_Antigravity/src/gui_wx/waveform_panel.py) | ~9.9KB | 解析用WAVを描画する波形パネル。 |
| [preview_panel.py](file:///d:/Kanna_Works/MMD_AppWork/MMD_AutoLipTool-dev/MMD_AutoLipTool_Antigravity/src/gui_wx/preview_panel.py) | ~14.0KB | 口の変形を描画するプレビューパネル。 |
| [right_pane.py](file:///d:/Kanna_Works/MMD_AppWork/MMD_AutoLipTool-dev/MMD_AutoLipTool_Antigravity/src/gui_wx/right_pane.py) | ~6.3KB | タブ表示（Info / Warnings 等）の右側ペイン。 |

### 5.3 VMDライター系 (`src/vmd_writer/`)

| ファイル名とリンク | サイズ | 役割・概要とMS17における位置づけ |
| :--- | :--- | :--- |
| [writer.py](file:///d:/Kanna_Works/MMD_AppWork/MMD_AutoLipTool-dev/MMD_AutoLipTool_Antigravity/src/vmd_writer/writer.py) | ~118.0KB | **【巨大ファイル注意】** VMDバイナリファイルの出力モジュール。リップモーフキーフレームの書き出しを担当。 |

---

## 6. テストコード・目録 (tests/)

MS17以降の動作保証とデグレード防止のための主要テストファイルの一覧です。

### 6.1 音声入力・変換・制限検証用 (MS17追加分)

| ファイル名とリンク | サイズ | 対象機能・テスト観点 |
| :--- | :--- | :--- |
| [test_ms17_b3_audio_input_foundation.py](file:///d:/Kanna_Works/MMD_AppWork/MMD_AutoLipTool-dev/MMD_AutoLipTool_Antigravity/tests/test_ms17_b3_audio_input_foundation.py) | ~2.2KB | 音声入力の抽象化データ構造、およびタイミング無効化の基礎検証。 |
| [test_ms17_b3_ffmpeg_locator.py](file:///d:/Kanna_Works/MMD_AppWork/MMD_AutoLipTool-dev/MMD_AutoLipTool_Antigravity/tests/test_ms17_b3_ffmpeg_locator.py) | ~5.1KB | FFmpegバイナリ優先探索および環境変数PATH探索の挙動検証。 |
| [test_ms17_b4_audio_input_limits.py](file:///d:/Kanna_Works/MMD_AppWork/MMD_AutoLipTool-dev/MMD_AutoLipTool_Antigravity/tests/test_ms17_b4_audio_input_limits.py) | ~3.9KB | 500MB制限、15分制限に違反するファイルのバリデーション拒否検証。 |
| [test_ms17_b4_audio_probe.py](file:///d:/Kanna_Works/MMD_AppWork/MMD_AutoLipTool-dev/MMD_AutoLipTool_Antigravity/tests/test_ms17_b4_audio_probe.py) | ~6.3KB | ffprobe でのコーデック、サンプリングレートなどの情報取得の正常・異常系検証。 |
| [test_ms17_b4_ffprobe_runner.py](file:///d:/Kanna_Works/MMD_AppWork/MMD_AutoLipTool-dev/MMD_AutoLipTool_Antigravity/tests/test_ms17_b4_ffprobe_runner.py) | ~2.4KB | ffprobe.exe の呼び出し、プロセス実行とエラーのテスト。 |
| [test_ms17_b5_audio_convert.py](file:///d:/Kanna_Works/MMD_AppWork/MMD_AutoLipTool-dev/MMD_AutoLipTool_Antigravity/tests/test_ms17_b5_audio_convert.py) | ~5.9KB | ffmpeg による解析用WAV生成、および失敗時の不完全ファイル削除検証。 |
| [test_ms17_b5_audio_cache.py](file:///d:/Kanna_Works/MMD_AppWork/MMD_AutoLipTool-dev/MMD_AutoLipTool_Antigravity/tests/test_ms17_b5_audio_cache.py) | ~2.0KB | 解析用WAVキャッシュの命名・再利用・削除方針の検証。 |
| [test_ms17_b5_ffmpeg_runner.py](file:///d:/Kanna_Works/MMD_AppWork/MMD_AutoLipTool-dev/MMD_AutoLipTool_Antigravity/tests/test_ms17_b5_ffmpeg_runner.py) | ~2.7KB | ffmpeg.exe の非同期プロセスの制御・キャンセルテスト。 |
| [test_ms17_b7_mmd_wav_export.py](file:///d:/Kanna_Works/MMD_AppWork/MMD_AutoLipTool-dev/MMD_AutoLipTool_Antigravity/tests/test_ms17_b7_mmd_wav_export.py) | ~5.3KB | MMD用WAV出力core、stereo固定、ch1/ch2選択、mono複製、`-bitexact` コマンド、検証失敗系のテスト。 |
| [test_ms17_b7_mmd_wav_failure_cleanup.py](file:///d:/Kanna_Works/MMD_AppWork/MMD_AutoLipTool-dev/MMD_AutoLipTool_Antigravity/tests/test_ms17_b7_mmd_wav_failure_cleanup.py) | ~2.1KB | MMD用WAV生成失敗時に一時ファイルを削除し、既存出力を壊さないことの検証。 |
| [test_ms17_b7_mmd_wav_button_state.py](file:///d:/Kanna_Works/MMD_AppWork/MMD_AutoLipTool-dev/MMD_AutoLipTool_Antigravity/tests/test_ms17_b7_mmd_wav_button_state.py) | ~2.2KB | 解析用WAV生成済み状態に応じた「MMD用WAV出力」ボタン有効化の検証。 |
| [test_ms17_b7_mmd_wav_save_dialog.py](file:///d:/Kanna_Works/MMD_AppWork/MMD_AutoLipTool-dev/MMD_AutoLipTool_Antigravity/tests/test_ms17_b7_mmd_wav_save_dialog.py) | ~2.0KB | MMD用WAV保存ダイアログの初期名、拡張子付与、キャンセル扱いの検証。 |
| [test_ms17_b7_mmd_wav_overwrite_confirm.py](file:///d:/Kanna_Works/MMD_AppWork/MMD_AutoLipTool-dev/MMD_AutoLipTool_Antigravity/tests/test_ms17_b7_mmd_wav_overwrite_confirm.py) | ~2.1KB | 既存ファイル指定時の上書き確認とキャンセル時非出力の検証。 |
| [test_ms17_b8_audio_worker_state.py](file:///d:/Kanna_Works/MMD_AppWork/MMD_AutoLipTool-dev/MMD_AutoLipTool_Antigravity/tests/test_ms17_b8_audio_worker_state.py) | ~1.0KB | audio_job_id と AudioWorkerState の状態判定を検証。 |
| [test_ms17_b8_cancel_ffmpeg_ffprobe.py](file:///d:/Kanna_Works/MMD_AppWork/MMD_AutoLipTool-dev/MMD_AutoLipTool_Antigravity/tests/test_ms17_b8_cancel_ffmpeg_ffprobe.py) | ~2.0KB | cancellable ffmpeg/ffprobe runner が Popen 経路を使うこと、terminate→kill 補助を検証。 |
| [test_ms17_b8_long_audio_confirmation.py](file:///d:/Kanna_Works/MMD_AppWork/MMD_AutoLipTool-dev/MMD_AutoLipTool_Antigravity/tests/test_ms17_b8_long_audio_confirmation.py) | ~1.5KB | 300秒超過時に確認キャンセルで解析用WAV生成へ進まないことを検証。 |
| [test_ms17_b8_busy_action_states.py](file:///d:/Kanna_Works/MMD_AppWork/MMD_AutoLipTool-dev/MMD_AutoLipTool_Antigravity/tests/test_ms17_b8_busy_action_states.py) | ~1.6KB | 音声worker実行中に主要操作が無効化され、キャンセルだけ有効になることを検証。 |
| [test_ms17_b8_late_worker_result_discard.py](file:///d:/Kanna_Works/MMD_AppWork/MMD_AutoLipTool-dev/MMD_AutoLipTool_Antigravity/tests/test_ms17_b8_late_worker_result_discard.py) | ~1.3KB | 古い audio_job_id の worker 結果が現在状態へ反映されないことを検証。 |
| [test_wx_ms14_b3_input.py](file:///d:/Kanna_Works/MMD_AppWork/MMD_AutoLipTool-dev/MMD_AutoLipTool_Antigravity/tests/test_wx_ms14_b3_input.py) | ~4.0KB | GUI音声入力導線、解析用WAV生成後の状態更新、MS17-B6/B8統合後の入力回帰を検証。 |

### 6.2 プレビュー形状・VMDライター等 (デグレード防止用)

| ファイル名とリンク | サイズ | 対象機能・テスト観点 |
| :--- | :--- | :--- |
| [test_wx_ms16_b4_preview_shape.py](file:///d:/Kanna_Works/MMD_AppWork/MMD_AutoLipTool-dev/MMD_AutoLipTool_Antigravity/tests/test_wx_ms16_b4_preview_shape.py) | ~2.7KB | プレビュー台形変形の形状計算が壊れていないかの検証。 |
| [test_vmd_writer_intervals.py](file:///d:/Kanna_Works/MMD_AppWork/MMD_AutoLipTool-dev/MMD_AutoLipTool_Antigravity/tests/test_vmd_writer_intervals.py) | ~44.0KB | VMD出力におけるインターバル計算とキーフレーム整合性テスト。 |
| [test_vmd_writer_zero_guard.py](file:///d:/Kanna_Works/MMD_AppWork/MMD_AutoLipTool-dev/MMD_AutoLipTool_Antigravity/tests/test_vmd_writer_zero_guard.py) | ~34.9KB | VMDライター内のゼロガードロジックのロバスト性テスト。 |
