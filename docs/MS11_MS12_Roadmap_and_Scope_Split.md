# MS11_MS12_Roadmap_and_Scope_Split.md

## 0. Document Info

- Document Name: `docs/MS11_MS12_Roadmap_and_Scope_Split.md`
- Created: 2026-03-30
- Last Updated: 2026-04-01
- Target Repository: `MMD_AutoLipTool`
- Baseline Version: `Ver 0.3.6.4`
- Purpose:
  - Record the agreed milestone split after MS11-5.
  - Clarify which remaining items belong to MS11 and which belong to MS12.
  - Provide a Codex-friendly roadmap with fixed scope boundaries.
  - Record the policy for future dependency bundling work, including FFmpeg bundling.
  - Keep packaging and bundled-file growth under control.

---

## 1. Current Baseline

The following are already completed and should be treated as fixed baseline:

- MS10 completed
- GUIFIX series completed
- MS11-1 completed
- MS11-2 completed
- MS11-2_FIX01 completed
- MS11-2_FIX02 completed
- MS11-3 completed
- writer.py local fixes after MS11-3 completed
- MS11-4 completed
- MS11-5 first-stage implementation completed
- `Ver 0.3.6.4` committed

Current understanding of the project state:

- Major writer-side issues are mostly converged.
- Main remaining work on the MS11 side is:
  - MS11-7 real-data observation review execution
  - RMS retuning necessity judgment finalization
  - remaining output-quality expansion that still belongs to MS11
- GUI responsiveness / splash behavior should be handled separately from MS11.
- Packaging / distribution dependency handling should also be treated separately from MS11.

---

## 2. Fixed Scope Split

The following scope split is fixed.

### 2.1 Items that belong to MS11

The following user-requested items are treated as part of MS11:

1. Add a separate user input for **mouth-closing softness** (in frame units), independent from morph max value, and use it to make the closing slope from fall start to zero more gradual.
2. Change Preview-side vowel visualization from simple filled area style to **trapezoid / multi-point compatible shape display**.

Interpretation:

- These are not just GUI cosmetics.
- They affect output-shape semantics or Preview representation of output-shape semantics.
- Therefore they belong to the MS11 line, not to the GUI-only line.

### 2.2 Items that belong to MS12

The following user-requested items are treated as part of MS12:

1. Prevent the UI from appearing frozen during processing; allow periodic UI refresh / animation while heavy processing runs.
2. Fix the splash screen so that it appears earlier during application startup.
3. Show the current version number on the splash screen.
4. Bundle FFmpeg with the distributed application if bundling is adopted as the release policy.

Interpretation:

- These items are GUI / execution responsiveness / startup UX / packaging work.
- They are not part of pipeline observation cleanup or output-shape quality work.
- Therefore they belong to the MS12 line.

---

## 3. Milestone Policy After MS11-5

After MS11-5, the roadmap is split into:

- **MS11 line**:
  - pipeline observation / connection cleanup
  - output-quality related extensions
  - Preview-side display alignment with output-shape behavior
- **MS12 line**:
  - GUI responsiveness
  - processing-time UX
  - splash/startup UX
  - packaging / dependency bundling cleanup

Important rule:

- Do not mix MS11 and MS12 tasks in the same implementation step unless explicitly instructed.
- MS11 should remain focused on pipeline / writer / Preview representation consistency.
- MS12 should remain focused on GUI behavior, startup/processing UX, and packaging/distribution behavior.

---

## 4. MS11 Roadmap After Ver 0.3.6.4

## MS11-6
### Name
pipeline observation connection cleanup

### Goal
Turn the MS11-5 observation helper from a mostly test-oriented helper into a structure that can be referenced from the main pipeline flow when needed, without breaking the current writer path.

### Main target
- `src/core/pipeline.py`
- `tests/test_pipeline_peak_values.py`
- `tests/test_pipeline_and_vmd.py`

### Main work
- Preserve initial timeline in the main flow
- Keep refined timeline in the main flow
- Make observation data retrievable from the pipeline flow when needed
- Keep existing `timeline` as the canonical writer input
- Do not redesign writer here
- Do not redesign GUI here

### Completion image
- `PeakValueObservation` is no longer effectively limited to direct helper tests
- initial interval and refined interval can be tracked in main-flow-connected usage
- existing pipeline → writer behavior remains stable

### Status Note (2026-03-31)
- Treated as implemented.
- `VowelTimingPlan` is now the first canonical holder of optional/internal observation data.
- provided timing plan behavior is clarified as:
  - preserve observation when the plan is used as-is
  - drop observation to `None` when duration inference rebuilds the provided timeline

---

## MS11-7
### Name
real-data observation review and RMS retuning decision

### Goal
Use actual observation results to determine whether RMS constants need minimal retuning.

### Main target
- pipeline-side observation outputs
- pipeline-side tests
- optional documentation for reviewed real-data cases

### Main work
- Collect and classify `peak_value = 0.0` cases
- Confirm the main reasons:
  - `rms_unavailable`
  - `global_peak_zero`
  - `no_peak_in_window`
  - `below_abs_threshold`
  - `below_rel_threshold`
- Decide whether RMS constant retuning is needed
- If needed, keep changes minimal

### Completion image
- Real-data zero-peak cases are explainable
- Retuning necessity is judged with evidence
- Large-scale tuning is still avoided

### Status Note (2026-04-01)
- Documentation scaffolding for MS11-7 is in place.
- `docs/MS11-7_Implementation_Plan.md` and `docs/MS11-7_Real_Data_Observation_Review.md` are added as the current written baseline.
- A minimum observation-boundary test for `global_peak_zero` is added.
- Actual real-data review execution and final retuning judgment are still pending.

---

## MS11-8
### Name
mouth-closing softness control

### Goal
Add a new control for the closing slope so that mouth closing can be made more gradual, independently from morph max value.

### Main target
- `src/vmd_writer/writer.py`
- writer-related tests
- only the minimum required parameter handoff path, if UI input is needed later

### Main work
- Define the new setting concept clearly
- Apply it to the fall-start → zero closing shape
- Keep current shape families compatible as much as possible
- Avoid breaking existing fallback behavior

### Important note
This is a **shape-generation** task, not a pure GUI task.

### Completion image
- Closing softness is controllable
- Existing output logic remains coherent
- writer regression coverage is updated

---

## MS11-9
### Name
Preview trapezoid / multi-point display alignment

### Goal
Replace the current Preview-side simple filled-area style with a display that better matches actual output-shape behavior.

### Main target
- `src/gui/preview_area.py`
- `src/gui/preview_transform.py`
- only minimal `main_window.py` changes if needed

### Main work
- Reflect at least trapezoid-style visualization in Preview
- Add multi-point compatible Preview display if the current writer-side shape logic requires it
- Keep shared viewport / playback sync stable
- Do not mix this with MS12 startup or responsiveness work

### Important note
This is treated as MS11 because it is a representation-alignment task for output-shape logic.

### Completion image
- Preview representation is closer to actual writer-side shape semantics
- Existing playback / viewport sync remains intact

---

## MS11-10
### Name
MS11 final consistency sync

### Goal
Synchronize the final MS11 state across code assumptions, documents, and milestone tracking.

### Main target
- `docs/repo_milestone.md`
- `docs/Specification_Prompt_v3.md`
- `docs/Version_Control.md`
- related MS11 planning documents if necessary

### Main work
- Sync the final MS11 reached state
- Clarify what remains outside MS11
- Prepare clean handoff into MS12

### Completion image
- MS11 end state is documented consistently
- Remaining GUI-only work is clearly separated into MS12

---

## 5. MS12 Roadmap

## MS12
### Name
GUI responsiveness, startup UX, and packaging cleanup

### Scope summary
MS12 is intentionally separated from MS11 and should cover:

- GUI responsiveness work
- event-loop / processing-time UX work
- splash / startup UX work
- distribution / dependency bundling work

### Important rule
These items are intentionally split away from MS11.

They should be treated as:

- GUI / event-loop / responsiveness work
- startup UX work
- packaging / distribution work
- not pipeline observation work
- not writer output-shape work

---

## MS12-1
### Name
processing-time UI responsiveness improvement

### Goal
Reduce the perception that the UI is frozen during heavy processing.

### Main target
- `src/gui/main_window.py`
- processing-time dialog / execution control path
- any minimum required GUI-side helper modules

### Main work
- Allow periodic UI refresh during heavy processing
- Keep double-run prevention intact
- Keep state restoration intact after success / failure
- Avoid introducing unstable partial-state behavior

### Completion image
- The UI no longer appears fully frozen during normal processing runs
- Existing processing guard rules still hold

---

## MS12-2
### Name
splash timing improvement

### Goal
Make the splash screen appear earlier during startup.

### Main target
- startup path
- splash initialization path
- minimum required startup-related files only

### Main work
- Move splash display earlier in startup order where safe
- Avoid breaking existing initialization order
- Keep the change limited to startup UX behavior

### Completion image
- Splash appears early enough to serve its intended startup-feedback role
- Main window startup remains stable

---

## MS12-3
### Name
splash version display

### Goal
Show the current application version on the splash screen.

### Main target
- splash rendering path
- version source wiring

### Main work
- Add version text to splash
- Keep version source single and consistent
- Avoid duplicating version constants unnecessarily

### Completion image
- Splash shows the current version correctly
- Existing version-display paths remain consistent

---

## MS12-4
### Name
distribution dependency bundling cleanup

### Goal
Handle bundling-oriented release cleanup separately from GUI responsiveness work, including possible FFmpeg bundling.

### Main target
- build / packaging definition
- release-side documentation
- only the minimum runtime dependency resolution path required for distribution

### Main work
- Decide whether FFmpeg bundling is adopted
- If adopted, define the bundling method for the release build
- Update build scripts / spec files only where required
- Update release-side license / notice documents accordingly
- Confirm runtime dependency resolution without requiring user-side PATH setup

### Important note
This is a **distribution / packaging** task, not an MS11 task.

### Completion image
- External runtime dependency handling is documented and reproducible
- If FFmpeg is bundled, it is bundled intentionally and minimally
- User-side manual FFmpeg installation is not required if bundling policy is adopted

---

## 6. Bundled File Minimization Policy

This policy applies especially to MS12-4, but should also be respected in other packaging-related work.

### 6.1 Core rule

Only bundle files that are **strictly necessary** for runtime execution and agreed release behavior.

### 6.2 What this means in practice

- Do not bundle optional tools that are not used at runtime
- Do not bundle duplicate helper binaries
- Do not bundle development-only files
- Do not bundle debug-only files
- Do not bundle unused sample data
- Do not bundle unused model data
- Do not bundle entire external tool folders if only a small subset is required

### 6.3 FFmpeg-specific minimization rule

If FFmpeg bundling is adopted:

- bundle only the minimum required executable set
- do not bundle unrelated FFmpeg companion files unless actually required
- do not bundle multiple alternative FFmpeg builds
- keep the distribution-side FFmpeg footprint as small as possible
- include only the required accompanying license / notice files for the chosen bundled build

### 6.4 Packaging intent

The packaging goal is:

- no unnecessary environment pollution for users
- no unnecessary increase of release size
- no accidental dependency sprawl
- no silent inclusion of files that are not part of the approved release scope

---

## 7. Recommended Execution Order

The recommended order after `Ver 0.3.6.4` is:

1. MS11-7
2. MS11-8
3. MS11-9
4. MS11-10
5. MS12-1
6. MS12-2
7. MS12-3
8. MS12-4

Reasoning:

- First stabilize pipeline-side observation and connection.
- Then judge RMS retuning based on evidence.
- Then extend writer-side shape behavior.
- Then align Preview-side representation with that shape behavior.
- Then perform final MS11 sync.
- After MS11 is stable, address GUI responsiveness and startup UX.
- Put dependency bundling cleanup, including FFmpeg bundling, at the end of MS12 so it reflects the final agreed release behavior and avoids rework.

---

## 8. Scope Guard Rules for Future Work

Unless explicitly instructed otherwise, follow these rules:

1. Do not move items 2-4 from the user request list back into MS11.
2. Do not move items 1 and 5 from the user request list into MS12.
3. Do not mix MS12 GUI responsiveness work into MS11-6 or MS11-7.
4. Do not redesign writer during MS11-6.
5. Do not redesign GUI during MS11-6 or MS11-7.
6. Treat Preview shape alignment as MS11 work, not as generic GUI polish.
7. Treat splash / startup / processing responsiveness as MS12 work, not as output-quality work.
8. Treat FFmpeg bundling as MS12 packaging work, not as MS11 output-quality work.
9. Keep bundled files to the minimum necessary set.
10. Do not expand release artifacts casually during bundling tasks.

---

## 9. Notes for Codex

This document is a roadmap and scope-split memo.

What Codex should infer from this document:

- The milestone split here is intentional and fixed.
- MS11 and MS12 serve different purposes.
- If asked to implement one of the listed tasks, Codex should first check which milestone it belongs to.
- If a requested implementation would cross the milestone boundary, Codex should stop and ask before broadening scope.
- Bundling-related work should stay minimal and explicit.
- If FFmpeg bundling is implemented, it should be done in the MS12 packaging phase, not earlier.

What Codex should **not** infer:

- This document is not permission to implement all items at once.
- This document does not override detailed implementation constraints in existing milestone-specific documents.
- This document does not authorize large redesign outside the explicitly assigned milestone.
- This document does not authorize bundling extra files beyond the minimum required runtime set.

---
