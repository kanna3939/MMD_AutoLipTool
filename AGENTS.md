# AGENTS.md

## Project overview

This repository is a Windows desktop tool project for MikuMikuDance (MMD).
The app is developed in Python and runs on Windows 11.
The intended GUI framework is PySide6.
The final goal is a tool that reads one UTF-8 text file and one PCM WAV file, then generates a VMD lip-motion file for MMD.

## Working assumptions

- OS target: Windows 11
- Language: Python 3
- IDE/editor: Visual Studio Code
- GUI: PySide6
- Packaging target: Windows executable
- Development is performed in a local virtual environment (.venv)

## Product scope

- This is a small Windows utility application, not a web app.
- The tool is intended for single-run desktop usage.
- The final output target is a VMD file for lip motion.
- Lip morph targets are fixed to: あ, い, う, え, お
- Keep implementations aligned with the current repository scope and existing specification documents.

## Change policy

- Prefer small, reviewable changes.
- Do not perform large refactors unless explicitly requested.
- Do not rename many files or reorganize the whole project unless explicitly requested.
- Do not add unrelated features.
- Do not replace the selected stack unless explicitly requested.
- Before making broad changes, first explain the proposed scope briefly.

## Implementation policy

- Start from the minimum working version.
- Keep modules separated by responsibility.
- Prefer clear and simple code over clever code.
- Avoid unnecessary dependencies.
- Do not introduce network-dependent features unless explicitly requested.
- Preserve Windows compatibility in file paths, dialogs, and packaging behavior.

## Expected repository structure

Prefer a structure close to the following unless the repository already defines another structure:

- src/
- src/gui/
- src/core/
- src/app_io/
- tests/
- sample/

If an existing structure is already present, adapt to it instead of forcing a rewrite.

## Coding rules

- Use explicit, readable names.
- Keep functions and classes focused.
- Add comments only where intent is not obvious from code.
- Avoid hardcoding absolute local paths.
- Use UTF-8 for text files unless the repository explicitly requires otherwise.

## Testing and validation

- After making changes, explain how to run the affected part locally.
- When practical, prefer verification steps that work in VS Code terminal on Windows.
- For GUI changes, keep the first implementation minimal and runnable.
- For file-processing changes, avoid silently changing file formats or encodings.

## Git and task discipline

- Assume the user may create a Git checkpoint before and after each task.
- Keep each task narrow enough to review in a single diff.
- Report changed files after implementation.
- Summarize what remains unimplemented if the task is only partial.

## MMD-specific guidance

- This project is for MMD-related desktop tooling.
- Do not assume advanced animation features unless explicitly requested.
- Focus on practical tooling for MMD workflows.
- When implementing lip-motion behavior, keep the current project goal in mind: simple automatic vowel-based lip motion, not full phoneme-accurate animation.

## Interaction rules

- If repository context is unclear, inspect the current files first and summarize the structure before making broad edits.
- If a task can be split into a safer first step, prefer the safer first step.
- If asked to implement something large, propose a minimal first milestone before expanding.
