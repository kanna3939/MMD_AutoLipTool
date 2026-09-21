# THIRD_PARTY_LICENSES.md

## 1. Purpose

This document provides an overview of major third-party components used by
MMD AutoLip Tool and the licenses that should be reviewed for source and
binary distribution.

This file is an operational summary document.
For final release distribution, verify the exact resolved package versions and
their bundled license texts in the actual release environment.

### MS27-B3 implementation status (2026-09-14)

- The declared direct runtime dependencies and the observed local distribution
  metadata are recorded below.
- The local environment passes `pip check` with exit code 0. This is a metadata
  consistency result, not proof of the final frozen contents or license
  completeness.
- The current tracked FFmpeg build is recorded with file identities below.
- Web research on 2026-09-14 fixed the upstream revision and official FFmpeg
  license entry points recorded below. The user reports that acquisition was
  started from the FFmpeg official Download page at the time of acquisition.
  The exact Windows binary provider, release asset identity, and complete
  corresponding-source package for the selected files are not independently
  verified and remain provenance limitations.
- G-LICENSE is **Pass under the user-confirmed project policy**. The selected
  FFmpeg version is unchanged; current official FFmpeg license/legal references
  are used; and an exact license-revision / binary-revision match is not
  required by this project decision.
- Static B4/B5 artifact verification completed on 2026-09-15 is recorded in
  the next section. Candidate #08 later passed B5 GUI operation,
  independent-environment behavior, and normal-termination checks on
  2026-09-16; the splash version is user-reported and the detailed evidence is
  in the B5 plan ledger. This document is not public-release clearance.

### MS27-B4/B5 static artifact mapping (2026-09-15)

- Candidate-specific build, SmokeLaunch, version, and embedded-document
  comparisons are recorded in the B5 plan evidence ledger. Earlier static
  passes do not validate a subsequently changed exclusion policy or executable.
  Required values remain `FileVersion=1.0.0` and `ProductVersion=1.0.0`;
  embedded `LICENSE`, `NOTICE`, `THIRD_PARTY_LICENSES.md`, and `pyproject.toml`
  must match the candidate's repository inputs.
- The exclusion policy removes the `pytest` / `_pytest` test runners,
  `pylab`, `mpl_toolkits`, Matplotlib, and the retired PySide6 family.
  Names containing `test` are not a sufficient exclusion criterion:
  `numpy._pytesttester`, `jinja2.tests`, imported `torch.testing` helpers,
  and `torch._inductor.test_operators` are required by runtime imports.
  SymPy's Matplotlib adapter definitions are also retained for SymPy startup;
  they do not bundle the external Matplotlib package. PyTorch `_inductor`
  remains part of the active Whisper/Torch runtime path. Candidate-specific
  PYZ contents and runtime verification are recorded separately in the ledger.
- The adopted B5 static ZIP candidate, its size/hash, and its work area are
  recorded in the B5 plan evidence ledger. The ZIP has 157 files; input and
  extracted trees have identical paths and SHA-256 values. Its root contains
  only the executable, readme, `LICENSE`, `NOTICE`, `THIRD_PARTY_LICENSES.md`,
  and `licenses/`.
- The following mapping is based on the actual frozen PYZ packages and the
  outer ZIP license tree. `PIL` is covered by Pillow; `whisper` is covered by
  openai-whisper. The paths are evidence of staged text, not a legal opinion
  about obligations beyond the observed package metadata.

| Frozen package / component | Observed version | ZIP license path |
| --- | --- | --- |
| wxPython / `wx` | 4.2.5 | `licenses/wxpython/4.2.5/licenses/LICENSE.txt` |
| Pillow / `PIL` | 12.3.0 | `licenses/pillow/12.3.0/licenses/LICENSE` |
| NumPy / `numpy` | 2.4.3 | `licenses/numpy/2.4.3/licenses/` and nested files |
| openai-whisper / `whisper` | 20250625 | `licenses/openai-whisper/20250625/licenses/LICENSE` |
| pyopenjtalk | 0.4.1 | `licenses/pyopenjtalk/0.4.1/` and nested files |
| tiktoken | 0.14.0 | `licenses/tiktoken/0.14.0/licenses/LICENSE` |
| llvmlite | 0.49.0 | `licenses/llvmlite/0.49.0/licenses/` |
| numba | 0.67.0 | `licenses/numba/0.67.0/licenses/` |
| torch | 2.14.0 | `licenses/torch/2.14.0/licenses/` and nested files |
| tqdm | 4.70.0 | `licenses/tqdm/4.70.0/licenses/LICENCE` |
| regex | 2026.9.3 | `licenses/regex/2026.9.3/licenses/LICENSE.txt` |
| requests | 2.34.2 | `licenses/requests/2.34.2/licenses/LICENSE` and `NOTICE` |
| certifi | 2026.7.22 | `licenses/certifi/2026.7.22/licenses/LICENSE` |
| charset-normalizer | 3.5.1 | `licenses/charset-normalizer/3.5.1/licenses/LICENSE` |
| colorama | 0.4.6 | `licenses/colorama/0.4.6/licenses/LICENSE.txt` |
| filelock | 3.32.5 | `licenses/filelock/3.32.5/licenses/LICENSE` |
| fsspec | 2026.7.0 | `licenses/fsspec/2026.7.0/licenses/LICENSE` |
| idna | 3.19 | `licenses/idna/3.19/licenses/LICENSE.md` |
| Jinja2 | 3.1.6 | `licenses/jinja2/3.1.6/licenses/LICENSE.txt` |
| MarkupSafe | 3.0.3 | `licenses/markupsafe/3.0.3/licenses/LICENSE.txt` |
| more-itertools | 11.1.0 | `licenses/more-itertools/11.1.0/licenses/LICENSE` |
| mpmath | 1.3.0 | `licenses/mpmath/1.3.0/LICENSE` |
| NetworkX | 3.6.1 | `licenses/networkx/3.6.1/licenses/LICENSE.txt` |
| packaging | 26.3 | `licenses/packaging/26.3/licenses/` |
| Pygments | 2.20.0 | `licenses/pygments/2.20.0/licenses/LICENSE` |
| setuptools | 84.0.0 | `licenses/setuptools/84.0.0/licenses/LICENSE` |
| SymPy | 1.14.0 | `licenses/sympy/1.14.0/licenses/LICENSE` |
| typing-extensions | 4.16.0 | `licenses/typing-extensions/4.16.0/licenses/LICENSE` |
| urllib3 | 2.7.0 | `licenses/urllib3/2.7.0/licenses/LICENSE.txt` |
| PyInstaller bootloader / packaging | 6.19.0 | `licenses/pyinstaller/6.19.0/COPYING.txt` |
| FFmpeg binaries | `N-123549-g70537ec8e6-20260318` | `licenses/ffmpeg/N-123549-g70537ec8e6-20260318/` |

- `altgraph`, `pefile`, `pywin32-ctypes`, and
  `pyinstaller-hooks-contrib` are build-environment inputs, not frozen runtime
  packages in this candidate. Their build-only status is kept separate from
  the runtime license mapping.
- The outer ZIP candidate was created from the tree above and is a static
  package result. That mapping alone does not establish GUI acceptance,
  independent-environment execution, or normal-termination acceptance; those
  B5 results are recorded separately in the B5 plan ledger.

---

## 2. Project License

The source code of **MMD AutoLip Tool** is distributed under the **MIT License**.

See:

- `LICENSE`
- `NOTICE`

---

## 3. Major Third-Party Components

The following list is based on the current project structure, README, and
documented implementation state.

### 3.1 wxPython

- Package / Framework: `wxPython`
- Role:
  - Main GUI framework
  - Windowing / widgets / event loop
- License family:
  - wxWindows Library Licence (based on L-GPL)
  - Review the applicable wxPython license documents included with the package
- Notes:
  - For binary distribution, include the applicable wxPython license notices
  - Verify the exact license files included in the installed distribution used for release
  - If distribution format or bundled modules change, re-check obligations before release

### 3.2 matplotlib

- Package: `matplotlib`
- Role:
  - Historical B3 development-environment candidate only
- License:
  - Matplotlib license
- Notes:
  - The packaging policy excludes the `matplotlib` package, `pylab`, and
    `mpl_toolkits`; SymPy's own adapter definitions remain available because
    SymPy imports them during initialization
  - It is not present in the MS27-B5 static ZIP runtime license mapping

### 3.3 NumPy

- Package: `numpy`
- Role:
  - Numerical processing
  - Array handling for waveform / RMS-related processing
- License:
  - NumPy license
- Notes:
  - Verify exact version and included license text in the release environment

### 3.4 openai-whisper

- Package: `openai-whisper`
- Role:
  - Speech timing extraction
  - Whisper-based timing anchor generation
- License:
  - MIT License
- Notes:
  - Project dependency is pinned to `openai-whisper==20250625`
  - The current B7 verification environment imported `openai-whisper` version `20250625`
  - The versioned project manifest records the official model URL, filename, exact size, and SHA256 for `small`, `medium`, and `turbo`
  - Model weights are external user-managed files and are not bundled in the repository or the executable ZIP
  - The GUI downloads a model only after explicit user action through `Download & Verify`; analysis does not perform an implicit download or send audio externally
  - Confirm the exact resolved version and applicable license notices again for the final release artifact

### 3.5 pyopenjtalk

- Package: `pyopenjtalk`
- Role:
  - Japanese text processing support
  - Reading / phonetic conversion support
- License:
  - Review the package-provided license information
- Notes:
  - `pyopenjtalk` may include or rely on multiple upstream components
  - Verify bundled license texts for release distribution

### 3.6 tiktoken / tiktoken_ext

- Package:
  - `tiktoken`
  - `tiktoken_ext`
- Role:
  - Tokenizer-related internal dependency used by the environment documented in the build notes
- License:
  - Review the package-provided license information
- Notes:
  - Include license texts if bundled in the release build

### 3.7 PyInstaller

- Package: `PyInstaller`
- Role:
  - Windows executable packaging
- License:
  - Review PyInstaller license terms
- Notes:
  - PyInstaller itself is a build tool, but retain its notice where appropriate in release documentation

### 3.7.1 PySide6 observed in PyInstaller analysis

- Package: `PySide6`
- Role:
  - Not used as the active GUI framework
  - Observed in PyInstaller xref through matplotlib backend / Qt compatibility analysis
- License:
  - Review the applicable PySide6 / Qt license terms if bundled in the final release artifact
- Notes:
  - The active GUI line remains wxPython
  - Do not treat this as a revival of the old PySide6 GUI line
  - The MS27-B4 candidate excludes the PySide6 family; it is not a bundled
    runtime dependency of the MS27-B5 static ZIP candidate

### 3.8 FFmpeg

- Package / Binary: `FFmpeg`
- Role:
  - External multimedia runtime binary bundled for Windows distribution
- Source:
  - Current manually staged FFmpeg build
- Version:
  - Use the version currently staged under `FFmpeg\bin\`
  - The MS17 pre-check confirmed `N-123549-g70537ec8e6-20260318`
- Bundling policy:
  - Manual staging before build
  - Only the `bin` contents are used as build input
  - Staging path in repository: `FFmpeg\bin\`
  - Bundled output path: bundled within the single executable (extracted to temporary directory at runtime)
  - As of 2026-07-02, the staged `FFmpeg\bin\` binaries are also tracked by Git and therefore are expected to appear in GitHub-generated Source code ZIP / tar.gz archives
- License:
  - Review and include the applicable FFmpeg license notices for the chosen staged build
  - The confirmed staged build is configured with `--enable-gpl --enable-version3`; release packaging must treat that as a licensing check item
- Notes:
  - Keep the recorded FFmpeg version synchronized across README, NOTICE, and packaging-related docs
  - Do not silently switch FFmpeg source or version without updating release-side documents
  - If FFmpeg binaries remain tracked in Git, treat both binary release archives and GitHub source archives as FFmpeg-containing distribution artifacts for notice review

#### 3.8.1 Network research supplement (2026-09-14)

- The local `ffmpeg.exe` and `ffprobe.exe` report
  `N-123549-g70537ec8e6-20260318`. The FFmpeg FATE history independently lists
  upstream revision `N-123549-g70537ec8e6` on 2026-03-18:
  <https://fatebeta.ffmpeg.org/history/x86_64-archlinux-gcc-threads-misc?begin=350>
- The corresponding upstream source reference is the FFmpeg repository at
  revision `70537ec8e6`:
  <https://github.com/FFmpeg/FFmpeg/tree/70537ec8e6>
- The revision-pinned upstream license entry points are:
  - `LICENSE.md`:
    <https://raw.githubusercontent.com/FFmpeg/FFmpeg/70537ec8e6/LICENSE.md>
  - `COPYING.LGPLv2.1`:
    <https://raw.githubusercontent.com/FFmpeg/FFmpeg/70537ec8e6/COPYING.LGPLv2.1>
  - `COPYING.LGPLv3`:
    <https://raw.githubusercontent.com/FFmpeg/FFmpeg/70537ec8e6/COPYING.LGPLv3>
  - `COPYING.GPLv2`:
    <https://raw.githubusercontent.com/FFmpeg/FFmpeg/70537ec8e6/COPYING.GPLv2>
  - `COPYING.GPLv3`:
    <https://raw.githubusercontent.com/FFmpeg/FFmpeg/70537ec8e6/COPYING.GPLv3>
- The exact bytes retrieved from those revision-pinned URLs on 2026-09-14
  were stored temporarily for inspection. Their SHA-256 values were:

  | File | Size (bytes) | SHA-256 |
  | --- | ---: | --- |
  | `LICENSE.md` | 4346 | `2E1D16C72FD74E12063776371DA757322F8B77589386532F4FD8634BDE7DE1AF` |
  | `COPYING.LGPLv2.1` | 26517 | `246041B6ECF9BC32D718A62C57877C78B5EB397B6467E74ED7AE2626AB189C30` |
  | `COPYING.LGPLv3` | 7651 | `DA7EABB7BAFDF7D3AE5E9F223AA5BDC1EECE45AC569DC21B3B037520B4464768` |
  | `COPYING.GPLv2` | 18092 | `8177F97513213526DF2CF6184D8FF986C675AFB514D4E68A404010521B880643` |
  | `COPYING.GPLv3` | 35147 | `8CEB4B9EE5ADEDDE47B31E975C1D90C73AD27B6B165A1DCD80C7C545EB65B903` |

  These are upstream reference bytes, not yet the final release-package
  placement. The source tree and license references are immutable by commit
  ID, but the selected Windows archive and its complete external-library
  notices still require separate correspondence evidence.
- The exact local build evidence is `x86_64-w64-mingw32`, GCC 15.2.0,
  `--enable-gpl`, `--enable-version3`, `--enable-shared`, and
  `--enable-whisper`, together with the ten tracked files listed in the B3
  identity table. These are local binary/configuration facts, not a remote
  release checksum match.
- The local build is strongly consistent with the BtbN `win64` / `gpl-shared`
  build family: BtbN documents `win64` as x86_64 Windows, `gpl-shared` as the
  GPL dependency set with shared libav libraries, and its build script uses
  the FFmpeg repository plus a date-based `--extra-version`:
  <https://github.com/BtbN/FFmpeg-Builds/blob/master/README.md>
  <https://github.com/BtbN/FFmpeg-Builds/blob/master/build.sh>
- This provider attribution is an inference, not a confirmed archive
  identity. The currently retained BtbN release index did not expose an exact
  2026-03-18 asset for `N-123549-g70537ec8e6`; BtbN states that it retains the
  last 14 daily builds and the last build of each month for two years:
  <https://github.com/BtbN/FFmpeg-Builds/releases>
- BtbN's repository `LICENSE` is the MIT license for that build repository's
  files. It is not a replacement for the FFmpeg license texts or the licenses
  of external libraries linked into an FFmpeg build:
  <https://github.com/BtbN/FFmpeg-Builds/blob/master/LICENSE>
- FFmpeg's official legal guidance states that `--enable-gpl` changes the
  applicable FFmpeg license from the normal LGPL baseline to GPL terms. It also
  lists source, build configuration, archive, and external-library review
  considerations. The project adopts the current official license/legal
  references for this record and, by user decision, does not require an exact
  license-revision / binary-revision match:
  <https://ffmpeg.org/legal.html>
- Accordingly, the selected build is recorded as **GPL-enabled / version3-enabled**,
  not as an unqualified `GPLv3` label. The user-reported official Download-page
  acquisition route and current legal references are sufficient for the B3
  G-LICENSE decision. Exact provider archive, external-library mapping, and
  final release placement remain separately recorded provenance or artifact
  checks, not a B3 Hold.

### 3.9 MS27-B3 dependency and license ledger

The following is the 2026-09-14 B3 implementation snapshot. A package being
present in the development environment does not by itself establish that it is
in the final onefile executable. The final frozen component set is a B4
responsibility.

#### Direct runtime dependencies

| Component | Declared value | Observed METADATA | Runtime role | License evidence observed |
| --- | --- | --- | --- | --- |
| wxPython | `wxPython==4.2.5` | 4.2.5 | wx GUI and native runtime | Package `licenses/LICENSE.txt`; wxWindows Library Licence 3.1 and included LGPL text |
| matplotlib | `matplotlib==3.10.8` | 3.10.8 | waveform and plotting | Package `LICENSE`; Matplotlib terms and bundled-component notices |
| NumPy | `numpy==2.4.3` | 2.4.3 | numeric processing | Package `licenses/LICENSE.txt` and nested third-party license files |
| openai-whisper | `openai-whisper==20250625` | 20250625 | speech timing and transcription | Package `licenses/LICENSE`; MIT, Copyright 2022 OpenAI |
| pyopenjtalk | `pyopenjtalk==0.4.1` | 0.4.1 | Japanese phonetic processing | Package `licenses/LICENSE.md`; bundled dictionary `COPYING` also observed |

#### Observed runtime and build candidates

The values below are observed from installed METADATA and are not a new lock
file. Values differing from `requirements.txt` remain differences to explain;
they were not changed during B3.

| Component | Declared or parent source | Observed version | B3 classification |
| --- | --- | --- | --- |
| contourpy | `matplotlib` / requirements | 1.3.3 | runtime-transitive candidate |
| cycler | `matplotlib` / requirements | 0.12.1 | runtime-transitive candidate |
| fonttools | `matplotlib` / requirements `4.62.1` | 4.64.0 | runtime-transitive candidate; declared/observed difference |
| kiwisolver | `matplotlib` / requirements `1.5.0` | 1.5.1 | runtime-transitive candidate; declared/observed difference |
| packaging | `matplotlib` / PyInstaller / requirements `26.0` | 26.3 | runtime/build candidate; declared/observed difference |
| pillow | `matplotlib` / requirements `12.1.1` | 12.3.0 | runtime-transitive candidate; declared/observed difference |
| pyparsing | `matplotlib` / requirements | 3.3.2 | runtime-transitive candidate |
| python-dateutil | `matplotlib` / requirements | 2.9.0.post0 | runtime-transitive candidate |
| six | requirements | 1.17.0 | runtime-transitive candidate |
| tiktoken | `openai-whisper` Requires-Dist | 0.14.0 | runtime-transitive candidate; `tiktoken_ext` is a namespace, not an assumed distribution |
| more-itertools | `openai-whisper` Requires-Dist | 11.1.0 | runtime-transitive candidate |
| numba | `openai-whisper` Requires-Dist | 0.67.0 | runtime-transitive/native candidate |
| llvmlite | `numba` dependency | 0.49.0 | runtime-transitive/native candidate |
| torch | `openai-whisper` Requires-Dist | 2.14.0 | runtime-transitive/native candidate; bundled notices require final artifact review |
| tqdm | Whisper / pyopenjtalk dependency | 4.70.0 | runtime-transitive candidate |
| regex | `tiktoken` dependency | 2026.9.3 | runtime-transitive/native candidate |
| requests | `tiktoken` dependency | 2.34.2 | runtime-transitive candidate |
| networkx | `torch` dependency | 3.6.1 | runtime-transitive candidate |
| sympy | `torch` dependency | 1.14.0 | runtime-transitive candidate |
| mpmath | `sympy` dependency | 1.3.0 | runtime-transitive candidate |
| fsspec | `torch` dependency | 2026.7.0 | runtime-transitive candidate |
| PySide6 / Addons / Essentials / shiboken6 | observed environment and old PyInstaller xref | 6.10.2 | optional/observed only; final inclusion is unknown and must not be inferred |

#### Build inputs

| Component | Declared value | Observed version | B3 treatment |
| --- | --- | --- | --- |
| PyInstaller | requirements `6.19.0` | 6.19.0 | build-only; bootloader obligations are reviewed separately |
| pyinstaller-hooks-contrib | requirements `2026.3` | 2026.3 | build-only hook input |
| altgraph | requirements `0.17.5` | 0.17.5 | PyInstaller build dependency |
| pefile | requirements `2024.8.26` | 2024.8.26 | Windows build dependency |
| pywin32-ctypes | requirements `0.2.3` | 0.2.3 | Windows build dependency |
| setuptools | build-system `>=82.0.0`, requirements `82.0.1` | 84.0.0 | observed difference; no update or reinstall performed |

#### License source status

The following package-provided source files were present in the B3 local
environment. They are evidence of available upstream text, not yet the final
ZIP placement. Their exact bytes, all nested notices, and correspondence to the
actual frozen files must be rechecked in B4/B5.

| Component | Package-provided source observed | Current release placement |
| --- | --- | --- |
| wxPython 4.2.5 | `wxpython-4.2.5.dist-info/licenses/LICENSE.txt` | not fixed in repository/release package |
| matplotlib 3.10.8 | `matplotlib-3.10.8.dist-info/LICENSE` | not fixed in repository/release package |
| NumPy 2.4.3 | `numpy-2.4.3.dist-info/licenses/LICENSE.txt` and nested license files | not fixed in repository/release package |
| openai-whisper 20250625 | `openai_whisper-20250625.dist-info/licenses/LICENSE` | not fixed in repository/release package |
| pyopenjtalk 0.4.1 | `pyopenjtalk-0.4.1.dist-info/licenses/LICENSE.md` and dictionary `COPYING` | not fixed in repository/release package |
| tiktoken 0.14.0 | `tiktoken-0.14.0.dist-info/licenses/LICENSE` | not fixed in repository/release package |
| PyInstaller 6.19.0 | `pyinstaller-6.19.0.dist-info/licenses/COPYING.txt` | build input evidence only; final notice placement unresolved |
| pyinstaller-hooks-contrib 2026.3 | `pyinstaller_hooks_contrib-2026.3.dist-info/licenses/LICENSE` | build input evidence only |
| FFmpeg selected binaries | upstream revision, revision-pinned FFmpeg license entry points, official Download-page acquisition route, and current legal reference identified; exact provider archive and complete corresponding-source package remain unverified | **Pass under user-confirmed policy**; exact archive correspondence is a non-gating provenance limitation |

The package-provided files above do not prove that every native, vendored, font,
dictionary, bootloader, or statically linked component in the final executable
has been covered. The revision-pinned FFmpeg URLs above identify upstream
reference material, while the official Download-page acquisition route and
current legal reference are the B3 project policy basis. They do not by
themselves prove the selected Windows archive, exact external-library linkage,
or final ZIP placement; those remain later provenance or artifact checks.

---

## 4. Current Distribution Assumption

Current documented build policy is based on **PyInstaller onefile** output.

Documented included areas currently mention:

- Python modules under `src`
- wxPython
- no Matplotlib package, `pylab`, or `mpl_toolkits` in the final candidate
- whisper submodules and assets
- the versioned `src/core/whisper_models.json` manifest
- no external Whisper model weights
- pyopenjtalk data / dynamic libraries
- tiktoken / tiktoken_ext data and submodules
- Current FFmpeg / ffprobe `bin` contents staged under `FFmpeg\bin\`

Because actual bundled content may vary by environment and spec file changes,
final release verification should be performed against the built artifact.

---

## 5. Release Checklist for Licensing

Before a public GitHub release or binary distribution, verify at least the following:

1. `LICENSE` is present in the repository root
2. `NOTICE` is present in the repository root
3. `THIRD_PARTY_LICENSES.md` is updated for the actual release state
4. Binary release archives include:
   - `LICENSE`
   - `NOTICE`
   - applicable third-party license texts / notices
5. Exact package versions used for the release are recorded
6. If new dependencies are added, this file is updated
7. FFmpeg bundling details, exact version, build configuration, and applicable license notices are confirmed for the release build
8. If `FFmpeg\bin\` binaries remain tracked by Git, applicable FFmpeg notices are also checked for GitHub-generated Source code ZIP / tar.gz archives
9. PyInstaller xref / warn outputs are checked for optional GUI/backend dependencies such as PySide6

---

## 6. FFmpeg Bundling Note

At the time of writing, this document **does assume** FFmpeg is bundled.

Current assumption:

- currently staged FFmpeg build
- version confirmed from `FFmpeg\bin\ffmpeg.exe -version` and `FFmpeg\bin\ffprobe.exe -version`
- manual staging under `FFmpeg\bin\`
- bundle only the `bin` contents
- bundled within the single executable (`onefile` mode)
- the confirmed MS17 staged build reports `--enable-gpl --enable-version3`; release-side notices must account for this
- currently, the staged `FFmpeg\bin\` binaries are Git-tracked, so GitHub-generated source archives should also be reviewed as FFmpeg-containing artifacts

If this policy changes in a future release:

- update this document explicitly
- record the new build source and version
- include the exact applicable license notices in the release package

---

## 7. Maintainer Note

Replace high-level placeholder wording above with exact versioned dependency
records when preparing a public release.

Recommended practice:

- generate a release-time dependency inventory
- confirm actual bundled files in `dist/`
- sync this document to the built artifact, not only to the development environment
