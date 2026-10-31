from __future__ import annotations

import hashlib
from dataclasses import dataclass, replace as dataclass_replace
from pathlib import Path
from typing import Literal

from src.core.final_morph_closure_plan import ClosurePlan, validate_closure_plan_integrity
from src.core.final_morph_closure_plan import closure_plan_from_json
from src.core.final_morph_transition_plan import validate_transition_plan
from src.core.final_output_projection import (
    SharedFinalOutputContext,
    SharedOutputConsumerView,
    TransitionSharedOutputBinding,
    shared_output_consumer_view,
)
from src.core.output_diagnostics import (
    OutputDiagnosticsSnapshot,
    shared_warning_confirmation_matches,
)
from src.vmd_writer.final_morph_closure_adapter import (
    ClosureProjection,
    project_validated_closure_candidate,
)
from src.vmd_writer.final_morph_transition_adapter import (
    project_validated_transition_plan,
    validate_transition_vmd_readback,
)
from src.vmd_writer.verified_morph_output import (
    VerifiedVmdEvidence,
    validate_verified_morph_readback,
)


GateStatus = Literal["ready", "warning_confirmation_required", "blocked"]


@dataclass(frozen=True, slots=True)
class SharedSaveGateResult:
    status: GateStatus
    blocking_codes: tuple[str, ...]
    warning_codes: tuple[str, ...]
    fingerprint: str | None
    context: SharedFinalOutputContext | None
    diagnostics_snapshot: OutputDiagnosticsSnapshot | None

    def __post_init__(self) -> None:
        object.__setattr__(self, "blocking_codes", tuple(dict.fromkeys(self.blocking_codes)))
        object.__setattr__(self, "warning_codes", tuple(dict.fromkeys(self.warning_codes)))
        if self.status == "blocked":
            if not self.blocking_codes or self.context is not None:
                raise ValueError("blocked shared save gate must expose reasons only")
        elif self.blocking_codes or self.context is None or self.fingerprint is None:
            raise ValueError("ready shared save gate requires a bound context")


@dataclass(frozen=True, slots=True)
class VerifiedVmdSaveRequest:
    job_id: int
    context: SharedFinalOutputContext
    diagnostics_snapshot: OutputDiagnosticsSnapshot
    fingerprint: str
    ticket: int
    lifecycle_epoch: int
    lifecycle_signature: tuple[object, ...]
    model_name: str
    output_mapping: tuple[tuple[str, str], ...]
    final_path: Path
    overwrite_authorized: bool
    expected_existing_file_identity: tuple[int | None, int | None, int | None, int] | None
    protected_paths: tuple[str, ...]

    def __post_init__(self) -> None:
        if isinstance(self.job_id, bool) or not isinstance(self.job_id, int) or self.job_id <= 0:
            raise ValueError("job_id must be positive")
        if not isinstance(self.context, SharedFinalOutputContext):
            raise ValueError("context must be SharedFinalOutputContext")
        if not isinstance(self.diagnostics_snapshot, OutputDiagnosticsSnapshot):
            raise ValueError("diagnostics_snapshot is invalid")
        if self.diagnostics_snapshot.shared_final_output_identity != self.context.identity:
            raise ValueError("diagnostics do not match the shared output context")
        if self.diagnostics_snapshot.save_state_fingerprint != self.fingerprint:
            raise ValueError("fingerprint does not match diagnostics")
        if self.ticket != self.context.ticket or self.lifecycle_epoch != self.context.lifecycle_epoch:
            raise ValueError("request ticket does not match its context")
        if self.lifecycle_signature != self.context.lifecycle_signature:
            raise ValueError("request lifecycle signature does not match its context")
        if type(self.model_name) is not str or not self.model_name:
            raise ValueError("model_name is invalid")
        if self.output_mapping != self.context.input_identity.output_mapping:
            raise ValueError("output mapping differs from the shared identity")
        if not isinstance(self.final_path, Path):
            raise ValueError("final_path must be a Path")
        if not isinstance(self.overwrite_authorized, bool):
            raise ValueError("overwrite_authorized must be bool")
        if self.expected_existing_file_identity is not None:
            if (
                not isinstance(self.expected_existing_file_identity, tuple)
                or len(self.expected_existing_file_identity) != 4
                or isinstance(self.expected_existing_file_identity[3], bool)
                or not isinstance(self.expected_existing_file_identity[3], int)
                or self.expected_existing_file_identity[3] < 0
            ):
                raise ValueError("expected_existing_file_identity is invalid")
            if not self.overwrite_authorized:
                raise ValueError("existing file identity requires overwrite consent")
        object.__setattr__(self, "protected_paths", tuple(self.protected_paths))
        if any(type(path) is not str or not path for path in self.protected_paths):
            raise ValueError("protected_paths contains an invalid path")


@dataclass(frozen=True, slots=True)
class SaveCommitLease:
    job_id: int
    ticket: int
    lifecycle_epoch: int
    binding_digest: str
    fingerprint: str
    lifecycle_signature: tuple[object, ...]
    lease_id: str

    def __post_init__(self) -> None:
        if isinstance(self.job_id, bool) or not isinstance(self.job_id, int) or self.job_id <= 0:
            raise ValueError("lease job_id must be positive")
        for name in ("ticket", "lifecycle_epoch"):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, int) or value < 0:
                raise ValueError(f"{name} must be non-negative")
        for name in ("binding_digest", "fingerprint", "lease_id"):
            value = getattr(self, name)
            if type(value) is not str or not value:
                raise ValueError(f"{name} must be non-empty")
        if not isinstance(self.lifecycle_signature, tuple):
            raise ValueError("lifecycle_signature must be a tuple")


def _blocked(*codes: str) -> SharedSaveGateResult:
    return SharedSaveGateResult(
        status="blocked",
        blocking_codes=tuple(code for code in codes if code),
        warning_codes=(),
        fingerprint=None,
        context=None,
        diagnostics_snapshot=None,
    )


def evaluate_shared_save_gate(
    *,
    context: SharedFinalOutputContext | None,
    diagnostics_snapshot: OutputDiagnosticsSnapshot | None,
    current_lifecycle_signature: tuple[object, ...] | None,
    confirmed_warning_fingerprint: str | None,
    application_busy: bool,
    analysis_pending: bool,
    expected_transition_input_digest: str | None = None,
    expected_application_binding_digest: str | None = None,
    expected_cleanup_input_digest: str | None = None,
    expected_cleanup_application_binding_digest: str | None = None,
) -> SharedSaveGateResult:
    """Check that one accepted B3 result is still the save target, without rebuilding it."""
    if not isinstance(context, SharedFinalOutputContext):
        return _blocked("shared_final_output_unavailable")
    if not isinstance(diagnostics_snapshot, OutputDiagnosticsSnapshot):
        return _blocked("shared_diagnostics_unavailable")
    if application_busy:
        return _blocked("delivery_busy")
    if analysis_pending or diagnostics_snapshot.analysis_summary.analysis_pending_rebuild:
        return _blocked("analysis_rebuild_required")
    if (
        current_lifecycle_signature is None
        or context.lifecycle_signature != current_lifecycle_signature
    ):
        return _blocked("shared_final_output_stale")
    if diagnostics_snapshot.shared_final_output_identity != context.identity:
        return _blocked("shared_diagnostics_stale")
    if (
        not diagnostics_snapshot.analysis_summary.analysis_result_valid
        or diagnostics_snapshot.analysis_summary.event_count <= 0
    ):
        return _blocked("analysis_not_ready")
    if (
        not diagnostics_snapshot.saveability.vmd_save_allowed
        or diagnostics_snapshot.saveability.blocking_codes
        or any(item.severity.value == "ERROR" for item in diagnostics_snapshot.items)
    ):
        return _blocked("effective_writer_input_unavailable")
    fingerprint = diagnostics_snapshot.save_state_fingerprint
    if type(fingerprint) is not str or not fingerprint:
        return _blocked("shared_fingerprint_unavailable")
    plan = context.candidate.plan
    if not isinstance(plan, ClosurePlan) or plan.state != "valid":
        return _blocked("shared_closure_plan_unavailable")
    try:
        validate_closure_plan_integrity(plan)
    except (TypeError, ValueError):
        return _blocked("shared_closure_plan_invalid")
    cleanup_binding = context.cleanup_binding
    if cleanup_binding is not None:
        from src.core.cleanup_shared_output import (
            CleanupSharedOutputBinding,
            validate_cleanup_shared_binding,
        )

        if (
            not isinstance(cleanup_binding, CleanupSharedOutputBinding)
            or expected_cleanup_input_digest is None
            or expected_cleanup_input_digest != cleanup_binding.input_digest
            or context.input_identity.cleanup_input_digest != cleanup_binding.input_digest
            or context.input_identity.cleanup_application_binding_digest
            != (
                None
                if cleanup_binding.default_selection is None
                else cleanup_binding.default_selection.selection_digest
            )
            or expected_cleanup_application_binding_digest
            != context.input_identity.cleanup_application_binding_digest
            or diagnostics_snapshot.cleanup_summary != cleanup_binding.summary
            or diagnostics_snapshot.shared_final_output_identity != context.identity
        ):
            return _blocked("shared_cleanup_binding_mismatch")
        try:
            validate_cleanup_shared_binding(cleanup_binding)
            project_shared_output_context(context)
        except (TypeError, ValueError):
            return _blocked("shared_cleanup_plan_invalid")
        warnings = tuple(diagnostics_snapshot.saveability.warning_codes)
        if warnings and not shared_warning_confirmation_matches(
            diagnostics_snapshot, confirmed_warning_fingerprint
        ):
            return SharedSaveGateResult(
                status="warning_confirmation_required",
                blocking_codes=(), warning_codes=warnings, fingerprint=fingerprint,
                context=context, diagnostics_snapshot=diagnostics_snapshot,
            )
        return SharedSaveGateResult(
            status="ready", blocking_codes=(), warning_codes=warnings,
            fingerprint=fingerprint, context=context,
            diagnostics_snapshot=diagnostics_snapshot,
        )
    if (
        context.input_identity.cleanup_input_digest is not None
        or context.input_identity.cleanup_application_binding_digest is not None
        or expected_cleanup_input_digest is not None
        or expected_cleanup_application_binding_digest is not None
    ):
        return _blocked("shared_cleanup_binding_missing")
    if context.transition_binding is None:
        if expected_transition_input_digest is not None:
            return _blocked("shared_transition_binding_mismatch")
        selection = context.default_selection
        if selection is None:
            if (
                expected_application_binding_digest is not None
                or context.input_identity.application_binding_digest is not None
            ):
                return _blocked("shared_application_binding_mismatch")
        elif (
            selection.selection_kind != "scope_excluded"
            or expected_application_binding_digest != selection.selection_digest
            or context.input_identity.application_binding_digest != selection.selection_digest
        ):
            return _blocked("shared_application_binding_mismatch")
        if (
            context.input_identity.transition_input_digest is not None
            or context.identity.semantic_digest != plan.semantic_digest
            or context.identity.wire_digest != plan.wire_digest
            or context.identity.input_identity != context.input_identity
            or tuple(context.input_identity.output_mapping) != tuple(plan.identity_context.output_mapping)
        ):
            return _blocked("shared_final_output_identity_mismatch")
    else:
        binding = context.transition_binding
        selection = context.default_selection
        if selection is None:
            application_binding_valid = (
                expected_application_binding_digest is None
                and context.input_identity.application_binding_digest is None
                and binding.default_selection is None
            )
        else:
            application_binding_valid = (
                selection.selection_kind == "transition"
                and binding.default_selection == selection
                and expected_application_binding_digest == selection.selection_digest
                and context.input_identity.application_binding_digest == selection.selection_digest
            )
        if (
            not isinstance(binding, TransitionSharedOutputBinding)
            or not application_binding_valid
            or expected_transition_input_digest is None
            or expected_transition_input_digest != binding.input_snapshot.input_digest
            or context.input_identity.transition_input_digest != expected_transition_input_digest
            or binding.validation.state != "valid"
            or context.identity.plan_schema_id != binding.plan.schema_id
            or context.identity.semantic_digest != binding.plan.semantic_digest
            or context.identity.wire_digest != binding.projection.wire_digest
            or context.identity.input_identity != context.input_identity
        ):
            return _blocked("shared_transition_binding_mismatch")
        try:
            outer_closure = closure_plan_from_json(binding.plan.closure_plan_json)
            validate_closure_plan_integrity(outer_closure)
        except (TypeError, ValueError):
            return _blocked("shared_transition_plan_invalid")
        if (
            plan != outer_closure
            or tuple(context.input_identity.output_mapping)
            != tuple(outer_closure.identity_context.output_mapping)
        ):
            return _blocked("shared_transition_binding_mismatch")
    if not isinstance(context.projection, ClosureProjection):
        return _blocked("shared_wire_projection_unavailable")
    if context.projection.wire_digest != plan.wire_digest:
        return _blocked("shared_wire_projection_mismatch")
    warnings = tuple(diagnostics_snapshot.saveability.warning_codes)
    if warnings and not shared_warning_confirmation_matches(
        diagnostics_snapshot,
        confirmed_warning_fingerprint,
    ):
        return SharedSaveGateResult(
            status="warning_confirmation_required",
            blocking_codes=(),
            warning_codes=warnings,
            fingerprint=fingerprint,
            context=context,
            diagnostics_snapshot=diagnostics_snapshot,
        )
    return SharedSaveGateResult(
        status="ready",
        blocking_codes=(),
        warning_codes=warnings,
        fingerprint=fingerprint,
        context=context,
        diagnostics_snapshot=diagnostics_snapshot,
    )


def validate_shared_save_request(request: VerifiedVmdSaveRequest) -> ClosureProjection:
    """Perform the worker-side independent producer validation before any temp write."""
    if not isinstance(request, VerifiedVmdSaveRequest):
        raise ValueError("verified VMD save request is invalid")
    plan = request.context.candidate.plan
    if not isinstance(plan, ClosurePlan):
        raise ValueError("verified VMD save request has no closure plan")
    return project_shared_output_context(request.context)


def _project_shared_output_context_and_view(
    context: SharedFinalOutputContext,
) -> tuple[ClosureProjection, SharedOutputConsumerView]:
    """Revalidate and project the complete shared output source for a worker."""
    if not isinstance(context, SharedFinalOutputContext):
        raise ValueError("shared final output context is invalid")
    consumer_view = shared_output_consumer_view(context)
    cleanup_binding = consumer_view.cleanup_binding
    if cleanup_binding is not None:
        final_plan_row = cleanup_binding.final_plan.to_dict()
        if (
            cleanup_binding.final_projection != context.projection
            or cleanup_binding.final_projection.wire_digest != context.identity.wire_digest
            or final_plan_row.get("semantic_digest") != context.identity.semantic_digest
            or final_plan_row.get("schema_id") != context.identity.plan_schema_id
        ):
            raise ValueError("captured cleanup projection differs from its validated final plan")
        return cleanup_binding.final_projection, consumer_view
    plan = context.candidate.plan
    if not isinstance(plan, ClosurePlan):
        raise ValueError("shared final output context has no closure wire view")
    if context.transition_binding is not None:
        binding = context.transition_binding
        if not isinstance(binding, TransitionSharedOutputBinding):
            raise ValueError("shared transition binding is invalid")
        validation = validate_transition_plan(
            binding.plan,
            issuer_context=binding.issuer_context,
            resolution=binding.resolution,
        )
        if validation.state != "valid" or validation != binding.validation:
            raise ValueError("transition plan no longer validates against its full issuer")
        try:
            transition_projection = project_validated_transition_plan(
                binding.plan,
                issuer_context=binding.issuer_context,
                resolution=binding.resolution,
            )
        except (AttributeError, TypeError, ValueError) as error:
            raise ValueError(
                "transition plan no longer validates against its full issuer"
            ) from error
        closure_plan = closure_plan_from_json(binding.plan.closure_plan_json)
        if (
            transition_projection != binding.projection
            or transition_projection.closure_projection != context.projection
            or closure_plan != plan
            or context.identity.plan_schema_id != binding.plan.schema_id
            or context.identity.semantic_digest != binding.plan.semantic_digest
            or context.identity.wire_digest != transition_projection.wire_digest
            or context.input_identity.transition_input_digest
            != binding.input_snapshot.input_digest
        ):
            raise ValueError("captured transition projection differs from its validated outer plan")
        return transition_projection.closure_projection, consumer_view
    if context.input_identity.transition_input_digest is not None:
        raise ValueError("transition input binding is missing from shared context")
    try:
        projection = project_validated_closure_candidate(
            context.candidate,
            context.issuer_context,
            plan.contract,
        )
    except (AttributeError, TypeError, ValueError) as error:
        raise ValueError(
            "closure plan no longer validates against its captured issuer"
        ) from error
    if projection != context.projection:
        raise ValueError("captured projection differs from the validated closure plan")
    return projection, consumer_view


def project_shared_output_context(
    context: SharedFinalOutputContext,
) -> ClosureProjection:
    """Revalidate and project the complete shared output source for a worker."""
    projection, _consumer_view = _project_shared_output_context_and_view(context)
    return projection


def validate_shared_output_readback(
    context: SharedFinalOutputContext,
    output_path: str | Path,
    *,
    model_name: str,
) -> VerifiedVmdEvidence:
    """Read back closure bytes and, for candidates, the outer transition result."""
    projection, consumer_view = _project_shared_output_context_and_view(context)
    if consumer_view.cleanup_binding is not None:
        from src.core.cleanup_shared_output import (
            CleanupSharedOutputBinding,
        )
        from src.vmd_writer.final_morph_cleanup_adapter import (
            project_validated_cleanup_plan,
            validate_cleanup_vmd_readback,
        )
        from src.vmd_writer.final_morph_key_reduction_adapter import (
            project_validated_key_reduction_plan,
            validate_key_reduction_vmd_readback,
        )
        from src.vmd_writer.verified_morph_output import VerifiedVmdEvidence

        binding = consumer_view.cleanup_binding
        if not isinstance(binding, CleanupSharedOutputBinding):
            raise ValueError("cleanup binding is invalid")
        if binding.final_plan_kind == "upstream":
            evidence = validate_shared_output_readback(
                binding.upstream_context, output_path, model_name=model_name
            )
            return dataclass_replace(
                evidence,
                semantic_digest=context.identity.semantic_digest,
                wire_digest=context.identity.wire_digest,
            )
        if binding.final_plan_kind == "event_cleanup":
            projected = project_validated_cleanup_plan(binding.event_plan, binding.event_issuer)
            result = validate_cleanup_vmd_readback(
                output_path, binding.event_plan, projected, model_name=model_name
            )
            if result.status != "passed" or result.wire_digest != context.identity.wire_digest:
                raise ValueError("cleanup VMD readback differs from the validated B2 plan")
            model_name_read = result.model_name
            record_count = result.record_count
            file_digest = result.sha256
            file_size = result.file_size_bytes
        elif binding.final_plan_kind == "key_reduction":
            projected = project_validated_key_reduction_plan(
                binding.reduction_plan, binding.reduction_issuer
            )
            result = validate_key_reduction_vmd_readback(
                output_path, projected, model_name=model_name
            )
            if result.status != "passed" or result.wire_digest != context.identity.wire_digest:
                raise ValueError("cleanup VMD readback differs from the validated B3 plan")
            model_name_read = result.model_name
            record_count = result.record_count
            file_digest = hashlib.sha256(Path(output_path).read_bytes()).hexdigest()
            file_size = Path(output_path).stat().st_size
        else:
            raise ValueError("cleanup final plan kind is unsupported")
        path = Path(output_path).resolve(strict=True)
        before = path.stat()
        payload = path.read_bytes()
        after = path.stat()
        identity_before = (
            getattr(before, "st_dev", None), getattr(before, "st_ino", None),
            getattr(before, "st_mtime_ns", None), int(before.st_size),
        )
        identity_after = (
            getattr(after, "st_dev", None), getattr(after, "st_ino", None),
            getattr(after, "st_mtime_ns", None), int(after.st_size),
        )
        if identity_before != identity_after or len(payload) != after.st_size:
            raise ValueError("cleanup VMD changed during independent readback")
        if hashlib.sha256(payload).hexdigest() != file_digest or after.st_size != file_size:
            raise ValueError("cleanup VMD file identity differs from readback evidence")
        closure = binding.upstream_context.candidate.plan
        return VerifiedVmdEvidence(
            path=path,
            file_size_bytes=len(payload),
            file_sha256=file_digest,
            file_identity=identity_after,
            model_name=model_name_read,
            output_mapping=context.input_identity.output_mapping,
            semantic_digest=context.identity.semantic_digest,
            wire_digest=context.identity.wire_digest,
            record_count=record_count,
            requirement_ids=tuple(item.requirement_id for item in closure.requirements),
            closure_verified=True,
        )
    plan = context.candidate.plan
    if not isinstance(plan, ClosurePlan):
        raise ValueError("shared final output context has no closure plan")
    evidence = validate_verified_morph_readback(
        output_path,
        projection,
        plan,
        model_name=model_name,
    )
    binding = context.transition_binding
    if binding is not None:
        if not isinstance(binding, TransitionSharedOutputBinding):
            raise ValueError("shared transition binding is invalid")
        validate_transition_vmd_readback(
            output_path,
            binding.plan,
            issuer_context=binding.issuer_context,
            resolution=binding.resolution,
            model_name=model_name,
            projection=binding.projection,
        )
    return evidence


__all__ = [
    "SaveCommitLease",
    "SharedSaveGateResult",
    "VerifiedVmdSaveRequest",
    "evaluate_shared_save_gate",
    "project_shared_output_context",
    "validate_shared_save_request",
    "validate_shared_output_readback",
]
