from __future__ import annotations

import hashlib
import json
import math
import os
import re
from dataclasses import dataclass, replace

from src.core.final_morph_capture import build_capture_baseline, snapshot_digest
from src.core.final_morph_plan import (
    CURVE_POLICY_ID as LEGACY_CURVE_POLICY_ID,
    FinalMorphFullSnapshotIssuerContext,
    FinalMorphIdentityContext,
    effective_plan_snapshot_digest,
)
from src.core.final_morph_plan import POLICY_ID as LEGACY_NUMERIC_POLICY_ID
from src.core.final_morph_capture import CROSSFADE_POLICY_ID
from src.core.final_morph_closure_plan import (
    ClosureBuildResult,
    ClosureContract,
    ClosureIdentityContext,
    ClosureIssue,
    ClosurePlanError,
    ClosureRestriction,
    closure_plan_from_json,
)
from src.core.cross_vowel_transition import (
    TransitionInputSnapshot,
    TransitionPairInput,
    TransitionResolution,
    TransitionSourceLineage,
    build_transition_pairs_from_effective_plan,
    resolve_cross_vowel_transition,
)
from src.core.transition_default_policy import DefaultTransitionSelection
from src.core.final_morph_transition_plan import (
    FinalMorphTransitionPlan,
    TransitionPlanIssuerContext,
    TransitionValidationResult,
    build_transition_candidate,
    transition_pair_identity,
    validate_transition_plan,
)
from src.core.morph_closure import (
    ClosureExplicitBoundary,
    ClosureIssuerContext,
    ClosureProtectedPoint,
    build_closure_candidate,
)
from src.core.morph_name_sets import SEMANTIC_VOWEL_ORDER, validate_output_morph_names
from src.core.final_output_state import FinalOutputOrigin
from src.vmd_writer.final_morph_closure_adapter import (
    ClosureProjection,
    project_validated_closure_candidate,
)
from src.vmd_writer.final_morph_transition_adapter import (
    TransitionProjection,
    project_validated_transition_plan,
)
from src.vmd_writer.final_morph_legacy_bridge import capture_issuer_evidence
from src.core.transition_evaluation import TransitionEvaluationRequest


_EVENT_SOURCE_PATTERN = re.compile(r"source:event:(0|[1-9][0-9]*)\Z")


def _require_digest(value: object, name: str) -> str:
    if (
        type(value) is not str
        or len(value) != 64
        or any(char not in "0123456789abcdef" for char in value)
    ):
        raise ValueError(f"{name} must be a lowercase SHA-256 digest")
    return value


def _require_text(value: object, name: str, *, allow_empty: bool = False) -> str:
    if type(value) is not str or (not allow_empty and not value):
        raise ValueError(f"{name} must be text")
    return value


def _require_non_negative_int(value: object, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(f"{name} must be a non-negative integer")
    return value


def canonical_transition_generation_token(value: object) -> str:
    """Map an accepted integer generation to B2's canonical decimal string."""
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError("accepted analysis generation must be a non-negative integer")
    return str(value)


def _normalize_path(value: str | None) -> str | None:
    if value is None:
        return None
    return os.path.normcase(os.path.abspath(os.path.normpath(value)))


def build_closure_issuer_context(
    *,
    origin: FinalOutputOrigin,
    base_input: object,
    adjustment_snapshot: object,
    effective_plan: object,
    manual_revision: int,
    resolved_profile_id: str | None,
    output_morph_names: tuple[str, ...],
    protected_points: tuple[ClosureProtectedPoint, ...] = (),
    explicit_requirement_boundaries: tuple[ClosureExplicitBoundary, ...] = (),
) -> ClosureIssuerContext:
    """Build a complete B2 issuer from one accepted, immutable UI snapshot."""
    if not isinstance(origin, FinalOutputOrigin) or origin.base_plan_digest is None:
        raise ValueError("an accepted analysis origin is required")
    _require_non_negative_int(manual_revision, "manual_revision")
    names = validate_output_morph_names(output_morph_names)
    output_mapping = tuple(zip(SEMANTIC_VOWEL_ORDER, names))
    identity = FinalMorphIdentityContext(
        source_run_id=origin.source_run_id,
        analysis_generation=origin.analysis_generation,
        base_plan_digest=origin.base_plan_digest,
        effective_plan_digest=effective_plan_snapshot_digest(effective_plan),
        manual_revision=manual_revision,
        resolved_profile_id=resolved_profile_id,
        output_mapping=output_mapping,
        numeric_policy_id=LEGACY_NUMERIC_POLICY_ID,
        curve_policy_id=LEGACY_CURVE_POLICY_ID,
        silence_policy_id=_require_text(
            getattr(effective_plan, "silence_policy", None), "silence_policy_id"
        ),
        crossfade_policy_id=CROSSFADE_POLICY_ID,
    )
    evidence = capture_issuer_evidence(
        effective_plan,
        source_run_id=origin.source_run_id,
        analysis_generation=origin.analysis_generation,
        manual_revision=manual_revision,
    )
    legacy_context = FinalMorphFullSnapshotIssuerContext(
        input_kind="captured_snapshot",
        identity_context=identity,
        base_input=base_input,
        adjustment_snapshot=adjustment_snapshot,
        effective_plan_snapshot=effective_plan,
        issuer_evidence=evidence,
    )
    baseline = build_capture_baseline(
        effective_plan,
        output_morph_names=names,
    )
    baseline_points = tuple(
        sorted(
            (
                (
                    int(item["frame_no"]),
                    _require_text(item["semantic_morph"], "semantic_morph"),
                    float.fromhex(_require_text(item["value_hex"], "value_hex")),
                )
                for item in baseline["points"]
            ),
            key=lambda item: (item[0], SEMANTIC_VOWEL_ORDER.index(item[1])),
        )
    )
    return ClosureIssuerContext(
        legacy_context=legacy_context,
        baseline_points=baseline_points,
        protected_points=protected_points,
        explicit_requirement_boundaries=explicit_requirement_boundaries,
    )


@dataclass(frozen=True, slots=True)
class FinalOutputInputIdentity:
    source_run_id: str
    job_id: int
    analysis_generation: int
    manual_revision: int
    input_mode: str
    input_binding_digest: str
    source_audio_path: str | None
    analysis_wav_path: str | None
    normalized_text_path: str | None
    base_plan_digest: str
    adjustment_snapshot_digest: str
    effective_plan_digest: str
    resolved_profile_id: str | None
    output_mapping: tuple[tuple[str, str], ...]
    numeric_policy_id: str
    curve_policy_id: str
    silence_policy_id: str
    crossfade_policy_id: str
    closure_contract_digest: str
    baseline_digest: str
    transition_input_digest: str | None = None
    application_binding_digest: str | None = None
    cleanup_input_digest: str | None = None
    cleanup_application_binding_digest: str | None = None

    def __post_init__(self) -> None:
        _require_text(self.source_run_id, "source_run_id")
        _require_non_negative_int(self.job_id, "job_id")
        _require_non_negative_int(self.analysis_generation, "analysis_generation")
        _require_non_negative_int(self.manual_revision, "manual_revision")
        if self.input_mode not in {"text_audio", "voice_only"}:
            raise ValueError("input_mode is unsupported")
        for name in (
            "input_binding_digest",
            "base_plan_digest",
            "adjustment_snapshot_digest",
            "effective_plan_digest",
            "closure_contract_digest",
            "baseline_digest",
        ):
            _require_digest(getattr(self, name), name)
        if self.transition_input_digest is not None:
            _require_digest(self.transition_input_digest, "transition_input_digest")
        if self.application_binding_digest is not None:
            _require_digest(self.application_binding_digest, "application_binding_digest")
        if self.cleanup_input_digest is not None:
            _require_digest(self.cleanup_input_digest, "cleanup_input_digest")
        if self.cleanup_application_binding_digest is not None:
            _require_digest(
                self.cleanup_application_binding_digest,
                "cleanup_application_binding_digest",
            )
        for name in ("source_audio_path", "analysis_wav_path", "normalized_text_path"):
            value = getattr(self, name)
            if value is not None:
                _require_text(value, name)
        if self.resolved_profile_id is not None:
            _require_text(self.resolved_profile_id, "resolved_profile_id")
        if (
            not isinstance(self.output_mapping, tuple)
            or any(not isinstance(item, tuple) or len(item) != 2 for item in self.output_mapping)
            or tuple(item[0] for item in self.output_mapping) != SEMANTIC_VOWEL_ORDER
        ):
            raise ValueError("output_mapping must use fixed semantic vowel order")
        for semantic, output_name in self.output_mapping:
            _require_text(semantic, "output_mapping semantic")
            _require_text(output_name, "output_mapping name")
        for name in (
            "numeric_policy_id",
            "curve_policy_id",
            "silence_policy_id",
            "crossfade_policy_id",
        ):
            _require_text(getattr(self, name), name)

    @property
    def semantic_binding(self) -> str:
        payload = {
            "source_run_id": self.source_run_id,
            "job_id": self.job_id,
            "analysis_generation": self.analysis_generation,
            "manual_revision": self.manual_revision,
            "input_mode": self.input_mode,
            "input_binding_digest": self.input_binding_digest,
            "source_audio_path": self.source_audio_path,
            "analysis_wav_path": self.analysis_wav_path,
            "normalized_text_path": self.normalized_text_path,
            "base_plan_digest": self.base_plan_digest,
            "adjustment_snapshot_digest": self.adjustment_snapshot_digest,
            "effective_plan_digest": self.effective_plan_digest,
            "resolved_profile_id": self.resolved_profile_id,
            "output_mapping": self.output_mapping,
            "numeric_policy_id": self.numeric_policy_id,
            "curve_policy_id": self.curve_policy_id,
            "silence_policy_id": self.silence_policy_id,
            "crossfade_policy_id": self.crossfade_policy_id,
            "closure_contract_digest": self.closure_contract_digest,
            "baseline_digest": self.baseline_digest,
        }
        if self.transition_input_digest is not None:
            payload["transition_input_digest"] = self.transition_input_digest
        if self.application_binding_digest is not None:
            payload["application_binding_digest"] = self.application_binding_digest
        if self.cleanup_input_digest is not None:
            payload["cleanup_input_digest"] = self.cleanup_input_digest
        if self.cleanup_application_binding_digest is not None:
            payload["cleanup_application_binding_digest"] = self.cleanup_application_binding_digest
        encoded = json.dumps(
            payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")
        ).encode("utf-8")
        return hashlib.sha256(encoded).hexdigest()


@dataclass(frozen=True, slots=True)
class FinalOutputIdentity:
    input_identity: FinalOutputInputIdentity
    plan_schema_id: str
    curve_policy_id: str
    semantic_digest: str
    wire_digest: str

    def __post_init__(self) -> None:
        if not isinstance(self.input_identity, FinalOutputInputIdentity):
            raise ValueError("input_identity must be FinalOutputInputIdentity")
        _require_text(self.plan_schema_id, "plan_schema_id")
        _require_text(self.curve_policy_id, "curve_policy_id")
        _require_digest(self.semantic_digest, "semantic_digest")
        _require_digest(self.wire_digest, "wire_digest")

    @property
    def binding_digest(self) -> str:
        payload = {
            "input_binding": self.input_identity.semantic_binding,
            "plan_schema_id": self.plan_schema_id,
            "curve_policy_id": self.curve_policy_id,
            "semantic_digest": self.semantic_digest,
            "wire_digest": self.wire_digest,
        }
        return hashlib.sha256(
            json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()


@dataclass(frozen=True, slots=True)
class SourceEventMetadata:
    base_event_index: int
    vowel: str
    start_frame: int
    peak_frame: int
    end_frame: int
    peak_value: float
    group_event_indices: tuple[int, ...] = ()
    shape_internal_source_tokens: tuple[int, ...] = ()
    long_vowel_source_event_index: int | None = None
    long_vowel_role: str | None = None
    long_vowel_mode: str | None = None

    def __post_init__(self) -> None:
        _require_non_negative_int(self.base_event_index, "base_event_index")
        if self.vowel not in SEMANTIC_VOWEL_ORDER:
            raise ValueError("event vowel is unsupported")
        for name in ("start_frame", "peak_frame", "end_frame"):
            _require_non_negative_int(getattr(self, name), name)
        if not self.start_frame <= self.peak_frame <= self.end_frame:
            raise ValueError("event frames must satisfy start <= peak <= end")
        if (
            isinstance(self.peak_value, bool)
            or not isinstance(self.peak_value, (int, float))
            or not math.isfinite(float(self.peak_value))
            or self.peak_value < 0
        ):
            raise ValueError("peak_value must be finite and non-negative")
        group_indices = tuple(self.group_event_indices) or (self.base_event_index,)
        if (
            self.base_event_index not in group_indices
            or len(group_indices) != len(set(group_indices))
            or any(
                isinstance(item, bool) or not isinstance(item, int) or item < 0
                for item in group_indices
            )
        ):
            raise ValueError("group_event_indices must uniquely include this event")
        object.__setattr__(self, "group_event_indices", group_indices)
        tokens = tuple(self.shape_internal_source_tokens)
        if any(
            isinstance(item, bool) or not isinstance(item, int)
            for item in tokens
        ):
            raise ValueError("shape_internal_source_tokens must be integers")
        object.__setattr__(self, "shape_internal_source_tokens", tokens)
        if self.long_vowel_source_event_index is not None:
            _require_non_negative_int(
                self.long_vowel_source_event_index,
                "long_vowel_source_event_index",
            )
        if self.long_vowel_role not in {
            None,
            "source",
            "continuation",
            "terminal",
            "continuation_terminal",
        }:
            raise ValueError("long_vowel_role is unsupported")
        if self.long_vowel_mode not in {None, "hold", "decay"}:
            raise ValueError("long_vowel_mode is unsupported")
        if (self.long_vowel_role is None) != (
            self.long_vowel_source_event_index is None or self.long_vowel_mode is None
        ):
            raise ValueError("long-vowel selection metadata is incomplete")


@dataclass(frozen=True, slots=True)
class RestrictionEventTarget:
    restriction: ClosureRestriction
    event: SourceEventMetadata


@dataclass(frozen=True, slots=True)
class TransitionSharedOutputBinding:
    evaluation_request: TransitionEvaluationRequest | None
    input_snapshot: TransitionInputSnapshot
    issuer_context: TransitionPlanIssuerContext
    resolution: TransitionResolution
    plan: FinalMorphTransitionPlan
    validation: TransitionValidationResult
    projection: TransitionProjection
    default_selection: DefaultTransitionSelection | None = None

    def __post_init__(self) -> None:
        if self.evaluation_request is not None and not isinstance(
            self.evaluation_request, TransitionEvaluationRequest
        ):
            raise ValueError("transition evaluation request is invalid")
        if self.default_selection is not None and not isinstance(
            self.default_selection, DefaultTransitionSelection
        ):
            raise ValueError("default transition selection is invalid")
        if (self.evaluation_request is None) == (self.default_selection is None):
            raise ValueError("transition binding needs exactly one request or default selection")
        if not isinstance(self.input_snapshot, TransitionInputSnapshot):
            raise ValueError("transition input snapshot is invalid")
        if not isinstance(self.issuer_context, TransitionPlanIssuerContext):
            raise ValueError("transition issuer context is invalid")
        if not isinstance(self.resolution, TransitionResolution):
            raise ValueError("transition resolution is invalid")
        if not isinstance(self.plan, FinalMorphTransitionPlan):
            raise ValueError("transition plan is invalid")
        if not isinstance(self.validation, TransitionValidationResult):
            raise ValueError("transition validation is invalid")
        if self.validation.state != "valid":
            raise ValueError("transition binding requires a valid outer plan")
        if not isinstance(self.projection, TransitionProjection):
            raise ValueError("transition projection is invalid")
        expected_policy = (
            self.evaluation_request.policy
            if self.evaluation_request is not None
            else self.default_selection.binding.policy
        )
        if (
            self.issuer_context.input_snapshot != self.input_snapshot
            or expected_policy != self.input_snapshot.policy
            or self.plan.identity_context.transition_input_digest
            != self.input_snapshot.input_digest
            or self.validation.resolution_digest != self.resolution.resolution_digest
            or self.projection.transition_plan_digest != self.plan.semantic_digest
        ):
            raise ValueError("transition binding components disagree")


@dataclass(frozen=True, slots=True)
class SharedFinalOutputContext:
    input_identity: FinalOutputInputIdentity
    identity: FinalOutputIdentity
    issuer_context: ClosureIssuerContext
    candidate: ClosureBuildResult
    projection: ClosureProjection
    source_events: tuple[SourceEventMetadata, ...]
    restriction_event_targets: tuple[RestrictionEventTarget, ...]
    ticket: int
    lifecycle_epoch: int
    lifecycle_signature: tuple[object, ...] | None = None
    transition_binding: TransitionSharedOutputBinding | None = None
    default_selection: DefaultTransitionSelection | None = None
    cleanup_binding: object | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.input_identity, FinalOutputInputIdentity):
            raise ValueError("input_identity is invalid")
        if not isinstance(self.identity, FinalOutputIdentity):
            raise ValueError("identity is invalid")
        if self.identity.input_identity != self.input_identity:
            raise ValueError("final identity does not match input identity")
        if not isinstance(self.issuer_context, ClosureIssuerContext):
            raise ValueError("issuer_context is invalid")
        if self.candidate.state != "valid" or self.candidate.plan is None:
            raise ValueError("shared context requires a valid candidate")
        if not isinstance(self.projection, ClosureProjection):
            raise ValueError("projection is invalid")
        if self.default_selection is not None and not isinstance(
            self.default_selection, DefaultTransitionSelection
        ):
            raise ValueError("default_selection is invalid")
        if self.projection.wire_digest != self.identity.wire_digest:
            raise ValueError("projection digest differs from final identity")
        if self.cleanup_binding is not None:
            from src.core.cleanup_shared_output import (
                CleanupSharedOutputBinding,
                validate_cleanup_shared_binding,
            )

            binding = self.cleanup_binding
            if not isinstance(binding, CleanupSharedOutputBinding):
                raise ValueError("cleanup_binding is invalid")
            upstream = binding.upstream_context
            final_plan_row = binding.final_plan.to_dict()
            if (
                not isinstance(upstream, SharedFinalOutputContext)
                or upstream.cleanup_binding is not None
                or upstream.input_identity.cleanup_input_digest is not None
                or upstream.input_identity.cleanup_application_binding_digest is not None
                or upstream.input_identity
                != replace(
                    self.input_identity,
                    cleanup_input_digest=None,
                    cleanup_application_binding_digest=None,
                )
                or upstream.candidate != self.candidate
                or upstream.issuer_context != self.issuer_context
                or upstream.source_events != self.source_events
                or upstream.restriction_event_targets != self.restriction_event_targets
                or upstream.transition_binding != self.transition_binding
                or upstream.default_selection != self.default_selection
                or binding.final_projection != self.projection
                or binding.input_digest != self.input_identity.cleanup_input_digest
                or final_plan_row.get("schema_id") != self.identity.plan_schema_id
                or final_plan_row.get("semantic_digest") != self.identity.semantic_digest
                or binding.final_projection.wire_digest != self.identity.wire_digest
            ):
                raise ValueError("cleanup context differs from its upstream or final binding")
            validate_cleanup_shared_binding(binding)
        elif self.transition_binding is not None:
            binding = self.transition_binding
            if not isinstance(binding, TransitionSharedOutputBinding):
                raise ValueError("transition_binding is invalid")
            closure_plan = closure_plan_from_json(binding.plan.closure_plan_json)
            if (
                self.input_identity.transition_input_digest
                != binding.input_snapshot.input_digest
                or self.identity.plan_schema_id != binding.plan.schema_id
                or self.identity.semantic_digest != binding.plan.semantic_digest
                or self.identity.wire_digest != binding.projection.wire_digest
                or self.projection != binding.projection.closure_projection
                or self.candidate.plan != closure_plan
            ):
                raise ValueError("transition context differs from the validated outer plan")
            if binding.default_selection != self.default_selection:
                raise ValueError("transition and application selections differ")
        elif self.cleanup_binding is None and (
            self.input_identity.transition_input_digest is not None
            or self.identity.plan_schema_id != self.candidate.plan.schema_id
            or self.identity.semantic_digest != self.candidate.plan.semantic_digest
            or self.identity.wire_digest != self.candidate.plan.wire_digest
        ):
            raise ValueError("legacy shared context has an unbound transition identity")
        if self.default_selection is None:
            if self.input_identity.application_binding_digest is not None:
                raise ValueError("application binding has no default selection")
        elif (
            self.input_identity.application_binding_digest
            != self.default_selection.selection_digest
            or (self.transition_binding is None)
            != (self.default_selection.selection_kind == "scope_excluded")
        ):
            raise ValueError("application selection differs from its shared identity")
        if not isinstance(self.source_events, tuple) or not isinstance(
            self.restriction_event_targets, tuple
        ):
            raise ValueError("shared context metadata must be immutable tuples")
        if self.lifecycle_signature is not None and not isinstance(
            self.lifecycle_signature, tuple
        ):
            raise ValueError("lifecycle_signature must be a tuple or None")
        _require_non_negative_int(self.ticket, "ticket")
        _require_non_negative_int(self.lifecycle_epoch, "lifecycle_epoch")


@dataclass(frozen=True, slots=True)
class SharedOutputConsumerView:
    identity: FinalOutputIdentity
    input_identity: FinalOutputInputIdentity
    candidate: ClosureBuildResult
    projection: ClosureProjection | None
    source_events: tuple[SourceEventMetadata, ...]
    restriction_event_targets: tuple[RestrictionEventTarget, ...]
    transition_binding: TransitionSharedOutputBinding | None
    ticket: int
    lifecycle_epoch: int
    lifecycle_signature: tuple[object, ...] | None
    default_selection: DefaultTransitionSelection | None = None
    cleanup_binding: object | None = None
    final_points: tuple[object, ...] = ()
    cleanup_summary: object | None = None


def shared_output_consumer_view(
    context: SharedFinalOutputContext,
) -> SharedOutputConsumerView:
    """Return the single immutable view consumed by Preview, diagnostics, and saves."""
    if not isinstance(context, SharedFinalOutputContext):
        # Preserve the legacy preview helper's narrow duck-typed test/adapter
        # surface. Transition candidates always require the concrete context so
        # their outer plan, issuer, wire and input binding cannot be detached.
        identity = getattr(context, "identity", None)
        input_identity = getattr(context, "input_identity", None)
        if input_identity is None and identity is not None:
            input_identity = getattr(identity, "input_identity", None)
        candidate = getattr(context, "candidate", None)
        projection = getattr(context, "projection", None)
        source_events = getattr(context, "source_events", None)
        binding = getattr(context, "transition_binding", None)
        if (
            identity is None
            or input_identity is None
            or getattr(identity, "input_identity", None) != input_identity
            or getattr(input_identity, "transition_input_digest", None) is not None
            or getattr(input_identity, "application_binding_digest", None) is not None
            or getattr(input_identity, "cleanup_input_digest", None) is not None
            or binding is not None
            or getattr(candidate, "state", None) != "valid"
            or getattr(candidate, "plan", None) is None
            or getattr(identity, "plan_schema_id", None)
            != getattr(candidate.plan, "schema_id", None)
            or getattr(identity, "semantic_digest", None)
            != getattr(candidate.plan, "semantic_digest", None)
            or getattr(identity, "wire_digest", None)
            != getattr(candidate.plan, "wire_digest", None)
            or not isinstance(source_events, tuple)
            or (
                projection is not None
                and getattr(projection, "wire_digest", None)
                != getattr(identity, "wire_digest", None)
            )
        ):
            raise ValueError("shared final-output context is invalid")
        return SharedOutputConsumerView(
            identity=identity,
            input_identity=input_identity,
            candidate=candidate,
            projection=projection,
            source_events=source_events,
            restriction_event_targets=getattr(
                context, "restriction_event_targets", ()
            ),
            transition_binding=None,
            ticket=getattr(context, "ticket", 0),
            lifecycle_epoch=getattr(context, "lifecycle_epoch", 0),
            lifecycle_signature=getattr(context, "lifecycle_signature", None),
            default_selection=None,
        )
    if (
        context.identity.input_identity != context.input_identity
        or context.projection.wire_digest != context.identity.wire_digest
        or context.candidate.state != "valid"
        or context.candidate.plan is None
    ):
        raise ValueError("shared final-output context identity is inconsistent")
    if context.cleanup_binding is not None:
        from src.core.cleanup_shared_output import (
            CleanupSharedOutputBinding,
            validate_cleanup_shared_binding,
        )

        cleanup_binding = context.cleanup_binding
        if not isinstance(cleanup_binding, CleanupSharedOutputBinding):
            raise ValueError("shared cleanup binding is invalid")
        validate_cleanup_shared_binding(cleanup_binding)
        final_plan_row = cleanup_binding.final_plan.to_dict()
        if (
            context.input_identity.cleanup_input_digest != cleanup_binding.input_digest
            or context.input_identity.cleanup_application_binding_digest
            != (
                None
                if cleanup_binding.default_selection is None
                else cleanup_binding.default_selection.selection_digest
            )
            or cleanup_binding.final_projection != context.projection
            or final_plan_row.get("schema_id") != context.identity.plan_schema_id
            or final_plan_row.get("semantic_digest") != context.identity.semantic_digest
            or cleanup_binding.final_projection.wire_digest != context.identity.wire_digest
        ):
            raise ValueError("shared cleanup consumer binding is inconsistent")
        return SharedOutputConsumerView(
            identity=context.identity,
            input_identity=context.input_identity,
            candidate=context.candidate,
            projection=context.projection,
            source_events=context.source_events,
            restriction_event_targets=context.restriction_event_targets,
            transition_binding=context.transition_binding,
            ticket=context.ticket,
            lifecycle_epoch=context.lifecycle_epoch,
            lifecycle_signature=context.lifecycle_signature,
            default_selection=context.default_selection,
            cleanup_binding=cleanup_binding,
            final_points=cleanup_binding.final_points,
            cleanup_summary=cleanup_binding.summary,
        )
    if (
        context.input_identity.cleanup_input_digest is not None
        or context.input_identity.cleanup_application_binding_digest is not None
    ):
        raise ValueError("cleanup input digest has no shared cleanup binding")
    binding = context.transition_binding
    if binding is not None and (
        context.input_identity.transition_input_digest
        != binding.input_snapshot.input_digest
        or context.identity.plan_schema_id != binding.plan.schema_id
        or context.identity.semantic_digest != binding.plan.semantic_digest
        or context.identity.wire_digest != binding.projection.wire_digest
        or context.projection != binding.projection.closure_projection
        or context.candidate.plan
        != closure_plan_from_json(binding.plan.closure_plan_json)
    ):
        raise ValueError("shared transition consumer binding is inconsistent")
    if binding is None and context.input_identity.transition_input_digest is not None:
        raise ValueError("transition input digest has no shared transition binding")
    selection = context.default_selection
    if selection is None:
        if context.input_identity.application_binding_digest is not None:
            raise ValueError("application binding has no default selection")
    elif (
        context.input_identity.application_binding_digest != selection.selection_digest
        or (binding is None) != (selection.selection_kind == "scope_excluded")
        or (binding is not None and binding.default_selection != selection)
    ):
        raise ValueError("default application selection is inconsistent")
    if binding is None and (
        context.identity.plan_schema_id != context.candidate.plan.schema_id
        or context.identity.semantic_digest != context.candidate.plan.semantic_digest
        or context.identity.wire_digest != context.candidate.plan.wire_digest
    ):
        raise ValueError("legacy shared output identity differs from its closure plan")
    return SharedOutputConsumerView(
        identity=context.identity,
        input_identity=context.input_identity,
        candidate=context.candidate,
        projection=context.projection,
        source_events=context.source_events,
        restriction_event_targets=context.restriction_event_targets,
        transition_binding=binding,
        ticket=context.ticket,
        lifecycle_epoch=context.lifecycle_epoch,
        lifecycle_signature=context.lifecycle_signature,
        default_selection=context.default_selection,
        cleanup_binding=None,
        final_points=(),
        cleanup_summary=None,
    )


@dataclass(frozen=True, slots=True)
class FinalOutputSyncResult:
    status: str
    context: SharedFinalOutputContext | None = None
    issues: tuple[ClosureIssue, ...] = ()
    preview_data: object | None = None
    diagnostics_snapshot: object | None = None
    expected_transition_input_digest: str | None = None
    expected_application_binding_digest: str | None = None
    expected_cleanup_input_digest: str | None = None
    expected_cleanup_application_binding_digest: str | None = None

    def __post_init__(self) -> None:
        if self.status not in {"valid", "invalid", "unavailable", "stale"}:
            raise ValueError("status is unsupported")
        if self.status == "valid" and self.context is None:
            raise ValueError("valid result requires a context")
        if self.status != "valid" and self.context is not None:
            raise ValueError("failed result cannot carry a context")
        if self.status != "valid" and self.preview_data is not None:
            raise ValueError("failed result cannot carry shared preview data")
        if not isinstance(self.issues, tuple):
            raise ValueError("issues must be a tuple")
        if self.expected_transition_input_digest is not None:
            _require_digest(
                self.expected_transition_input_digest,
                "expected_transition_input_digest",
            )
        if self.expected_application_binding_digest is not None:
            _require_digest(
                self.expected_application_binding_digest,
                "expected_application_binding_digest",
            )
        if self.expected_cleanup_input_digest is not None:
            _require_digest(
                self.expected_cleanup_input_digest,
                "expected_cleanup_input_digest",
            )
        if self.expected_cleanup_application_binding_digest is not None:
            _require_digest(
                self.expected_cleanup_application_binding_digest,
                "expected_cleanup_application_binding_digest",
            )
        if self.context is not None:
            context_digest = self.context.input_identity.transition_input_digest
            if context_digest != self.expected_transition_input_digest:
                raise ValueError("sync result transition digest differs from its context")
            if (
                self.context.input_identity.application_binding_digest
                != self.expected_application_binding_digest
            ):
                raise ValueError("sync result application digest differs from its context")
            if (
                self.context.input_identity.cleanup_input_digest
                != self.expected_cleanup_input_digest
            ):
                raise ValueError("sync result cleanup digest differs from its context")
            if (
                self.context.input_identity.cleanup_application_binding_digest
                != self.expected_cleanup_application_binding_digest
            ):
                raise ValueError("sync result cleanup application digest differs from its context")


def build_final_output_input_identity(
    *,
    origin: FinalOutputOrigin,
    manual_revision: int,
    input_mode: str,
    normalized_text_path: str | None,
    issuer_context: ClosureIssuerContext,
    closure_contract: ClosureContract,
    transition_input_digest: str | None = None,
    application_binding_digest: str | None = None,
    crossfade_policy_id: str | None = None,
) -> FinalOutputInputIdentity:
    if not isinstance(issuer_context, ClosureIssuerContext):
        raise TypeError("issuer_context must be ClosureIssuerContext")
    if not isinstance(closure_contract, ClosureContract):
        raise TypeError("closure_contract must be ClosureContract")
    legacy = issuer_context.legacy_context
    legacy_identity = legacy.identity_context
    if legacy_identity is None:
        raise ValueError("issuer identity is missing")
    if (
        origin.source_run_id != legacy_identity.source_run_id
        or origin.analysis_generation != legacy_identity.analysis_generation
        or origin.job_id < 0
        or origin.base_plan_digest != legacy_identity.base_plan_digest
        or manual_revision < 0
        or input_mode != origin.input_mode
        or _normalize_path(normalized_text_path) != _normalize_path(origin.text_path)
    ):
        raise ValueError("origin and B2 issuer identity differ")
    if legacy_identity.manual_revision != manual_revision:
        raise ValueError("manual revision differs from B2 issuer identity")
    return FinalOutputInputIdentity(
        source_run_id=origin.source_run_id,
        job_id=origin.job_id,
        analysis_generation=origin.analysis_generation,
        manual_revision=manual_revision,
        input_mode=input_mode,
        input_binding_digest=origin.input_binding_digest,
        source_audio_path=_normalize_path(origin.source_audio_path),
        analysis_wav_path=_normalize_path(origin.analysis_wav_path),
        normalized_text_path=_normalize_path(normalized_text_path),
        base_plan_digest=legacy_identity.base_plan_digest,
        adjustment_snapshot_digest=snapshot_digest(legacy.adjustment_snapshot),
        effective_plan_digest=legacy_identity.effective_plan_digest,
        resolved_profile_id=legacy_identity.resolved_profile_id,
        output_mapping=tuple(legacy_identity.output_mapping),
        numeric_policy_id=legacy_identity.numeric_policy_id,
        curve_policy_id=legacy_identity.curve_policy_id,
        silence_policy_id=legacy_identity.silence_policy_id,
        crossfade_policy_id=(
            legacy_identity.crossfade_policy_id
            if crossfade_policy_id is None
            else _require_text(crossfade_policy_id, "crossfade_policy_id")
        ),
        closure_contract_digest=closure_contract.digest,
        baseline_digest=issuer_context.baseline_digest,
        transition_input_digest=transition_input_digest,
        application_binding_digest=application_binding_digest,
    )


def capture_source_event_metadata(effective_plan: object) -> tuple[SourceEventMetadata, ...]:
    events = tuple(getattr(effective_plan, "effective_events", ()))
    group_by_event: dict[int, tuple[tuple[int, ...], tuple[int, ...], str]] = {}
    for shape in tuple(getattr(effective_plan, "shapes", ())):
        group = tuple(getattr(shape, "real_base_event_indices", ()))
        tokens = tuple(getattr(shape, "internal_shape_source_tokens", ()))
        for index in group:
            if index in group_by_event:
                raise ValueError("effective event belongs to more than one shape group")
            group_by_event[index] = (group, tokens, getattr(shape, "vowel", None))
    long_by_event: dict[int, tuple[int, str, str]] = {}
    for run in tuple(getattr(effective_plan, "long_vowel_runs", ())):
        source_index = getattr(run, "source_base_event_index", None)
        continuation_indices = tuple(
            getattr(run, "continuation_base_event_indices", ())
        )
        terminal_index = getattr(run, "terminal_base_event_index", None)
        mode = getattr(run, "resolved_mode", None)
        if (
            isinstance(source_index, bool)
            or not isinstance(source_index, int)
            or source_index < 0
            or isinstance(terminal_index, bool)
            or not isinstance(terminal_index, int)
            or terminal_index < 0
            or mode not in {"hold", "decay"}
        ):
            raise ValueError("effective long-vowel run metadata is invalid")
        if len(continuation_indices) != len(set(continuation_indices)):
            raise ValueError("long-vowel continuation indices are duplicated")
        roles_by_index = {source_index: "source"}
        for index in continuation_indices:
            if isinstance(index, bool) or not isinstance(index, int) or index < 0:
                raise ValueError("long-vowel run event index is invalid")
            if index == source_index:
                raise ValueError("long-vowel source cannot be its own continuation")
            roles_by_index[index] = "continuation"
        if terminal_index in roles_by_index:
            if roles_by_index[terminal_index] != "continuation":
                raise ValueError("long-vowel terminal metadata conflicts with source")
            roles_by_index[terminal_index] = "continuation_terminal"
        else:
            roles_by_index[terminal_index] = "terminal"
        for index, role in roles_by_index.items():
            if index in long_by_event:
                raise ValueError("effective event belongs to multiple long-vowel runs")
            long_by_event[index] = (source_index, role, mode)
    result: list[SourceEventMetadata] = []
    seen: set[int] = set()
    for event in events:
        index = getattr(event, "base_event_index", None)
        if isinstance(index, bool) or not isinstance(index, int) or index < 0 or index in seen:
            raise ValueError("effective events must have unique non-negative base indices")
        seen.add(index)
        if (
            index in group_by_event
            and group_by_event[index][2] != getattr(event, "vowel", None)
        ):
            raise ValueError("effective event vowel differs from its shape group")
        group, tokens, _ = group_by_event.get(
            index,
            ((index,), (), getattr(event, "vowel", None)),
        )
        long_metadata = long_by_event.get(index)
        result.append(
            SourceEventMetadata(
                base_event_index=index,
                vowel=getattr(event, "vowel", None),
                start_frame=getattr(event, "start_frame", None),
                peak_frame=getattr(event, "peak_frame", None),
                end_frame=getattr(event, "end_frame", None),
                peak_value=getattr(event, "peak_value", None),
                group_event_indices=group,
                shape_internal_source_tokens=tokens,
                long_vowel_source_event_index=(
                    None if long_metadata is None else long_metadata[0]
                ),
                long_vowel_role=(
                    None if long_metadata is None else long_metadata[1]
                ),
                long_vowel_mode=(
                    None if long_metadata is None else long_metadata[2]
                ),
            )
        )
    event_indices = {item.base_event_index for item in result}
    if set(group_by_event).difference(event_indices) or set(long_by_event).difference(
        event_indices
    ):
        raise ValueError("shape or long-vowel metadata references an unknown effective event")
    event_by_index = {item.base_event_index: item for item in result}
    for event in result:
        if event.long_vowel_source_event_index is None:
            continue
        source = event_by_index.get(event.long_vowel_source_event_index)
        if source is None or source.vowel != event.vowel:
            raise ValueError("long-vowel source must resolve to the same vowel")
        if (event.long_vowel_role == "source") != (
            event.base_event_index == event.long_vowel_source_event_index
        ):
            raise ValueError("long-vowel source role does not match its event")
    return tuple(sorted(result, key=lambda item: item.base_event_index))


def _restriction_event_targets(
    restrictions: tuple[ClosureRestriction, ...],
    source_events: tuple[SourceEventMetadata, ...],
) -> tuple[RestrictionEventTarget, ...]:
    event_by_index = {item.base_event_index: item for item in source_events}
    if len(event_by_index) != len(source_events):
        raise ValueError("source event indices are not unique")
    targets: list[RestrictionEventTarget] = []
    for restriction in restrictions:
        indices: list[int] = []
        for source_id in restriction.source_ids:
            if source_id.startswith("source:event"):
                match = _EVENT_SOURCE_PATTERN.fullmatch(source_id)
                if match is None:
                    raise ValueError("event provenance id is malformed")
                index = int(match.group(1))
                if index not in event_by_index:
                    raise ValueError("event provenance id does not resolve in this snapshot")
                if index in indices:
                    raise ValueError("event provenance id is duplicated")
                indices.append(index)
        for index in indices:
            targets.append(
                RestrictionEventTarget(
                    restriction=restriction,
                    event=event_by_index[index],
                )
            )
    return tuple(targets)


def build_shared_final_output_context(
    issuer_context: ClosureIssuerContext,
    closure_contract: ClosureContract | None,
    current_input_identity: FinalOutputInputIdentity,
    *,
    source_events: tuple[SourceEventMetadata, ...] = (),
    ticket: int = 0,
    lifecycle_epoch: int = 0,
    lifecycle_signature: tuple[object, ...] | None = None,
    default_selection: DefaultTransitionSelection | None = None,
) -> FinalOutputSyncResult:
    if not isinstance(issuer_context, ClosureIssuerContext):
        return FinalOutputSyncResult("unavailable")
    if not isinstance(current_input_identity, FinalOutputInputIdentity):
        return FinalOutputSyncResult("invalid")
    contract = closure_contract or ClosureContract()
    if not isinstance(contract, ClosureContract):
        return FinalOutputSyncResult("invalid")
    try:
        legacy_identity = issuer_context.legacy_context.identity_context
        if legacy_identity is None:
            return FinalOutputSyncResult("unavailable")
        expected = FinalOutputInputIdentity(
            source_run_id=legacy_identity.source_run_id,
            job_id=current_input_identity.job_id,
            analysis_generation=legacy_identity.analysis_generation,
            manual_revision=legacy_identity.manual_revision,
            input_mode=current_input_identity.input_mode,
            input_binding_digest=current_input_identity.input_binding_digest,
            source_audio_path=current_input_identity.source_audio_path,
            analysis_wav_path=current_input_identity.analysis_wav_path,
            normalized_text_path=current_input_identity.normalized_text_path,
            base_plan_digest=legacy_identity.base_plan_digest,
            adjustment_snapshot_digest=snapshot_digest(
                issuer_context.legacy_context.adjustment_snapshot
            ),
            effective_plan_digest=legacy_identity.effective_plan_digest,
            resolved_profile_id=legacy_identity.resolved_profile_id,
            output_mapping=tuple(legacy_identity.output_mapping),
            numeric_policy_id=legacy_identity.numeric_policy_id,
            curve_policy_id=legacy_identity.curve_policy_id,
            silence_policy_id=legacy_identity.silence_policy_id,
            crossfade_policy_id=legacy_identity.crossfade_policy_id,
            closure_contract_digest=contract.digest,
            baseline_digest=issuer_context.baseline_digest,
            application_binding_digest=(
                None if default_selection is None else default_selection.selection_digest
            ),
        )
        if expected != current_input_identity:
            return FinalOutputSyncResult("stale")
        if not isinstance(source_events, tuple):
            return FinalOutputSyncResult("invalid")
        expected_source_events = capture_source_event_metadata(
            issuer_context.legacy_context.effective_plan_snapshot
        )
        if source_events and source_events != expected_source_events:
            return FinalOutputSyncResult("stale")
        source_events = expected_source_events
        candidate = build_closure_candidate(issuer_context, contract)
        if candidate.state != "valid" or candidate.plan is None:
            return FinalOutputSyncResult(candidate.state, issues=candidate.issues)
        projection = project_validated_closure_candidate(
            candidate,
            issuer_context,
            contract,
        )
        plan_identity = candidate.plan.identity_context
        if plan_identity is None:
            raise ClosurePlanError("candidate identity is missing")
        identity = FinalOutputIdentity(
            input_identity=current_input_identity,
            plan_schema_id=candidate.plan.schema_id,
            curve_policy_id=candidate.plan.contract.curve_policy_id,
            semantic_digest=candidate.plan.semantic_digest,
            wire_digest=projection.wire_digest,
        )
        targets = _restriction_event_targets(candidate.plan.restrictions, source_events)
        context = SharedFinalOutputContext(
            input_identity=current_input_identity,
            identity=identity,
            issuer_context=issuer_context,
            candidate=candidate,
            projection=projection,
            source_events=source_events,
            restriction_event_targets=targets,
            ticket=ticket,
            lifecycle_epoch=lifecycle_epoch,
            lifecycle_signature=lifecycle_signature,
            default_selection=default_selection,
        )
        return FinalOutputSyncResult(
            "valid",
            context=context,
            expected_application_binding_digest=(
                None if default_selection is None else default_selection.selection_digest
            ),
        )
    except (AttributeError, TypeError, ValueError, RuntimeError, OverflowError, ClosurePlanError) as error:
        issue = ClosureIssue("input_invalid", "shared_output", str(error))
        return FinalOutputSyncResult("invalid", issues=(issue,))


def build_transition_shared_final_output_context(
    *,
    origin: FinalOutputOrigin,
    manual_revision: int,
    input_mode: str,
    normalized_text_path: str | None,
    issuer_context: ClosureIssuerContext,
    closure_contract: ClosureContract,
    transition_request: TransitionEvaluationRequest,
    transition_input_snapshot: TransitionInputSnapshot,
    ticket: int = 0,
    lifecycle_epoch: int = 0,
    lifecycle_signature: tuple[object, ...] | None = None,
) -> FinalOutputSyncResult:
    """Build the candidate context only after B2 validates the complete outer plan."""
    expected_input_digest = (
        transition_input_snapshot.input_digest
        if isinstance(transition_input_snapshot, TransitionInputSnapshot)
        else None
    )
    if not isinstance(issuer_context, ClosureIssuerContext):
        return FinalOutputSyncResult("unavailable")
    if not isinstance(transition_request, TransitionEvaluationRequest):
        return FinalOutputSyncResult("invalid")
    if not isinstance(transition_input_snapshot, TransitionInputSnapshot):
        return FinalOutputSyncResult("unavailable")
    try:
        if transition_request.policy != transition_input_snapshot.policy:
            raise ValueError(
                "transition evaluation request policy differs from input snapshot"
            )
        if not isinstance(origin, FinalOutputOrigin):
            raise ValueError("accepted analysis origin is unavailable")
        legacy = issuer_context.legacy_context
        legacy_identity = legacy.identity_context
        effective_plan = legacy.effective_plan_snapshot
        if legacy_identity is None or legacy.adjustment_snapshot is None:
            raise ValueError("accepted closure source identity is unavailable")
        generation_token = canonical_transition_generation_token(
            origin.analysis_generation
        )
        if (
            transition_input_snapshot.run_id != origin.source_run_id
            or transition_input_snapshot.analysis_generation != generation_token
            or transition_input_snapshot.manual_revision != manual_revision
            or transition_input_snapshot.input_mode != input_mode
            or origin.input_mode != input_mode
            or transition_input_snapshot.base_plan_digest != origin.base_plan_digest
            or transition_input_snapshot.base_plan_digest != legacy_identity.base_plan_digest
            or transition_input_snapshot.analysis_generation
            != str(legacy_identity.analysis_generation)
            or transition_input_snapshot.run_id != legacy_identity.source_run_id
            or legacy_identity.manual_revision != manual_revision
        ):
            raise ValueError("accepted origin and transition input binding differ")
        acoustic = transition_input_snapshot.acoustic
        if (
            acoustic.analysis_wav_sha256 != transition_input_snapshot.analysis_wav_sha256
            or acoustic.source_sha256_before != transition_input_snapshot.analysis_wav_sha256
            or acoustic.source_sha256_after != transition_input_snapshot.analysis_wav_sha256
        ):
            raise ValueError("transition acoustic evidence is not bound to the accepted WAV")

        pairs = build_transition_pairs_from_effective_plan(
            effective_plan,
            fps=transition_input_snapshot.policy.fps,
        )
        source_lineage = TransitionSourceLineage(
            source_kind="live_analysis",
            origin_kind="accepted_analysis",
            origin_identity=f"{origin.source_run_id}/{generation_token}",
            run_id=origin.source_run_id,
            analysis_generation=generation_token,
            input_mode=input_mode,
            analysis_wav_sha256=transition_input_snapshot.analysis_wav_sha256,
            policy_digest=transition_input_snapshot.policy.policy_digest,
            parameter_digest=transition_input_snapshot.policy.policy_digest,
            acoustic_evidence_digest=acoustic.content_digest,
            base_plan_digest=transition_input_snapshot.base_plan_digest,
            manual_revision=manual_revision,
            manual_snapshot_digest=snapshot_digest(legacy.adjustment_snapshot),
            effective_plan_digest=legacy_identity.effective_plan_digest,
            # B2's strict lineage schema requires text when the accepted UI identity
            # has no selected profile. "default" is its established unprofiled
            # compatibility marker, not a generated profile or a UI selection.
            resolved_profile_id=legacy_identity.resolved_profile_id or "default",
            output_mapping=tuple(legacy_identity.output_mapping),
            pair_identity=transition_pair_identity(pairs),
        )
        transition_issuer = TransitionPlanIssuerContext(
            input_snapshot=transition_input_snapshot,
            source_lineage=source_lineage,
            pairs=pairs,
            baseline_shapes=tuple(getattr(effective_plan, "shapes", ())),
            closure_issuer_context=issuer_context,
        )
        resolution = resolve_cross_vowel_transition(
            policy=transition_input_snapshot.policy,
            acoustic_snapshot=acoustic,
            pairs=pairs,
            shapes=transition_issuer.baseline_shapes,
        )
        build_result = build_transition_candidate(transition_issuer, resolution)
        if build_result.state != "valid" or build_result.plan is None:
            issue = ClosureIssue(
                "capture_unavailable"
                if build_result.state == "unavailable"
                else "input_invalid",
                "transition_candidate",
                ";".join(build_result.issues) or build_result.state,
            )
            return FinalOutputSyncResult(
                build_result.state,
                issues=(issue,),
                expected_transition_input_digest=expected_input_digest,
            )
        validation = validate_transition_plan(
            build_result.plan,
            issuer_context=transition_issuer,
            resolution=resolution,
        )
        if validation.state != "valid":
            issue = ClosureIssue(
                "input_invalid",
                "transition_validation",
                ";".join(validation.issues) or validation.state,
            )
            return FinalOutputSyncResult(
                "invalid",
                issues=(issue,),
                expected_transition_input_digest=expected_input_digest,
            )
        projection = project_validated_transition_plan(
            build_result.plan,
            issuer_context=transition_issuer,
            resolution=resolution,
        )
        closure_plan = closure_plan_from_json(build_result.plan.closure_plan_json)
        closure_candidate = ClosureBuildResult("valid", closure_plan, ())
        input_identity = build_final_output_input_identity(
            origin=origin,
            manual_revision=manual_revision,
            input_mode=input_mode,
            normalized_text_path=normalized_text_path,
            issuer_context=issuer_context,
            closure_contract=closure_contract,
            transition_input_digest=transition_input_snapshot.input_digest,
            crossfade_policy_id=transition_request.policy.policy_id,
        )
        identity = FinalOutputIdentity(
            input_identity=input_identity,
            plan_schema_id=build_result.plan.schema_id,
            curve_policy_id=transition_request.policy.curve_family,
            semantic_digest=build_result.plan.semantic_digest,
            wire_digest=projection.wire_digest,
        )
        source_events = capture_source_event_metadata(effective_plan)
        targets = _restriction_event_targets(closure_plan.restrictions, source_events)
        binding = TransitionSharedOutputBinding(
            evaluation_request=transition_request,
            input_snapshot=transition_input_snapshot,
            issuer_context=transition_issuer,
            resolution=resolution,
            plan=build_result.plan,
            validation=validation,
            projection=projection,
        )
        context = SharedFinalOutputContext(
            input_identity=input_identity,
            identity=identity,
            issuer_context=issuer_context,
            candidate=closure_candidate,
            projection=projection.closure_projection,
            source_events=source_events,
            restriction_event_targets=targets,
            ticket=ticket,
            lifecycle_epoch=lifecycle_epoch,
            lifecycle_signature=lifecycle_signature,
            transition_binding=binding,
        )
        return FinalOutputSyncResult(
            "valid",
            context=context,
            expected_transition_input_digest=expected_input_digest,
        )
    except (AttributeError, TypeError, ValueError, RuntimeError, OverflowError, ClosurePlanError) as error:
        issue = ClosureIssue(
            "input_invalid",
            "transition_shared_output",
            f"{type(error).__name__}: {error}",
        )
        return FinalOutputSyncResult(
            "invalid",
            issues=(issue,),
            expected_transition_input_digest=expected_input_digest,
        )


__all__ = [
    "FinalOutputIdentity",
    "FinalOutputInputIdentity",
    "FinalOutputSyncResult",
    "RestrictionEventTarget",
    "SharedFinalOutputContext",
    "SharedOutputConsumerView",
    "SourceEventMetadata",
    "TransitionSharedOutputBinding",
    "build_closure_issuer_context",
    "build_final_output_input_identity",
    "build_shared_final_output_context",
    "build_transition_shared_final_output_context",
    "canonical_transition_generation_token",
    "shared_output_consumer_view",
    "capture_source_event_metadata",
]
