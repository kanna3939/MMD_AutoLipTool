"""Outer MS32 transition envelope bound to an independently checked closure plan."""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any, Mapping

from src.core.cross_vowel_transition import (
    TransitionDecision,
    TransitionInputSnapshot,
    TransitionPairInput,
    TransitionResolution,
    TransitionSourceLineage,
    TransitionValidationResult,
    apply_transition_resolution_to_effective_plan,
    build_transition_pairs_from_effective_plan,
    read_transition_source_lineage,
    transition_effective_snapshot_json,
    validate_transition_resolution,
)
from src.core.final_morph_closure_plan import (
    ClosurePlan,
    ClosurePlanError,
    closure_plan_from_json,
    validate_closure_plan_integrity,
)
from src.core.final_morph_plan import (
    effective_plan_snapshot_digest,
)
from src.core.final_morph_capture import snapshot_digest
from src.core.morph_closure import (
    ClosureBuildResult,
    ClosureIssuerContext,
    TransitionClosureAdmission,
    build_closure_candidate,
    validate_closure_plan,
    _verify_source_context,
)
from src.core.effective_shape_plan import EffectiveShape
from src.core.morph_name_sets import SEMANTIC_VOWEL_ORDER

FINAL_MORPH_TRANSITION_SCHEMA = "final-morph-transition-plan/v1"
FINAL_MORPH_TRANSITION_SCHEMA_V2 = "final-morph-transition-plan/v2"


class TransitionPlanError(ValueError):
    """A transition envelope or its strict wire representation is invalid."""


def _is_digest(value: object) -> bool:
    return (
        isinstance(value, str)
        and len(value) == 64
        and all(character in "0123456789abcdef" for character in value)
    )


def _canonical_json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)


def _sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


@dataclass(frozen=True, slots=True)
class TransitionPlanIdentity:
    source_lineage: TransitionSourceLineage
    transition_input_digest: str
    policy_digest: str
    acoustic_digest: str
    baseline_effective_digest: str
    resolved_effective_digest: str
    resolved_effective_snapshot_sha256: str
    resolution_digest: str
    closure_semantic_digest: str
    closure_wire_digest: str

    def __post_init__(self) -> None:
        if not isinstance(self.source_lineage, TransitionSourceLineage):
            raise TransitionPlanError("source lineage is required")
        for name in (
            "transition_input_digest", "policy_digest", "acoustic_digest", "baseline_effective_digest",
            "resolved_effective_digest", "resolved_effective_snapshot_sha256", "resolution_digest",
            "closure_semantic_digest", "closure_wire_digest",
        ):
            if not _is_digest(getattr(self, name)):
                raise TransitionPlanError(f"{name} must be lowercase SHA-256")

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_lineage": self.source_lineage.to_dict(),
            "transition_input_digest": self.transition_input_digest,
            "policy_digest": self.policy_digest,
            "acoustic_digest": self.acoustic_digest,
            "baseline_effective_digest": self.baseline_effective_digest,
            "resolved_effective_digest": self.resolved_effective_digest,
            "resolved_effective_snapshot_sha256": self.resolved_effective_snapshot_sha256,
            "resolution_digest": self.resolution_digest,
            "closure_semantic_digest": self.closure_semantic_digest,
            "closure_wire_digest": self.closure_wire_digest,
        }


def _decision_dict(item: TransitionDecision) -> dict[str, Any]:
    return {
        "previous_event_index": item.previous_event_index,
        "next_event_index": item.next_event_index,
        "previous_morph": item.previous_morph,
        "next_morph": item.next_morph,
        "state": item.state,
        "reason": item.reason,
        "baseline_start_frame": item.baseline_start_frame,
        "candidate_start_frame": item.candidate_start_frame,
        "start_advance_frames": item.start_advance_frames,
        "baseline_overlap_width_frames": item.baseline_overlap_width_frames,
        "candidate_overlap_width_frames": item.candidate_overlap_width_frames,
        "overlap_width_delta_frames": item.overlap_width_delta_frames,
        "baseline_positive_integer_frames": list(item.baseline_positive_integer_frames),
        "candidate_positive_integer_frames": list(item.candidate_positive_integer_frames),
        "local_peak_ratio": item.local_peak_ratio,
    }


def _strict_decision(raw: object) -> TransitionDecision:
    fields = {
        "previous_event_index", "next_event_index", "previous_morph", "next_morph", "state", "reason",
        "baseline_start_frame", "candidate_start_frame", "start_advance_frames", "baseline_overlap_width_frames",
        "candidate_overlap_width_frames", "overlap_width_delta_frames", "baseline_positive_integer_frames",
        "candidate_positive_integer_frames", "local_peak_ratio",
    }
    if type(raw) is not dict or set(raw) != fields:
        raise TransitionPlanError("transition record fields do not match the strict schema")
    for name in (
        "previous_event_index", "next_event_index", "baseline_start_frame", "candidate_start_frame", "start_advance_frames"
    ):
        value = raw[name]
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            raise TransitionPlanError(f"{name} must be a non-negative integer")
    for name in (
        "previous_morph", "next_morph"
    ):
        if type(raw[name]) is not str or not raw[name]:
            raise TransitionPlanError(f"{name} must be non-empty text")
    if raw["state"] not in {"applied", "not_applicable"}:
        raise TransitionPlanError("transition record state is unsupported")
    if raw["reason"] is not None and (type(raw["reason"]) is not str or not raw["reason"]):
        raise TransitionPlanError("transition record reason is invalid")
    for name in (
        "baseline_overlap_width_frames", "candidate_overlap_width_frames", "overlap_width_delta_frames"
    ):
        value = raw[name]
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(float(value)):
            raise TransitionPlanError(f"{name} must be finite")
    for name in ("baseline_positive_integer_frames", "candidate_positive_integer_frames"):
        values = raw[name]
        if type(values) is not list or any(type(value) is not int or value < 0 for value in values):
            raise TransitionPlanError(f"{name} must be an integer array")
    ratio = raw["local_peak_ratio"]
    if ratio is not None and (
        isinstance(ratio, bool) or not isinstance(ratio, (int, float)) or not math.isfinite(float(ratio))
    ):
        raise TransitionPlanError("local_peak_ratio must be finite or null")
    return TransitionDecision(
        previous_event_index=raw["previous_event_index"],
        next_event_index=raw["next_event_index"],
        previous_morph=raw["previous_morph"],
        next_morph=raw["next_morph"],
        state=raw["state"],
        reason=raw["reason"],
        baseline_start_frame=raw["baseline_start_frame"],
        candidate_start_frame=raw["candidate_start_frame"],
        start_advance_frames=raw["start_advance_frames"],
        baseline_overlap_width_frames=float(raw["baseline_overlap_width_frames"]),
        candidate_overlap_width_frames=float(raw["candidate_overlap_width_frames"]),
        overlap_width_delta_frames=float(raw["overlap_width_delta_frames"]),
        baseline_positive_integer_frames=tuple(raw["baseline_positive_integer_frames"]),
        candidate_positive_integer_frames=tuple(raw["candidate_positive_integer_frames"]),
        local_peak_ratio=None if ratio is None else float(ratio),
    )


@dataclass(frozen=True, slots=True)
class FinalMorphTransitionPlan:
    state: str
    identity_context: TransitionPlanIdentity
    transition_records: tuple[TransitionDecision, ...]
    resolved_effective_snapshot_json: str
    closure_plan_json: str
    issues: tuple[str, ...]
    semantic_digest: str
    schema_id: str = FINAL_MORPH_TRANSITION_SCHEMA

    def __post_init__(self) -> None:
        object.__setattr__(self, "transition_records", tuple(self.transition_records))
        object.__setattr__(self, "issues", tuple(self.issues))
        if self.schema_id not in {FINAL_MORPH_TRANSITION_SCHEMA, FINAL_MORPH_TRANSITION_SCHEMA_V2}:
            raise TransitionPlanError("unknown final morph transition schema")
        if self.state not in {"valid", "invalid", "unavailable"}:
            raise TransitionPlanError("transition plan state is unsupported")
        if not isinstance(self.identity_context, TransitionPlanIdentity):
            raise TransitionPlanError("transition plan identity is invalid")
        if any(not isinstance(item, TransitionDecision) for item in self.transition_records):
            raise TransitionPlanError("transition records contain an invalid item")
        if any(type(issue) is not str or not issue for issue in self.issues):
            raise TransitionPlanError("transition issues must be non-empty text")
        snapshot = _canonicalize_snapshot_json(self.resolved_effective_snapshot_json)
        object.__setattr__(self, "resolved_effective_snapshot_json", snapshot)
        try:
            closure = closure_plan_from_json(self.closure_plan_json)
            validate_closure_plan_integrity(closure)
        except (ClosurePlanError, TypeError, ValueError) as error:
            raise TransitionPlanError("closure subproof is not a strict valid plan") from error
        canonical_closure = closure.to_json()
        object.__setattr__(self, "closure_plan_json", canonical_closure)
        if closure.semantic_digest != self.identity_context.closure_semantic_digest:
            raise TransitionPlanError("closure semantic digest differs from outer identity")
        if closure.wire_digest != self.identity_context.closure_wire_digest:
            raise TransitionPlanError("closure wire digest differs from outer identity")
        if _sha256(snapshot.encode("utf-8")) != self.identity_context.resolved_effective_snapshot_sha256:
            raise TransitionPlanError("resolved effective snapshot hash differs from outer identity")
        if self.state == "valid" and self.issues:
            raise TransitionPlanError("valid transition plan cannot contain blocking issues")
        if self.semantic_digest != _digest_plan(self._payload(include_digest=False)):
            raise TransitionPlanError("transition plan semantic digest mismatch")

    def _payload(self, *, include_digest: bool) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "schema_id": self.schema_id,
            "state": self.state,
            "identity_context": self.identity_context.to_dict(),
            "transition_records": [_decision_dict(item) for item in self.transition_records],
            "resolved_effective_snapshot": json.loads(self.resolved_effective_snapshot_json),
            "closure_plan": json.loads(self.closure_plan_json),
            "issues": list(self.issues),
        }
        if include_digest:
            payload["semantic_digest"] = self.semantic_digest
        return payload

    def to_dict(self) -> dict[str, Any]:
        return self._payload(include_digest=True)

    def to_json(self) -> str:
        return _canonical_json(self.to_dict())


@dataclass(frozen=True, slots=True)
class TransitionPlanIssuerContext:
    input_snapshot: TransitionInputSnapshot
    source_lineage: TransitionSourceLineage
    pairs: tuple[TransitionPairInput, ...]
    baseline_shapes: tuple[EffectiveShape, ...]
    closure_issuer_context: ClosureIssuerContext
    compatibility_proof: TransitionCompatibilityProof | None = None
    preparation: object | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "pairs", tuple(self.pairs))
        object.__setattr__(self, "baseline_shapes", tuple(self.baseline_shapes))
        if not isinstance(self.input_snapshot, TransitionInputSnapshot):
            raise TransitionPlanError("typed transition input is required")
        if not isinstance(self.source_lineage, TransitionSourceLineage):
            raise TransitionPlanError("typed source lineage is required")
        if any(not isinstance(item, TransitionPairInput) for item in self.pairs):
            raise TransitionPlanError("transition issuer pairs are invalid")
        if any(not isinstance(item, EffectiveShape) for item in self.baseline_shapes):
            raise TransitionPlanError("transition issuer baseline shapes are invalid")
        if not isinstance(self.closure_issuer_context, ClosureIssuerContext):
            raise TransitionPlanError("typed closure issuer context is required")
        if self.compatibility_proof is not None and not isinstance(self.compatibility_proof, TransitionCompatibilityProof):
            raise TransitionPlanError("typed replay compatibility proof is invalid")


@dataclass(frozen=True, slots=True)
class TransitionCompatibilityProof:
    capture_manifest_sha256: str
    original_source_sha256: str
    original_runtime_sha256: str
    current_runtime_sha256: str
    captured_base_plan_digest: str
    current_base_plan_digest: str
    captured_effective_plan_digest: str
    current_effective_plan_digest: str
    captured_baseline_wire_digest: str
    current_baseline_wire_digest: str
    captured_closure_wire_digest: str
    current_closure_wire_digest: str

    def __post_init__(self) -> None:
        for name in self.__dataclass_fields__:
            if not _is_digest(getattr(self, name)):
                raise TransitionPlanError(f"compatibility proof {name} must be lowercase SHA-256")

    def canonical_payload(self) -> dict[str, str]:
        return {name: getattr(self, name) for name in self.__dataclass_fields__}

    @property
    def proof_digest(self) -> str:
        return _sha256(_canonical_json(self.canonical_payload()).encode("utf-8"))

    def to_dict(self) -> dict[str, str]:
        return {
            "schema_id": "transition-compatibility-proof/v1",
            **self.canonical_payload(),
            "proof_digest": self.proof_digest,
        }


def read_transition_compatibility_proof(data: str | bytes | Mapping[str, Any]) -> TransitionCompatibilityProof:
    if isinstance(data, (str, bytes)):
        try:
            raw = json.loads(data, object_pairs_hook=_reject_duplicates, parse_constant=_reject_constant)
        except (json.JSONDecodeError, UnicodeDecodeError) as error:
            raise TransitionPlanError("compatibility proof JSON is invalid") from error
    else:
        raw = dict(data)
    fields = {"schema_id", *TransitionCompatibilityProof.__dataclass_fields__, "proof_digest"}
    if type(raw) is not dict or set(raw) != fields or raw["schema_id"] != "transition-compatibility-proof/v1":
        raise TransitionPlanError("compatibility proof fields do not match the strict schema")
    proof = TransitionCompatibilityProof(**{
        name: raw[name]
        for name in TransitionCompatibilityProof.__dataclass_fields__
    })
    if raw["proof_digest"] != proof.proof_digest:
        raise TransitionPlanError("compatibility proof digest mismatch")
    return proof


_TRANSITION_RUNTIME_SOURCE_FILES = (
    "src/core/audio_processing.py",
    "src/core/cross_vowel_transition.py",
    "src/core/effective_shape_plan.py",
    "src/core/event_adjustment.py",
    "src/core/final_morph_capture.py",
    "src/core/final_morph_closure_plan.py",
    "src/core/final_morph_plan.py",
    "src/core/final_morph_transition_plan.py",
    "src/core/morph_closure.py",
    "src/core/transition_acoustic.py",
    "src/core/pipeline.py",
    "src/vmd_writer/effective_shape_adapter.py",
    "src/vmd_writer/final_morph_closure_adapter.py",
    "src/vmd_writer/final_morph_legacy_bridge.py",
    "src/vmd_writer/final_morph_transition_adapter.py",
    "src/vmd_writer/verified_morph_output.py",
    "src/vmd_writer/writer.py",
)


def current_transition_runtime_source_sha256() -> str:
    """Hash the closed set of source files that define B2 replay semantics."""
    root = Path(__file__).resolve().parents[2]
    entries: list[list[str]] = []
    for relative in _TRANSITION_RUNTIME_SOURCE_FILES:
        path = root / relative
        try:
            file_digest = _sha256(path.read_bytes())
        except OSError as error:
            raise TransitionPlanError(f"transition runtime source is unavailable: {relative}") from error
        entries.append([relative.replace("\\", "/"), file_digest])
    return _sha256(_canonical_json(entries).encode("utf-8"))


@dataclass(frozen=True, slots=True)
class TransitionBuildResult:
    state: str
    plan: FinalMorphTransitionPlan | None
    resolution: TransitionResolution | None
    issues: tuple[str, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "issues", tuple(self.issues))
        if self.state not in {"valid", "invalid", "unavailable"}:
            raise TransitionPlanError("transition build result state is unsupported")
        if self.state == "valid" and (self.plan is None or self.resolution is None or self.issues):
            raise TransitionPlanError("valid transition build result must contain a plan and resolution")
        if any(type(item) is not str or not item for item in self.issues):
            raise TransitionPlanError("transition build issues must be non-empty text")


def transition_pair_identity(pairs: tuple[TransitionPairInput, ...]) -> str:
    """Return the canonical source identity for the ordered original event pairs."""
    if not isinstance(pairs, tuple) or any(not isinstance(item, TransitionPairInput) for item in pairs):
        raise TransitionPlanError("typed ordered transition pairs are required")
    payload = [
        {
            name: getattr(item, name)
            for name in item.__dataclass_fields__
        }
        for item in pairs
    ]
    return _sha256(_canonical_json(payload).encode("utf-8"))


def _source_binding_issues(issuer_context: TransitionPlanIssuerContext) -> tuple[str, ...]:
    if issuer_context.preparation is not None:
        from src.core.bounded_transition import bounded_source_issues
        return bounded_source_issues(issuer_context)
    input_snapshot = issuer_context.input_snapshot
    source = issuer_context.source_lineage
    legacy = issuer_context.closure_issuer_context.legacy_context
    identity = legacy.identity_context
    if identity is None or legacy.adjustment_snapshot is None:
        return ("source_identity_unavailable",)
    issues: list[str] = []
    if (
        source.run_id != input_snapshot.run_id
        or source.analysis_generation != input_snapshot.analysis_generation
        or source.input_mode != input_snapshot.input_mode
        or source.analysis_wav_sha256 != input_snapshot.analysis_wav_sha256
        or source.policy_digest != input_snapshot.policy.policy_digest
        or source.parameter_digest != input_snapshot.policy.policy_digest
        or source.acoustic_evidence_digest != input_snapshot.acoustic.content_digest
        or source.base_plan_digest != input_snapshot.base_plan_digest
        or source.manual_revision != input_snapshot.manual_revision
        or identity.base_plan_digest != input_snapshot.base_plan_digest
        or identity.manual_revision != input_snapshot.manual_revision
        or source.effective_plan_digest != identity.effective_plan_digest
        or source.manual_snapshot_digest != snapshot_digest(legacy.adjustment_snapshot)
        or source.output_mapping != identity.output_mapping
        or (identity.resolved_profile_id is not None and source.resolved_profile_id != identity.resolved_profile_id)
        or source.origin_identity != f"{source.run_id}/{source.analysis_generation}"
    ):
        issues.append("source_input_binding_mismatch")
    if identity.source_run_id != input_snapshot.run_id or str(identity.analysis_generation) != input_snapshot.analysis_generation:
        issues.append("legacy_source_identity_mismatch")
    if source.pair_identity != transition_pair_identity(issuer_context.pairs):
        issues.append("source_pair_identity_mismatch")
    proof = issuer_context.compatibility_proof
    if source.source_kind == "live_analysis":
        if proof is not None:
            issues.append("live_lineage_contains_replay_compatibility_proof")
    elif source.source_kind == "replayed_capture":
        if proof is None:
            issues.append("replay_compatibility_proof_missing")
        elif (
            source.capture_manifest_sha256 != proof.capture_manifest_sha256
            or source.original_source_sha256 != proof.original_source_sha256
            or source.original_runtime_sha256 != proof.original_runtime_sha256
            or source.current_runtime_sha256 != proof.current_runtime_sha256
            or source.compatibility_proof_digest != proof.proof_digest
            or proof.captured_base_plan_digest != source.base_plan_digest
            or proof.current_base_plan_digest != input_snapshot.base_plan_digest
            or proof.captured_effective_plan_digest != source.effective_plan_digest
            or proof.current_effective_plan_digest != identity.effective_plan_digest
        ):
            issues.append("replay_compatibility_proof_binding_mismatch")
        else:
            try:
                if proof.current_runtime_sha256 != current_transition_runtime_source_sha256():
                    issues.append("replay_current_runtime_source_mismatch")
            except (OSError, TransitionPlanError):
                issues.append("replay_current_runtime_source_unavailable")
    return tuple(issues)


def _transitioned_closure_baseline_points(
    original: ClosureIssuerContext,
    resolution: TransitionResolution,
) -> tuple[tuple[int, str, float], ...]:
    applied = tuple(item for item in resolution.decisions if item.state == "applied")
    if not applied:
        return original.baseline_points
    points = {
        (frame, semantic): float(value)
        for frame, semantic, value in original.baseline_points
    }
    protected = {
        (item.frame_no, item.semantic_morph)
        for item in original.protected_points
    }
    boundaries = {
        (item.frame_no, item.semantic_morph)
        for item in original.explicit_requirement_boundaries
    }
    moved_targets: set[tuple[int, str]] = set()
    for decision in applied:
        if (
            decision.start_advance_frames != 1
            or decision.candidate_start_frame != decision.baseline_start_frame - 1
            or decision.next_morph not in SEMANTIC_VOWEL_ORDER
        ):
            raise TransitionPlanError("applied transition does not describe one structural-start advance")
        old_key = (decision.baseline_start_frame, decision.next_morph)
        new_key = (decision.candidate_start_frame, decision.next_morph)
        if old_key in protected or old_key in boundaries or new_key in protected or new_key in boundaries:
            raise TransitionPlanError("applied transition collides with a protected closure baseline point")
        if points.get(old_key) != 0.0:
            raise TransitionPlanError("closure baseline lacks the original structural start zero")
        if new_key in moved_targets:
            raise TransitionPlanError("applied transitions share a structural-start baseline point")
        existing_new_value = points.get(new_key)
        if existing_new_value is not None and existing_new_value != 0.0:
            raise TransitionPlanError("closure baseline has a non-zero point at the advanced start")
        points.pop(old_key)
        points.setdefault(new_key, 0.0)
        moved_targets.add(new_key)
    return tuple(
        (frame, semantic, value)
        for (frame, semantic), value in sorted(
            points.items(),
            key=lambda item: (item[0][0], SEMANTIC_VOWEL_ORDER.index(item[0][1])),
        )
    )


def _transition_closure_issuer_context(
    issuer_context: TransitionPlanIssuerContext,
    resolution: TransitionResolution,
) -> tuple[ClosureIssuerContext, object, str]:
    """Re-issue the MS31 closure source against independently resolved transition shapes."""
    if issuer_context.preparation is not None:
        from src.core.bounded_transition import verify_bounded_issuer
        resolved = verify_bounded_issuer(issuer_context, resolution)
        return issuer_context.closure_issuer_context, resolved, effective_plan_snapshot_digest(resolved)
    binding_issues = _source_binding_issues(issuer_context)
    if binding_issues:
        raise TransitionPlanError(";".join(binding_issues))
    input_snapshot = issuer_context.input_snapshot
    original = issuer_context.closure_issuer_context
    from src.vmd_writer.final_morph_legacy_bridge import capture_issuer_evidence, replay_effective_shape_plan

    try:
        resolved, _base_input, _issuer_evidence, _closure_identity, _points, _shapes = _verify_source_context(original)
    except (AttributeError, TypeError, ValueError, RuntimeError, OverflowError) as error:
        raise TransitionPlanError("original closure source could not be admitted") from error
    if tuple(getattr(resolved, "shapes", ())) != issuer_context.baseline_shapes:
        raise TransitionPlanError("transition baseline shapes differ from re-resolved source")
    proof = issuer_context.compatibility_proof
    if issuer_context.source_lineage.source_kind == "replayed_capture":
        if proof is None:
            raise TransitionPlanError("replayed capture compatibility proof is missing")
        try:
            current_replay = replay_effective_shape_plan(original.legacy_context)
            current_baseline_wire_digest = _sha256(
                _canonical_json([list(item) for item in current_replay.baseline_wire_values]).encode("utf-8")
            )
            current_closure = build_closure_candidate(original)
            if current_closure.state != "valid" or current_closure.plan is None:
                raise TransitionPlanError("current replay closure baseline is invalid")
            current_runtime = current_transition_runtime_source_sha256()
        except (AttributeError, TypeError, ValueError, RuntimeError, OverflowError) as error:
            raise TransitionPlanError("replayed capture compatibility could not be rechecked") from error
        if (
            proof.current_runtime_sha256 != current_runtime
            or proof.current_base_plan_digest != input_snapshot.base_plan_digest
            or proof.current_effective_plan_digest != effective_plan_snapshot_digest(resolved)
            or proof.current_baseline_wire_digest != current_baseline_wire_digest
            or proof.captured_baseline_wire_digest != proof.current_baseline_wire_digest
            or proof.current_closure_wire_digest != current_closure.plan.wire_digest
            or proof.captured_closure_wire_digest != proof.current_closure_wire_digest
        ):
            raise TransitionPlanError("replayed capture is not compatible with the current baseline")
    try:
        expected_pairs = build_transition_pairs_from_effective_plan(resolved, fps=input_snapshot.policy.fps)
    except (AttributeError, TypeError, ValueError, RuntimeError, OverflowError) as error:
        raise TransitionPlanError("transition source pairs could not be re-derived") from error
    if expected_pairs != issuer_context.pairs:
        raise TransitionPlanError("transition pairs differ from original event source")
    resolution_result = validate_transition_resolution(
        policy=input_snapshot.policy,
        acoustic_snapshot=input_snapshot.acoustic,
        pairs=expected_pairs,
        baseline_shapes=tuple(getattr(resolved, "shapes", ())),
        resolution=resolution,
    )
    if resolution_result.state != "valid":
        raise TransitionPlanError("transition resolution is not independently valid")
    try:
        transitioned = apply_transition_resolution_to_effective_plan(resolved, resolution)
        resolved_digest = effective_plan_snapshot_digest(transitioned)
        original_identity = original.legacy_context.identity_context
        transitioned_identity = replace(original_identity, effective_plan_digest=resolved_digest)
        transitioned_evidence = capture_issuer_evidence(
            transitioned,
            source_run_id=transitioned_identity.source_run_id,
            analysis_generation=transitioned_identity.analysis_generation,
            manual_revision=transitioned_identity.manual_revision,
        )
        transitioned_legacy = replace(
            original.legacy_context,
            identity_context=transitioned_identity,
            effective_plan_snapshot=transitioned,
            issuer_evidence=transitioned_evidence,
            replay_evidence=None,
        )
        replay = replay_effective_shape_plan(transitioned_legacy)
    except (AttributeError, TypeError, ValueError, RuntimeError, OverflowError) as error:
        raise TransitionPlanError("transition-resolved closure baseline could not be replayed") from error
    if replay.capture_issues:
        raise TransitionPlanError("transition-resolved closure replay contains capture issues")
    closure_source = ClosureIssuerContext(
        legacy_context=transitioned_legacy,
        baseline_points=_transitioned_closure_baseline_points(original, resolution),
        protected_points=original.protected_points,
        explicit_requirement_boundaries=original.explicit_requirement_boundaries,
        transition_admission=TransitionClosureAdmission(
            original_issuer_context=original,
            policy=input_snapshot.policy,
            acoustic_snapshot=input_snapshot.acoustic,
            pairs=expected_pairs,
            resolution=resolution,
        ),
    )
    return closure_source, transitioned, resolved_digest


def build_transition_candidate(
    issuer_context: TransitionPlanIssuerContext | None,
    resolution: TransitionResolution | None,
) -> TransitionBuildResult:
    if issuer_context is None or resolution is None:
        return TransitionBuildResult("unavailable", None, None, ("transition_build_input_missing",))
    if not isinstance(issuer_context, TransitionPlanIssuerContext) or not isinstance(resolution, TransitionResolution):
        return TransitionBuildResult("invalid", None, resolution if isinstance(resolution, TransitionResolution) else None, ("transition_build_input_invalid",))
    binding_issues = _source_binding_issues(issuer_context)
    if binding_issues:
        return TransitionBuildResult("invalid", None, resolution, binding_issues)
    try:
        closure_source, transitioned, resolved_digest = _transition_closure_issuer_context(issuer_context, resolution)
        closure_result: ClosureBuildResult = build_closure_candidate(closure_source)
    except (AttributeError, TypeError, ValueError, RuntimeError, OverflowError) as error:
        return TransitionBuildResult("invalid", None, resolution, (f"transition_closure_source_invalid:{type(error).__name__}",))
    if closure_result.state != "valid" or closure_result.plan is None:
        return TransitionBuildResult(
            closure_result.state if closure_result.state in {"invalid", "unavailable"} else "invalid",
            None,
            resolution,
            tuple(f"closure:{item.reason_code}" for item in closure_result.issues) or ("transition_closure_build_failed",),
        )
    input_snapshot = issuer_context.input_snapshot
    snapshot_json = transition_effective_snapshot_json(
        resolution,
        baseline_effective_digest=issuer_context.source_lineage.effective_plan_digest,
    )
    identity = TransitionPlanIdentity(
        source_lineage=issuer_context.source_lineage,
        transition_input_digest=input_snapshot.input_digest,
        policy_digest=input_snapshot.policy.policy_digest,
        acoustic_digest=input_snapshot.acoustic.content_digest,
        baseline_effective_digest=issuer_context.source_lineage.effective_plan_digest,
        resolved_effective_digest=resolved_digest,
        resolved_effective_snapshot_sha256=_sha256(snapshot_json.encode("utf-8")),
        resolution_digest=resolution.resolution_digest,
        closure_semantic_digest=closure_result.plan.semantic_digest,
        closure_wire_digest=closure_result.plan.wire_digest,
    )
    try:
        plan = create_final_morph_transition_plan(
            identity_context=identity,
            transition_records=resolution.decisions,
            resolved_effective_snapshot_json=snapshot_json,
            closure_plan=closure_result.plan,
            schema_id=FINAL_MORPH_TRANSITION_SCHEMA_V2 if resolution.schedule is not None else FINAL_MORPH_TRANSITION_SCHEMA,
        )
    except (ClosurePlanError, TypeError, ValueError, OverflowError) as error:
        return TransitionBuildResult("invalid", None, resolution, (f"transition_envelope_invalid:{type(error).__name__}",))
    validation = validate_transition_plan(plan, issuer_context=issuer_context, resolution=resolution)
    if validation.state != "valid":
        return TransitionBuildResult("invalid", None, resolution, validation.issues or ("transition_candidate_failed_validation",))
    return TransitionBuildResult("valid", plan, resolution, ())


def validate_transition_plan(
    plan: FinalMorphTransitionPlan | None,
    *,
    issuer_context: TransitionPlanIssuerContext | None,
    resolution: TransitionResolution | None,
) -> TransitionValidationResult:
    if issuer_context is not None and issuer_context.preparation is not None:
        from src.core.bounded_transition import validate_bounded_plan
        return validate_bounded_plan(plan, issuer_context, resolution)
    if plan is None or issuer_context is None or resolution is None:
        return TransitionValidationResult("unavailable", ("transition_validation_input_missing",), None)
    if (
        not isinstance(plan, FinalMorphTransitionPlan)
        or not isinstance(issuer_context, TransitionPlanIssuerContext)
        or not isinstance(resolution, TransitionResolution)
    ):
        return TransitionValidationResult("invalid", ("transition_validation_input_invalid",), None)
    issues: list[str] = []
    identity = plan.identity_context
    source = issuer_context.source_lineage
    input_snapshot = issuer_context.input_snapshot
    if plan.state != "valid":
        return TransitionValidationResult(plan.state, plan.issues or ("transition_candidate_not_valid",), None)
    if source != identity.source_lineage:
        issues.append("source_lineage_mismatch")
    try:
        issues.extend(_source_binding_issues(issuer_context))
    except (AttributeError, TypeError, ValueError, RuntimeError, OverflowError) as error:
        issues.append(f"transition_source_binding_invalid:{type(error).__name__}")
    if (
        identity.transition_input_digest != input_snapshot.input_digest
        or identity.policy_digest != input_snapshot.policy.policy_digest
        or identity.acoustic_digest != input_snapshot.acoustic.content_digest
        or identity.baseline_effective_digest != source.effective_plan_digest
    ):
        issues.append("outer_identity_binding_mismatch")
    if resolution.resolution_digest != identity.resolution_digest:
        issues.append("resolution_digest_mismatch")
    try:
        original_resolved, _base_input, _evidence, _closure_identity, _source_points, _shapes = _verify_source_context(
            issuer_context.closure_issuer_context
        )
        expected_pairs = build_transition_pairs_from_effective_plan(
            original_resolved,
            fps=input_snapshot.policy.fps,
        )
        if tuple(getattr(original_resolved, "shapes", ())) != issuer_context.baseline_shapes:
            issues.append("baseline_shapes_source_mismatch")
        if expected_pairs != issuer_context.pairs:
            issues.append("transition_pairs_source_mismatch")
    except (AttributeError, TypeError, ValueError, RuntimeError, OverflowError) as error:
        expected_pairs = ()
        issues.append(f"transition_source_unavailable:{type(error).__name__}")
    resolution_result = validate_transition_resolution(
        policy=input_snapshot.policy,
        acoustic_snapshot=input_snapshot.acoustic,
        pairs=expected_pairs,
        baseline_shapes=issuer_context.baseline_shapes,
        resolution=resolution,
    )
    if resolution_result.state != "valid":
        issues.extend(resolution_result.issues or ("transition_resolution_invalid",))
    if plan.transition_records != resolution.decisions:
        issues.append("outer_transition_records_mismatch")
    expected_snapshot = transition_effective_snapshot_json(
        resolution,
        baseline_effective_digest=identity.baseline_effective_digest,
    )
    if plan.resolved_effective_snapshot_json != expected_snapshot:
        issues.append("resolved_effective_snapshot_mismatch")
    try:
        closure_issuer, _transitioned, resolved_digest = _transition_closure_issuer_context(issuer_context, resolution)
        if resolved_digest != identity.resolved_effective_digest:
            issues.append("resolved_effective_digest_mismatch")
        closure = closure_plan_from_json(plan.closure_plan_json)
        validate_closure_plan_integrity(closure)
        if closure.identity_context.effective_plan_digest != identity.resolved_effective_digest:
            issues.append("closure_resolved_effective_identity_mismatch")
        if closure.semantic_digest != identity.closure_semantic_digest or closure.wire_digest != identity.closure_wire_digest:
            issues.append("closure_subproof_digest_mismatch")
        closure_result = validate_closure_plan(closure, closure_issuer)
        if closure_result.state != "valid":
            issues.extend(f"closure:{item.reason_code}" for item in closure_result.issues)
    except (ClosurePlanError, TypeError, ValueError) as error:
        issues.append(f"closure_subproof_invalid:{type(error).__name__}")
    return TransitionValidationResult(
        "invalid" if issues else "valid",
        tuple(sorted(set(issues))),
        resolution.resolution_digest if not issues else None,
    )


def _digest_plan(payload: Mapping[str, Any]) -> str:
    return _sha256(_canonical_json(payload).encode("utf-8"))


def _canonicalize_snapshot_json(value: str) -> str:
    if type(value) is not str:
        raise TransitionPlanError("resolved effective snapshot must be JSON text")
    try:
        raw = json.loads(value, object_pairs_hook=_reject_duplicates, parse_constant=_reject_constant)
    except (json.JSONDecodeError, UnicodeDecodeError) as error:
        raise TransitionPlanError("resolved effective snapshot JSON is invalid") from error
    if type(raw) is not dict:
        raise TransitionPlanError("resolved effective snapshot root must be an object")
    return _canonical_json(raw)


def _reject_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise TransitionPlanError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _reject_constant(value: str) -> None:
    raise TransitionPlanError(f"invalid numeric constant: {value}")


def create_final_morph_transition_plan(
    *,
    identity_context: TransitionPlanIdentity,
    transition_records: tuple[TransitionDecision, ...],
    resolved_effective_snapshot_json: str,
    closure_plan: ClosurePlan,
    state: str = "valid",
    issues: tuple[str, ...] = (),
    schema_id: str = FINAL_MORPH_TRANSITION_SCHEMA,
) -> FinalMorphTransitionPlan:
    if not isinstance(closure_plan, ClosurePlan):
        raise TransitionPlanError("typed closure plan is required")
    validate_closure_plan_integrity(closure_plan)
    provisional = {
        "schema_id": schema_id,
        "state": state,
        "identity_context": identity_context.to_dict(),
        "transition_records": [_decision_dict(item) for item in transition_records],
        "resolved_effective_snapshot": json.loads(_canonicalize_snapshot_json(resolved_effective_snapshot_json)),
        "closure_plan": closure_plan.to_dict(),
        "issues": list(issues),
    }
    semantic_digest = _digest_plan(provisional)
    return FinalMorphTransitionPlan(
        state=state,
        identity_context=identity_context,
        transition_records=transition_records,
        resolved_effective_snapshot_json=resolved_effective_snapshot_json,
        closure_plan_json=closure_plan.to_json(),
        issues=issues,
        semantic_digest=semantic_digest,
        schema_id=schema_id,
    )


def read_final_morph_transition_plan(data: str | bytes | Mapping[str, Any]) -> FinalMorphTransitionPlan:
    if isinstance(data, (str, bytes)):
        try:
            raw = json.loads(data, object_pairs_hook=_reject_duplicates, parse_constant=_reject_constant)
        except (json.JSONDecodeError, UnicodeDecodeError) as error:
            raise TransitionPlanError("transition plan JSON is invalid") from error
    else:
        raw = dict(data)
    fields = {
        "schema_id", "state", "identity_context", "transition_records", "resolved_effective_snapshot",
        "closure_plan", "issues", "semantic_digest",
    }
    if type(raw) is not dict or set(raw) != fields or raw["schema_id"] not in {FINAL_MORPH_TRANSITION_SCHEMA, FINAL_MORPH_TRANSITION_SCHEMA_V2}:
        raise TransitionPlanError("transition plan fields do not match the strict schema")
    identity_raw = raw["identity_context"]
    identity_fields = {
        "source_lineage", "transition_input_digest", "policy_digest", "acoustic_digest",
        "baseline_effective_digest", "resolved_effective_digest", "resolved_effective_snapshot_sha256",
        "resolution_digest", "closure_semantic_digest", "closure_wire_digest",
    }
    if type(identity_raw) is not dict or set(identity_raw) != identity_fields:
        raise TransitionPlanError("transition identity fields do not match the strict schema")
    identity = TransitionPlanIdentity(
        source_lineage=read_transition_source_lineage(identity_raw["source_lineage"]),
        transition_input_digest=identity_raw["transition_input_digest"],
        policy_digest=identity_raw["policy_digest"],
        acoustic_digest=identity_raw["acoustic_digest"],
        baseline_effective_digest=identity_raw["baseline_effective_digest"],
        resolved_effective_digest=identity_raw["resolved_effective_digest"],
        resolved_effective_snapshot_sha256=identity_raw["resolved_effective_snapshot_sha256"],
        resolution_digest=identity_raw["resolution_digest"],
        closure_semantic_digest=identity_raw["closure_semantic_digest"],
        closure_wire_digest=identity_raw["closure_wire_digest"],
    )
    if type(raw["transition_records"]) is not list or type(raw["issues"]) is not list:
        raise TransitionPlanError("transition records and issues must be arrays")
    if type(raw["resolved_effective_snapshot"]) is not dict or type(raw["closure_plan"]) is not dict:
        raise TransitionPlanError("resolved snapshot and closure plan must be objects")
    snapshot_json = _canonical_json(raw["resolved_effective_snapshot"])
    closure_json = _canonical_json(raw["closure_plan"])
    plan = FinalMorphTransitionPlan(
        state=raw["state"],
        identity_context=identity,
        transition_records=tuple(_strict_decision(item) for item in raw["transition_records"]),
        resolved_effective_snapshot_json=snapshot_json,
        closure_plan_json=closure_json,
        issues=tuple(raw["issues"]),
        semantic_digest=raw["semantic_digest"],
        schema_id=raw["schema_id"],
    )
    return plan

