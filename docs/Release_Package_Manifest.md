# Release Package Manifest

## 1. 目的

この文書は、MMD_AutoLipTool の GitHub Releases 向け配布ZIPに含めるファイル、含めないファイル、確認手順を定義する。

## 2. 配布方針

- GitHub Releases で配布する
- 実行用ZIPは手動または release workflow で作成する
- Source code ZIP / tar.gz は GitHub Releases の自動生成に任せる
- 実行用ZIPは PyInstaller onefile 前提とする
- 通常利用者には実行用ZIPを案内する
- Source code は開発者向けとして扱う
- Whisperのversioned manifestは実行ファイルへ組み込むが、外部取得するmodel weightsは実行用ZIPへ同梱しない
- Whisper model weightsは、利用者がGUIで明示的に `Download & Verify` を実行した場合だけ、manifestの公式URLから取得する
- 2026-07-02時点では `FFmpeg\bin\` の実体ファイルがGit追跡対象であるため、GitHubの自動生成 Source code ZIP / tar.gz にもFFmpegバイナリが含まれる前提でlicense noticeを確認する
- MS27-B3実装時点（2026-09-14）では、upstream revision、公式Downloadページを起点とした取得経路、revision固定のFFmpeg license参照先を記録し、ユーザー確認済み方針に基づきG-LICENSEをPassとした。現行FFmpeg versionは変更していない。B5で実行用ZIPの原文・通知配置は確認済みである。正確なWindows配布archive identity、完全な外部ライブラリ対応、公開時の対応ソース提供方式は、公開配布Readyとは別の未確認事項として残す

### 2.1 MS27-B4 artifact audit result (2026-09-14)

- fix-03候補のonefile build / SmokeLaunchはprocess exit code `0`で成功した。
- 候補EXEは425758214 bytes、SHA-256 `B211FA3312568C0E9067297157C63CEDA742BBFF67C5A84E62D2E1219F05965C`、FileVersion / ProductVersion `1.0.0`である。
- 内部archive監査でmatplotlib package/data、sample_data、旧Qt、Torch test/TensorBoard、Numba TBB任意backendは含まれないことを確認した。Whisper / Torch / Numba主要moduleは保持されている。
- `LICENSE`、`NOTICE`、`THIRD_PARTY_LICENSES.md`は候補内部でsource bytesとの一致を確認した既存B4証拠を継承する。ZIP外側の配置・展開・配布環境からの独立性は、後続B5の候補#08で確認済みである。
- ユーザーから手動確認通過・実MMD問題なしの報告を受領した。これはユーザー確認であり、Codex自身のGUI / 実MMD操作結果ではない。

### 2.2 MS27-B5 package verification result (2026-09-16)

- fix-03後のruntime除外補修を含む候補#08を採用した。EXEは425824202 bytes、SHA-256 `AF3B8FD65E3A518F5960EB4D697BE81AA773A1DAE312703552902D97D4CE4223`、FileVersion / ProductVersionは`1.0.0`である。
- `MMD_AutoLipTool_v1.0.0_Windows_onefile.zip`は423274681 bytes、SHA-256 `D963D5F619D48C59B2287992BF6AB350B23AA8DE240686477EA59093F9DB9086`。root必須5ファイルと`licenses/`を含む157 filesについて、入力・展開・実行先の全hash一致、CRC、安全なentry、不要なruntime data / weights / sample / 開発ファイルの非同梱を確認した。
- B5の配布実行では、repo外cwd、Windows標準PATHのみ、Python環境変数なしで同梱FFmpeg / ffprobe、3形式の音声、モデル未配置時の安全な停止、既存検証済みsmallモデルでの解析・VMD保存、通常終了・再起動・残留なしを確認した。スプラッシュ`Ver. 1.0.0`はユーザー目視確認として記録する。
- B5のG-PACKAGEはPass。ただし、exact provider archive provenance、完全なexternal-library対応、公開時の対応ソース提供方式、GitHub Release公開は未確認または未実施であり、公開Readyとは扱わない。

### 2.3 MS27-B6 readiness audit result (2026-09-18)

- 候補#08 EXE / ZIPとB5保存証跡をread-onlyで再照合し、§2.2のsize / SHA-256、157 files、B5実行証跡を確認した。B1〜B5のPassは維持する。
- 候補sourceの`MMD_AutoLipTool.spec`は現HEADと同一bytesである。候補embedded版の`THIRD_PARTY_LICENSES.md`はB5後の状態記録を含まない候補時点のbytesであり、現HEADとの差分を候補へ遡及させない。現HEAD版を実行用ZIPへ採用する場合は、B4 buildとB5 ZIP組立・照合を再実施する。
- Python 3.11 / 3.12のsource / build互換性は未検証だが、ユーザー決定によりWindows onefile公開判定から外した。`origin/main`は`2151d7b`を指し、FFmpeg 10 entriesとLICENSE / NOTICE / THIRD_PARTY_LICENSES / Manifestを追跡し、候補branchの`FFmpeg/bin`に差分がないことを確認した。ユーザーはGitHub上の既存公開を規約上問題なしと判断しており、Codexは法的適合を独自に保証しない。以上によりMS27 release readinessは**G-READY Pass**である。exact provider archive identityは既存B3方針上の非阻害provenance limitationとして維持する。
- このPassは、B5の実行用ZIP配置・実行確認の失敗を示すものではない。2026-09-18にユーザーがMS27 CloseOutを確定した。GitHub Release、tag、push、merge、公開用source archive生成は未実施の別工程である。

## 3. 実行用ZIP名

例:

- MMD_AutoLipTool_v1.0.0_Windows_onefile.zip

## 4. 実行用ZIPに含めるもの

必須:

- MMD_AutoLipTool.exe
- readme_mmdautolip.txt
- LICENSE
- NOTICE
- THIRD_PARTY_LICENSES.md

条件付き:

- FFmpeg 関連の正確な license/COPYING texts、copyright/NOTICE、必要な対応物

条件付き項目は、FFmpegを含む現在の配布方針では実質的に必須である。B3では、公式
Downloadページを起点とした取得経路と公式legal参照を採用し、license revisionと
binary revisionの厳密一致を要求しない。最終ZIPでの原文・対応物の実配置はB5で確認する。

`MMD_AutoLipTool.version.txt` は PyInstaller の Windows version resource 用ビルド入力であり、実行用ZIPへ単独では同梱しない。

### 4.2 MS27-B3 build input identity snapshot

次表は2026-09-14に確認したリポジトリ内FFmpeg入力のidentityであり、最終EXE/ZIPの
実同梱一覧ではない。全行が `FFmpeg\bin\` にあり、Git追跡対象である。

| File | Size (bytes) | SHA-256 |
| --- | ---: | --- |
| `ffmpeg.exe` | 542208 | `25F9F739794E20C7EBA08DD2E6C9165F79CA5C6D4423E07E9575DA0EA957E6D5` |
| `ffprobe.exe` | 228864 | `29221ACCA37F2BFB30CC17F1F9F219CEE0636383DFE48B4A8292B895AF988980` |
| `ffplay.exe` | 17744896 | `EDA12E438A5D509B0BE4D05292D58DB916C9049544A03A49BCF6B7F10A8C20F3` |
| `avcodec-62.dll` | 97590784 | `BE77A6E1872DF4591F090D948CD19FE3A1D0C02EF2642BF8A3307C33898F4E50` |
| `avdevice-62.dll` | 3683840 | `663A69109279A8A1C49AAA85FF18613C31C0FD9FE9F2DD87371C068B36B20858` |
| `avfilter-11.dll` | 94227456 | `59A7058E977D70C9B3A126303C44D691562CFF61080E8C89B9CD5D5168B3E847` |
| `avformat-62.dll` | 22062592 | `4B7E2144962F7851B828169BA162146CE77F99ED3AEBACD10959E6E4E619BD2B` |
| `avutil-60.dll` | 2930688 | `1B37A5835A1D895FB24A5DD0CAA84231B9EDFB753A76B5231748CE069E656259` |
| `swresample-6.dll` | 722944 | `C003F7911D0C160C0387D74F54A55BAF40C003405F7B322B46545988C2D76775` |
| `swscale-9.dll` | 12434432 | `E4089B3487534BAE9D4CAB56D694A738787C69201CB891BDE2DC3D0CC45267F9` |

Configuration evidence: `N-123549-g70537ec8e6-20260318`, with
`--enable-gpl --enable-version3`, `--enable-shared`, and
`--enable-whisper`. FFmpeg's FATE history records upstream revision
`N-123549-g70537ec8e6` on 2026-03-18. The revision-pinned upstream license
reference is:

- <https://raw.githubusercontent.com/FFmpeg/FFmpeg/70537ec8e6/LICENSE.md>

The local build signature is strongly consistent with BtbN's `win64` /
`gpl-shared` family, but the exact Windows release asset was not independently
identified. The user reports acquisition via the FFmpeg official Download page
at the time of acquisition. Under the user-confirmed B3 policy, exact
provider/archive correspondence and license-revision / binary-revision matching
are non-gating provenance limitations; final external-library mapping and
license/source placement remain later artifact checks.

含めない方針:

- sample/

`sample/` は、出典・ライセンス・用途説明が確定できるまでは実行用ZIPに含めない。

### 4.1 MS24 Whisper model distribution boundary

- `src/core/whisper_models.json` はPyInstaller specのpackage dataとして実行ファイルへ組み込む。
- `collect_data_files("whisper")`で取得されるWhisper package assetsは必要な実行時データとして扱う。
- `small.pt`、`medium.pt`、`large-v3-turbo.pt`などのmodel weightsは、リポジトリ、実行用ZIP、onefileへの同梱対象にしない。
- 利用者が明示的に `Download & Verify` を実行した場合だけ、versioned manifestの公式URLから取得し、exact sizeとSHA256を検証してローカル保存する。
- 実行用ZIPにmodel weightsが含まれないことと、解析時の自動downloadがないことを `readme_mmdautolip.txt` で案内する。

## 5. 実行用ZIPに含めないもの

- src/
- tests/
- docs/
- .agent/
- AGENTS.md
- .git/
- .venv/
- build/
- cache/
- __pycache__/
- .pytest_cache/
- *.pyc
- *.log
- *.tmp
- *.bak

## 6. GitHub Releases に表示されるもの

手動でアップロードするもの:

- MMD_AutoLipTool_v1.0.0_Windows_onefile.zip

GitHub が自動生成するもの:

- Source code (zip)
- Source code (tar.gz)

注意:

- GitHubの自動生成 Source code ZIP / tar.gz は、Gitで追跡されているファイルを含む。
- 2026-07-02時点では `FFmpeg\bin\ffmpeg.exe`, `FFmpeg\bin\ffprobe.exe`, 関連DLLがGit追跡対象である。
- そのため、実行用ZIPだけでなくSource code ZIP / tar.gzについても、FFmpeg同梱配布としてlicense noticeを確認する。

## 7. Release本文での案内

通常利用者には、実行用ZIPをダウンロードするよう案内する。

Source code は開発者向けであり、通常利用には不要であることを明記する。

## 8. 配布前チェック

- clean build が成功していること
- smoke launch が成功していること
- readme_mmdautolip.txt が同梱されていること
- LICENSE が同梱されていること
- NOTICE が同梱されていること
- THIRD_PARTY_LICENSES.md が同梱されていること
- FFmpeg 同梱時は、実際に同梱する version / build configuration / license 表記を確認していること
- `--enable-gpl --enable-version3` 等の構成がある場合は、該当する第三者ライセンス通知を同梱していること
- `FFmpeg\bin\` の実体がGit追跡対象である場合は、Source code ZIP / tar.gz側のFFmpeg license noticeも確認していること
- PyInstaller成果物の依存関係確認で、不要または意図しない依存関係が混入していないか確認していること
- `PySide6` など、wxPython主系ではない依存関係がPyInstallerログ / xrefに現れる場合は、配布サイズ・license notice・除外可否を確認していること
- `sample/` は、出典・ライセンス・用途説明が未確定なら実行用ZIPから除外していること
- 不要な開発用ファイルが混ざっていないこと
- GitHub Release 本文で Source code と実行用ZIPの違いを説明していること
- MS27-B3のG-LICENSEがPassであり、FFmpeg原文・出所・必要対応物が実物と対応していること

### 8.1 MS24-B7 static audit result

2026-08-28に、現行HEADのspec、package-data、tracked fileを読み取り専用で確認した。

- `MMD_AutoLipTool.spec`のrepo固有datasは `src/core/whisper_models.json -> src/core` である。
- `pyproject.toml`のpackage-dataは `core = ["whisper_models.json"]` である。
- `collect_data_files("whisper")` の列挙結果は `mel_filters.npz`、`multilingual.tiktoken`、`english.json`、`gpt2.tiktoken` の4件で、model weightsは含まれなかった。
- tracked fileの `*.pt`、`*.bin`、`*.part`、`models/` 検索では該当ファイルは見つからなかった。
- これはspecと開発ツリーの静的監査結果であり、onefile build、Analysis TOC、ZIP内容、PySide6の最終artifact混入判定ではない。これらはMS27で確認する。

## 9. MS18-B6 preflight result

2026-07-02時点のpreflight判定:

- 判定: package化へ進む前に追加確認が必要
- 理由:
  - `FFmpeg\bin\` の実体がGit追跡対象であり、GitHubの自動生成 Source code ZIP / tar.gzにもFFmpegバイナリが含まれる。
  - FFmpeg buildは `N-123549-g70537ec8e6-20260318` で、configurationに `--enable-gpl --enable-version3` を含む。
  - リポジトリ内にFFmpeg本体に対応する個別license texts / COPYING類は未確認。
  - PyInstaller xrefに `PySide6` / `PySide6.QtCore` / `PySide6.QtGui` / `PySide6.QtWidgets` が現れるため、配布内容・依存関係・license noticeの追加確認が必要。
  - `sample/` には音声・テキスト・pipeline生成用ディレクトリが存在するが、出典・ライセンス・用途説明が未確定のため、実行用ZIPから除外する方針とする。

package化へ進む前に必要な確認:

- FFmpeg関連license texts / noticeを、実行用ZIPおよびSource code ZIP / tar.gzの両方の前提で確定する。
- `FFmpeg\bin\` の実体をGit追跡に残すか、配布用ビルド入力として別管理にするかを判断する。
- PyInstaller xref上の `PySide6` 関連モジュールが最終成果物へ入るか、license noticeが必要か、除外できるかを確認する。
