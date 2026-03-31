# MS11-6 Implementation Plan

## 0. Document Info

- Document Name: `docs/MS11-6_Implementation_Plan.md`
- Created: 2026-03-31
- Target Milestone: `MS11-6`
- Target Repository: `MMD_AutoLipTool`
- Baseline Version: `Ver 0.3.6.2`
- Baseline Completed Milestones:
  - MS10
  - GUIFIX series
  - MS11-1
  - MS11-2
  - MS11-2_FIX01
  - MS11-2_FIX02
  - MS11-3
  - `writer.py` local fixes after MS11-3
  - MS11-4
  - MS11-5 first-stage implementation

### 0.1 Baseline Understanding

At the `Ver 0.3.6.2` baseline, the following are already treated as implemented on the MS11-5 side:

- `PeakValueEvaluation` remains in place
- `PeakValueObservation` has been added as a higher-level observation record
- `_build_peak_value_observations()` exists in `pipeline.py`
- `tests/test_pipeline_peak_values.py` includes direct observation-helper tests

However, the current understanding is that:

- the observation helper is still mainly connected through direct helper usage and tests
- the main pipeline flow does not yet expose observation results in a naturally retrievable way
- the pre-refinement timeline and post-refinement timeline are not yet organized as a clearly trackable pair in the main flow
- the current writer path should be treated as stable and must not be broken by MS11-6

MS11-6 is therefore positioned as a **connection-cleanup milestone**, not as a writer redesign or GUI milestone.

### 0.2 Implementation Reflection Note (2026-03-31)

As of 2026-03-31, MS11-6 is treated as implemented in the repository with the following reached state:

- `VowelTimingPlan` is the first canonical holder of optional/internal observation data
- main flow preserves both initial timeline meaning and refined timeline meaning through observation construction
- `PipelineResult` only relays optional observation data when available
- `timeline` remains the canonical writer input
- provided timing plan handling is clarified as:
  - preserve observation when the provided timing plan is used as-is
  - drop observation to `None` when duration inference rebuilds the provided timeline

---

## 1. Position of MS11-6

MS11-6 is the milestone that connects the MS11-5 observation foundation to the main pipeline flow in a controlled way.

The purpose of MS11-6 is **not** to redesign the writer, and **not** to redesign the GUI.  
It is also **not** the milestone for RMS constant retuning. That judgment belongs to the next milestone, MS11-7.

MS11-6 should remain focused on:

- preserving the meaning of MS11-5 observation data
- making initial / refined interval tracking practical in main-flow-connected usage
- exposing observation data in an internal and backward-compatible manner
- keeping the current `timeline` as the canonical writer input

---

## 2. Goal

The goal of MS11-6 is to make the observation information introduced in MS11-5 retrievable from the pipeline flow when needed, without breaking the current writer path or broadening scope into unrelated areas.

This goal can be broken down into the following points:

1. Preserve the pre-refinement timeline and the refined timeline in a way that allows both to be referenced coherently.
2. Make `PeakValueObservation` usable from main-flow-connected code paths when needed.
3. Keep `timeline` as the canonical writer input and avoid introducing writer-side redesign.
4. Maintain backward compatibility as much as possible for existing pipeline return contracts and call patterns.
5. Prepare a stable foundation for MS11-7 real-data observation review and RMS retuning judgment.

---

## 3. Scope

### 3.1 In Scope

- `src/core/pipeline.py`
- `tests/test_pipeline_peak_values.py`
- `tests/test_pipeline_and_vmd.py`
- optional minimum related documentation updates, if implementation state needs to be synchronized later

### 3.2 Main Focus

- main-flow preservation of initial timeline
- main-flow preservation of refined timeline
- observation retrieval path design
- backward-compatible internal connection cleanup
- integration-level validation of observation data

### 3.3 Out of Scope

The following are out of scope for MS11-6:

- `writer.py` redesign
- GUI constant display of observation data
- Preview Area debug display
- Preview trapezoid / multi-point visualization work
- RMS constant retuning
- large-scale output-shape redesign
- GUI responsiveness / splash / packaging work

---

## 4. Completion Criteria

MS11-6 is considered complete when all of the following are satisfied:

1. The main pipeline flow preserves enough information to distinguish initial timeline state from refined timeline state.
2. Observation data can be retrieved from a main-flow-connected path when needed.
3. `PeakValueObservation` is no longer effectively limited to direct helper tests.
4. Existing `timeline` remains the canonical writer input.
5. Existing pipeline → writer behavior remains stable.
6. Existing return contracts are not broken in a careless or unnecessary way.
7. Integration tests confirm that:
   - initial interval and refined interval can both be tracked
   - observation values remain coherent with evaluation values
   - fallback and zero-reason handling remain explainable
8. RMS retuning is still deferred to MS11-7.

---

## 5. Implementation Policy

### 5.1 Core Policy

MS11-6 should connect observation data to the main flow **without replacing the existing canonical pipeline behavior**.

That means:

- do not replace `timeline` with observation objects
- do not move writer-side logic into pipeline observation structures
- do not change the role of `PeakValueEvaluation`
- do not expose observation data as a mandatory GUI/public contract if it can remain internal or optional

### 5.2 Compatibility Policy

Backward compatibility should be preserved as much as possible.

Practical interpretation:

- existing main code paths should continue to work
- existing writer handoff should continue to use `timeline`
- any new observation-carrying path should be introduced with minimal disruption
- avoid unnecessary breaking changes in `VowelTimingPlan`, `PipelineResult`, or related return paths

### 5.3 Boundaries

MS11-6 must not drift into:

- writer-side shape redesign
- GUI observation display work
- RMS retuning
- startup / responsiveness / packaging work

---

## 6. Detailed Implementation Targets

### 6.1 Preserve Initial Timeline in Main Flow

At present, the refined timeline is the practical output of the pipeline flow, while the initial allocation timeline is not yet treated as a clearly paired reference in that same flow.

MS11-6 should establish a structure in which:

- the pre-refinement timeline can be preserved
- the refined timeline can be preserved
- both can be referenced together when building observations

The exact implementation form may vary, but the meaning must remain clear.

### 6.2 Connect Observation Building to Main-Flow-Connected Usage

`_build_peak_value_observations()` already exists.  
MS11-6 should connect it so that observation data can be retrieved from a main-flow-connected path when needed.

Important constraints:

- observation data should not replace `timeline`
- observation data may remain internal or optional
- main processing semantics should remain centered on `timeline`

### 6.3 Keep `PeakValueEvaluation` Stable

`PeakValueEvaluation` must remain in place.  
MS11-6 is not a replacement milestone for that structure.

The intended relationship remains:

- `PeakValueEvaluation` as the evaluation result unit
- `PeakValueObservation` as the higher-level observation unit that includes evaluation and contextual interval/window information

### 6.4 Observation Contents That Must Remain Traceable

At minimum, MS11-6 should preserve or expose the ability to track the following coherently:

- event index
- vowel
- representative `time_sec`
- initial interval
- refined interval
- peak window
- `local_peak`
- `global_peak`
- final `peak_value`
- `reason`
- fallback information
- window sample count
- nested `PeakValueEvaluation`

### 6.5 Optional/Internal Exposure Policy

Observation exposure does not need to become a broad public contract in MS11-6.

Preferred direction:

- make it retrievable when needed
- keep it internal and controlled if possible
- avoid turning it into GUI-facing always-on state at this stage

---

## 7. Test Policy

### 7.1 Keep Existing Direct Observation Tests

The existing observation-helper-oriented tests in `tests/test_pipeline_peak_values.py` should remain valid.

Existing direct observation coverage should continue to confirm items such as:

- initial / refined interval distinction
- halo window behavior
- sample count behavior
- fallback observation behavior
- mismatched initial timeline length handling

### 7.2 Add Main-Flow-Connected Coverage

MS11-6 should add or update tests so that observation availability is no longer limited to direct helper calls.

Candidate additions include:

1. A test confirming that main-flow-connected usage can retrieve observation data.
2. A test confirming that initial interval and refined interval remain distinguishable in that path.
3. A test confirming that observation `evaluation` remains coherent with final `peak_value` and `reason`.
4. A test confirming that fallback behavior remains explainable in the connected flow.

### 7.3 Preserve Pipeline → Writer Regression Stability

Existing pipeline → writer tests must continue to pass conceptually.

MS11-6 should not break:

- current writer handoff through `timeline`
- current use of `peak_value`
- current suppression of meaningless zero-only output shapes on the writer side

---

## 8. Expected Phase Breakdown

## Phase 1: Contract Fixing

- decide where observation data should be carried, if at all, in the main flow
- decide how initial timeline and refined timeline will be preserved together
- fix the compatibility policy before implementation broadens

## Phase 2: Initial / Refined Timeline Preservation

- preserve initial timeline in the main flow
- preserve refined timeline in the main flow
- ensure both can be referenced without semantic confusion

## Phase 3: Observation Connection

- connect `_build_peak_value_observations()` to a main-flow-connected path
- keep the connection internal / optional if appropriate
- avoid replacing canonical `timeline` behavior

## Phase 4: Integration Test Expansion

- extend integration coverage so that observation retrieval is validated outside direct helper-only usage
- verify coherence between observation data and evaluation data

## Phase 5: Stability Check

- confirm existing pipeline → writer behavior remains intact
- confirm that no unintended redesign pressure was introduced into writer or GUI paths

## Phase 6: Document Sync

- synchronize the reached state into milestone / specification / version-control documents if needed after implementation is confirmed

---

## 9. Implementation Notes

- Do not redesign `writer.py` here.
- Do not add GUI constant debug display here.
- Do not start RMS retuning here.
- Do not broaden this work into Preview shape redesign here.
- Keep `timeline` as canonical writer input.
- Preserve backward compatibility wherever practical.
- Avoid introducing a mandatory public-facing observation contract unless explicitly required.
- If a design tradeoff appears, prefer the minimal change that preserves observation traceability and main-flow stability.

---

## 10. Expected Deliverables

MS11-6 is expected to produce, at minimum:

- updated main-flow-connected observation handling in `pipeline.py`
- preserved initial / refined timeline traceability
- updated pipeline-side tests
- integration-level confirmation that observation data is retrievable without breaking current writer behavior
- optional minimum documentation sync after implementation is verified

---

## 11. Handoff into MS11-7

MS11-6 should end by preparing a clean transition into MS11-7.

MS11-7 is expected to use the improved observation connection to:

- review real-data `peak_value = 0.0` cases
- classify reasons with evidence
- determine whether RMS constants require minimal retuning

MS11-6 itself must not perform that retuning judgment.  
Its role is to make that later judgment better grounded and easier to execute.

---
