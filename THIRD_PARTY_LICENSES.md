# THIRD_PARTY_LICENSES.md

## 1. Purpose

This document provides an overview of major third-party components used by
MMD AutoLip Tool and the licenses that should be reviewed for source and
binary distribution.

This file is an operational summary document.
For final release distribution, verify the exact resolved package versions and
their bundled license texts in the actual release environment.

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

### 3.1 PySide6 / Qt for Python

- Package / Framework: `PySide6`
- Role:
  - Main GUI framework
  - Windowing / widgets / event loop
- License family:
  - Qt for Python / Qt licensing terms apply
  - Review the applicable Qt / PySide6 license documents included with the package
- Notes:
  - For binary distribution, include the applicable Qt / PySide6 license notices
  - Verify the exact license files included in the installed distribution used for release
  - If distribution format or bundled modules change, re-check obligations before release

### 3.2 matplotlib

- Package: `matplotlib`
- Role:
  - Waveform plotting / chart rendering
- License:
  - Matplotlib license
- Notes:
  - Include the applicable license text in release-side third-party notices if required

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
  - Confirm the exact installed version used for release

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

---

## 4. Current Distribution Assumption

Current documented build policy is based on **PyInstaller onedir** output.

Documented included areas currently mention:

- Python modules under `src`
- PySide6
- matplotlib backend-related modules
- whisper submodules and assets
- pyopenjtalk data / dynamic libraries
- tiktoken / tiktoken_ext data and submodules

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
7. If FFmpeg or other external binaries are bundled in the future, add a dedicated section and include their exact license notices

---

## 6. Future External Binary Note

At the time of writing, this document does **not** assume FFmpeg is bundled.

If a future release bundles FFmpeg or other external multimedia binaries:

- add them explicitly to this document
- record the exact build source and version
- include the exact applicable license notices in the release package

---

## 7. Maintainer Note

Replace high-level placeholder wording above with exact versioned dependency
records when preparing a public release.

Recommended practice:

- generate a release-time dependency inventory
- confirm actual bundled files in `dist/`
- sync this document to the built artifact, not only to the development environment
