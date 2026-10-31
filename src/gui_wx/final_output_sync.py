from __future__ import annotations

import os
import threading
from dataclasses import dataclass, replace
from typing import Callable

import wx

from src.core.effective_shape_plan import (
    BaseTimingPlanInput,
    EffectiveShapePlan,
    resolve_effective_shape_plan,
)
from src.core.event_adjustment import AdjustmentLayerSnapshot
from src.core.final_morph_closure_plan import ClosureContract
from src.core.final_morph_closure_plan import ClosureIssue
from src.core.output_diagnostics import DiagnosticSnapshotInput
from src.core.preview_transform import _build_preview_data_from_validated_consumer_view
from src.core.final_output_projection import (
    FinalOutputSyncResult,
    TransitionSharedOutputBinding,
    build_closure_issuer_context,
    build_final_output_input_identity,
    build_shared_final_output_context,
    build_transition_shared_final_output_context,
    canonical_transition_generation_token,
    shared_output_consumer_view,
)
from src.core.cleanup_evaluation import CleanupEvaluationRequest
from src.core.cleanup_shared_output import (
    build_cleanup_shared_output,
    build_default_cleanup_shared_output,
)
from src.core.cleanup_default_policy import DefaultCleanupSelection
from src.core.cross_vowel_transition import TransitionInputSnapshot, TRANSITION_POLICY_V2
from src.core.transition_acoustic import TransitionAcousticSnapshot
from src.core.final_output_state import FinalOutputOrigin, FinalOutputState
from src.core.transition_evaluation import TransitionEvaluationRequest
from src.core.transition_default_policy import DefaultTransitionSelection
from src.core.pipeline import sha256_file
from gui_wx.output_diagnostics_adapter import (
    _build_shared_output_diagnostics_snapshot_from_consumer_view,
    build_shared_output_failure_diagnostics_snapshot,
)


def _failure_result(
    request: FinalOutputRequest,
    status: str,
    issues: tuple[ClosureIssue, ...],
    expected_transition_input_digest: str | None = None,
    *,
    expected_application_binding_digest: str | None = None,
    expected_cleanup_input_digest: str | None = None,
    expected_cleanup_application_binding_digest: str | None = None,
) -> FinalOutputSyncResult:
    try:
        diagnostics_snapshot = build_shared_output_failure_diagnostics_snapshot(
            request.diagnostics_seed,
            status=status,
            issues=issues,
        )
    except Exception:
        diagnostics_snapshot = None
    return FinalOutputSyncResult(
        status,
        issues=issues,
        diagnostics_snapshot=diagnostics_snapshot,
        expected_transition_input_digest=expected_transition_input_digest,
        expected_application_binding_digest=expected_application_binding_digest,
        expected_cleanup_input_digest=expected_cleanup_input_digest,
        expected_cleanup_application_binding_digest=expected_cleanup_application_binding_digest,
    )


def _normalized_path(value: str | os.PathLike[str] | None) -> str | None:
    if value is None:
        return None
    path = os.fspath(value)
    if not path:
        return None
    return os.path.normcase(os.path.abspath(os.path.normpath(path)))


@dataclass(frozen=True, slots=True)
class FinalOutputInputSnapshot:
    origin: FinalOutputOrigin
    manual_revision: int
    input_mode: str
    base_input: BaseTimingPlanInput
    adjustment_snapshot: AdjustmentLayerSnapshot
    effective_plan: EffectiveShapePlan | None
    resolved_profile_id: str | None
    output_morph_names: tuple[str, ...]
    source_audio_path: str | None
    analysis_wav_path: str | None
    normalized_text_path: str | None
    ticket: int
    lifecycle_epoch: int
    lifecycle_signature: tuple[object, ...] | None
    closure_contract: ClosureContract
    transition_evaluation_request: TransitionEvaluationRequest | None = None
    transition_acoustic_snapshot: TransitionAcousticSnapshot | None = None
    default_transition_selection: DefaultTransitionSelection | None = None
    cleanup_evaluation_request: CleanupEvaluationRequest | None = None
    default_cleanup_selection: DefaultCleanupSelection | None = None
    resolve_effective_plan_in_worker: bool = False

    def __post_init__(self) -> None:
        if not isinstance(self.origin, FinalOutputOrigin):
            raise ValueError("origin is invalid")
        if isinstance(self.manual_revision, bool) or not isinstance(self.manual_revision, int) or self.manual_revision < 0:
            raise ValueError("manual_revision must be a non-negative integer")
        if self.input_mode not in {"text_audio", "voice_only"}:
            raise ValueError("input_mode is unsupported")
        if not isinstance(self.base_input, BaseTimingPlanInput):
            raise ValueError("base_input is invalid")
        if not isinstance(self.adjustment_snapshot, AdjustmentLayerSnapshot):
            raise ValueError("adjustment_snapshot is invalid")
        if self.transition_evaluation_request is not None and not isinstance(
            self.transition_evaluation_request, TransitionEvaluationRequest
        ):
            raise ValueError("transition_evaluation_request is invalid")
        if self.default_transition_selection is not None and not isinstance(
            self.default_transition_selection, DefaultTransitionSelection
        ):
            raise ValueError("default_transition_selection is invalid")
        if self.cleanup_evaluation_request is not None and not isinstance(
            self.cleanup_evaluation_request, CleanupEvaluationRequest
        ):
            raise ValueError("cleanup_evaluation_request is invalid")
        if self.default_cleanup_selection is not None and not isinstance(
            self.default_cleanup_selection, DefaultCleanupSelection
        ):
            raise ValueError("default_cleanup_selection is invalid")
        if self.cleanup_evaluation_request is not None and (
            self.transition_evaluation_request is not None
            or self.default_transition_selection is None
            or self.default_cleanup_selection is not None
        ):
            raise ValueError("cleanup candidates require only the adopted MS32 upstream selection")
        if self.default_cleanup_selection is not None and (
            self.transition_evaluation_request is not None
            or self.cleanup_evaluation_request is not None
        ):
            raise ValueError("adopted cleanup default cannot be combined with an explicit evaluation")
        if self.transition_evaluation_request is not None and self.default_transition_selection is not None:
            raise ValueError("explicit evaluation and adopted default cannot be selected together")
        bounded_policy = (
            self.transition_evaluation_request.policy
            if self.transition_evaluation_request is not None
            else self.default_transition_selection.binding.policy
            if self.default_transition_selection is not None
            and self.default_transition_selection.selection_kind == "transition"
            else None
        )
        bounded = bounded_policy is not None and bounded_policy.policy_id == TRANSITION_POLICY_V2
        if type(self.resolve_effective_plan_in_worker) is not bool:
            raise ValueError("resolve_effective_plan_in_worker must be a bool")
        if (
            not isinstance(self.effective_plan, EffectiveShapePlan)
            and not (
                self.effective_plan is None
                and (bounded or self.resolve_effective_plan_in_worker)
            )
        ):
            raise ValueError("effective_plan is invalid")
        if self.effective_plan is not None and self.effective_plan.canonical_adjustment_snapshot != self.adjustment_snapshot:
            raise ValueError("effective plan and adjustment snapshot differ")
        if not isinstance(self.closure_contract, ClosureContract):
            raise ValueError("closure_contract is invalid")
        if self.transition_acoustic_snapshot is not None and not isinstance(
            self.transition_acoustic_snapshot, TransitionAcousticSnapshot
        ):
            raise ValueError("transition_acoustic_snapshot is invalid")
        requires_acoustic = self.transition_evaluation_request is not None or bounded
        if requires_acoustic != (self.transition_acoustic_snapshot is not None):
            raise ValueError("selected transition route and acoustic evidence must be supplied together")
        if (
            self.default_transition_selection is not None
            and self.default_transition_selection.input_mode != self.input_mode
        ):
            raise ValueError("default transition selection differs from input mode")
        if self.lifecycle_signature is not None and not isinstance(
            self.lifecycle_signature, tuple
        ):
            raise ValueError("lifecycle_signature must be a tuple or None")
        for name in ("ticket", "lifecycle_epoch"):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, int) or value < 0:
                raise ValueError(f"{name} must be a non-negative integer")


@dataclass(frozen=True, slots=True)
class FinalOutputRequest:
    snapshot: FinalOutputInputSnapshot
    diagnostics_seed: DiagnosticSnapshotInput


def _build_selected_shared_output_result(
    request: FinalOutputRequest,
    *,
    cancelled=None,
    _include_consumers: bool = True,
) -> FinalOutputSyncResult:
    snapshot = request.snapshot
    transition_policy = (
        snapshot.transition_evaluation_request.policy
        if snapshot.transition_evaluation_request is not None
        else snapshot.default_transition_selection.binding.policy
        if snapshot.default_transition_selection is not None
        and snapshot.default_transition_selection.selection_kind == "transition"
        else None
    )
    bounded_policy = (
        transition_policy is not None
        and transition_policy.policy_id == TRANSITION_POLICY_V2
    )
    if (
        snapshot.resolve_effective_plan_in_worker
        and not bounded_policy
        and snapshot.effective_plan is None
    ):
        if cancelled is not None and cancelled():
            return FinalOutputSyncResult("stale")
        try:
            effective_plan = resolve_effective_shape_plan(
                snapshot.base_input,
                snapshot.adjustment_snapshot,
            )
        except Exception as error:
            return _failure_result(
                request,
                "unavailable",
                (ClosureIssue(
                    "capture_unavailable",
                    "automatic_shape_reresolution",
                    f"{type(error).__name__}: {error}",
                ),),
            )
        snapshot = replace(snapshot, effective_plan=effective_plan)
        request = FinalOutputRequest(snapshot, request.diagnostics_seed)
    if cancelled is not None and cancelled():
        return FinalOutputSyncResult("stale")
    if (
        snapshot.cleanup_evaluation_request is not None
        or snapshot.default_cleanup_selection is not None
    ):
        upstream_snapshot = replace(
            snapshot,
            cleanup_evaluation_request=None,
            default_cleanup_selection=None,
        )
        upstream_result = _build_selected_shared_output_result(
            FinalOutputRequest(upstream_snapshot, request.diagnostics_seed),
            cancelled=cancelled,
            _include_consumers=False,
        )
        if upstream_result.status != "valid" or upstream_result.context is None:
            return upstream_result
        try:
            if snapshot.cleanup_evaluation_request is not None:
                context = build_cleanup_shared_output(
                    upstream_result.context,
                    snapshot.cleanup_evaluation_request,
                    snapshot,
                    cancelled=cancelled,
                )
            else:
                context = build_default_cleanup_shared_output(
                    upstream_result.context,
                    snapshot.default_cleanup_selection,
                    snapshot,
                    cancelled=cancelled,
                )
            preview_data = None
            diagnostics_snapshot = None
            if _include_consumers:
                consumer_view = shared_output_consumer_view(context)
                preview_data = _build_preview_data_from_validated_consumer_view(
                    context,
                    consumer_view,
                )
                diagnostics_snapshot = _build_shared_output_diagnostics_snapshot_from_consumer_view(
                    request.diagnostics_seed,
                    context,
                    consumer_view,
                )
            cleanup_digest = context.input_identity.cleanup_input_digest
            return FinalOutputSyncResult(
                "valid",
                context=context,
                preview_data=preview_data,
                diagnostics_snapshot=diagnostics_snapshot,
                expected_transition_input_digest=upstream_result.expected_transition_input_digest,
                expected_application_binding_digest=upstream_result.expected_application_binding_digest,
                expected_cleanup_input_digest=cleanup_digest,
                expected_cleanup_application_binding_digest=(
                    None
                    if snapshot.default_cleanup_selection is None
                    else snapshot.default_cleanup_selection.selection_digest
                ),
            )
        except Exception as error:
            return _failure_result(
                request,
                "unavailable",
                (ClosureIssue(
                    "capture_unavailable",
                    "cleanup_request",
                    f"{type(error).__name__}: {error}",
                ),),
                upstream_result.expected_transition_input_digest,
                expected_application_binding_digest=upstream_result.expected_application_binding_digest,
                expected_cleanup_application_binding_digest=(
                    None
                    if snapshot.default_cleanup_selection is None
                    else snapshot.default_cleanup_selection.selection_digest
                ),
            )
    expected_transition_input_digest: str | None = None
    default_selection = snapshot.default_transition_selection
    expected_application_binding_digest = (
        None if default_selection is None else default_selection.selection_digest
    )
    try:
        transition_policy = (
            snapshot.transition_evaluation_request.policy
            if snapshot.transition_evaluation_request is not None
            else default_selection.binding.policy
            if default_selection is not None and default_selection.selection_kind == "transition"
            else None
        )
        bounded = transition_policy is not None and transition_policy.policy_id == TRANSITION_POLICY_V2
        issuer_context = None if bounded else build_closure_issuer_context(
            origin=snapshot.origin,
            base_input=snapshot.base_input,
            adjustment_snapshot=snapshot.adjustment_snapshot,
            effective_plan=snapshot.effective_plan,
            manual_revision=snapshot.manual_revision,
            resolved_profile_id=snapshot.resolved_profile_id,
            output_morph_names=snapshot.output_morph_names,
        )
        if snapshot.transition_evaluation_request is not None or bounded:
            acoustic = snapshot.transition_acoustic_snapshot
            if acoustic is None or snapshot.analysis_wav_path is None:
                raise ValueError("candidate analysis WAV or acoustic evidence is unavailable")
            current_wav_digest = sha256_file(snapshot.analysis_wav_path)
            if (
                acoustic.analysis_wav_sha256 != current_wav_digest
                or acoustic.source_sha256_before != current_wav_digest
                or acoustic.source_sha256_after != current_wav_digest
            ):
                return _failure_result(
                    request,
                    "invalid",
                    (
                        ClosureIssue(
                            "identity_mismatch",
                            "transition_acoustic",
                            "accepted analysis WAV differs from the acoustic snapshot",
                        ),
                    ),
                    expected_application_binding_digest=(
                        expected_application_binding_digest
                    ),
                )
            transition_input_snapshot = TransitionInputSnapshot(
                run_id=snapshot.origin.source_run_id,
                analysis_generation=canonical_transition_generation_token(
                    snapshot.origin.analysis_generation
                ),
                manual_revision=snapshot.manual_revision,
                input_mode=snapshot.input_mode,
                analysis_wav_sha256=current_wav_digest,
                base_plan_digest=snapshot.origin.base_plan_digest,
                policy=transition_policy,
                acoustic=acoustic,
            )
            expected_transition_input_digest = transition_input_snapshot.input_digest
            if bounded:
                from src.core.bounded_transition import build_bounded_shared_output
                result = build_bounded_shared_output(
                    origin=snapshot.origin, base_input=snapshot.base_input,
                    adjustment_snapshot=snapshot.adjustment_snapshot,
                    input_snapshot=transition_input_snapshot,
                    evaluation_request=snapshot.transition_evaluation_request,
                    default_selection=default_selection,
                    resolved_profile_id=snapshot.resolved_profile_id,
                    output_morph_names=snapshot.output_morph_names,
                    normalized_text_path=snapshot.normalized_text_path,
                    closure_contract=snapshot.closure_contract,
                    ticket=snapshot.ticket,lifecycle_epoch=snapshot.lifecycle_epoch,
                    lifecycle_signature=snapshot.lifecycle_signature,cancelled=cancelled)
            else:
                result = build_transition_shared_final_output_context(
                    origin=snapshot.origin,
                    manual_revision=snapshot.manual_revision,
                    input_mode=snapshot.input_mode,
                    normalized_text_path=snapshot.normalized_text_path,
                    issuer_context=issuer_context,
                    closure_contract=snapshot.closure_contract,
                    transition_request=snapshot.transition_evaluation_request,
                    transition_input_snapshot=transition_input_snapshot,
                    ticket=snapshot.ticket,
                    lifecycle_epoch=snapshot.lifecycle_epoch,
                    lifecycle_signature=snapshot.lifecycle_signature,
                )
        else:
            input_identity = build_final_output_input_identity(
                origin=snapshot.origin,
                manual_revision=snapshot.manual_revision,
                input_mode=snapshot.input_mode,
                normalized_text_path=snapshot.normalized_text_path,
                issuer_context=issuer_context,
                closure_contract=snapshot.closure_contract,
                application_binding_digest=expected_application_binding_digest,
            )
            result = build_shared_final_output_context(
                issuer_context,
                snapshot.closure_contract,
                input_identity,
                ticket=snapshot.ticket,
                lifecycle_epoch=snapshot.lifecycle_epoch,
                lifecycle_signature=snapshot.lifecycle_signature,
                default_selection=default_selection,
            )
        if result.status != "valid" or result.context is None:
            return _failure_result(
                request,
                result.status,
                result.issues,
                result.expected_transition_input_digest
                or expected_transition_input_digest,
                expected_application_binding_digest=expected_application_binding_digest,
            )
        if cancelled is not None and cancelled():
            return FinalOutputSyncResult("stale")
        preview_data = None
        diagnostics_snapshot = None
        if _include_consumers:
            consumer_view = shared_output_consumer_view(result.context)
            preview_data = _build_preview_data_from_validated_consumer_view(
                result.context,
                consumer_view,
            )
            diagnostics_snapshot = _build_shared_output_diagnostics_snapshot_from_consumer_view(
                request.diagnostics_seed,
                result.context,
                consumer_view,
            )
        return FinalOutputSyncResult(
            "valid",
            context=result.context,
            issues=result.issues,
            preview_data=preview_data,
            diagnostics_snapshot=diagnostics_snapshot,
            expected_transition_input_digest=(
                result.expected_transition_input_digest
                or expected_transition_input_digest
            ),
            expected_application_binding_digest=(
                result.expected_application_binding_digest
                or expected_application_binding_digest
            ),
        )
    except Exception as error:
        return _failure_result(
            request,
            "unavailable",
            (
                ClosureIssue(
                    "capture_unavailable",
                    "request_capture",
                    f"{type(error).__name__}: {error}",
                ),
            ),
            expected_transition_input_digest=expected_transition_input_digest,
            expected_application_binding_digest=expected_application_binding_digest,
        )


def build_default_shared_final_output_context(
    request: FinalOutputRequest,
    *,
    cancelled=None,
) -> FinalOutputSyncResult:
    """Build a context bound to the adopted default selection and its scope."""
    if not isinstance(request, FinalOutputRequest):
        return FinalOutputSyncResult("invalid")
    if request.snapshot.default_transition_selection is None:
        return FinalOutputSyncResult("invalid")
    return _build_selected_shared_output_result(request, cancelled=cancelled)


def _build_request_result(
    request: FinalOutputRequest,
    *,
    cancelled=None,
) -> FinalOutputSyncResult:
    if request.snapshot.default_transition_selection is not None:
        return build_default_shared_final_output_context(
            request,
            cancelled=cancelled,
        )
    return _build_selected_shared_output_result(request, cancelled=cancelled)


class FinalOutputSyncCoordinator:
    """Run at most one immutable final-output build and retain only the latest request."""

    def __init__(
        self,
        result_callback: Callable[[FinalOutputRequest, FinalOutputSyncResult], None],
        *,
        call_after: Callable[..., None] = wx.CallAfter,
    ) -> None:
        if not callable(result_callback):
            raise TypeError("result_callback must be callable")
        if not callable(call_after):
            raise TypeError("call_after must be callable")
        self._result_callback = result_callback
        self._call_after = call_after
        self._lock = threading.Lock()
        self._active = False
        self._active_request: FinalOutputRequest | None = None
        self._latest_request: FinalOutputRequest | None = None
        self._cancelled_tickets: set[int] = set()
        self._closed = False

    @property
    def is_active(self) -> bool:
        with self._lock:
            return self._active

    def request(self, request: FinalOutputRequest) -> bool:
        if not isinstance(request, FinalOutputRequest):
            raise TypeError("request must be FinalOutputRequest")
        start_now = False
        with self._lock:
            if self._closed:
                return False
            self._latest_request = request
            if not self._active:
                self._active = True
                self._latest_request = None
                start_now = True
        if start_now:
            self._start_worker(request)
        return True

    def _start_worker(self, request: FinalOutputRequest) -> None:
        with self._lock:
            self._active_request = request
        worker = threading.Thread(
            target=self._run_worker,
            args=(request,),
            name=f"ms31-final-output-{request.snapshot.ticket}",
            daemon=True,
        )
        try:
            worker.start()
        except RuntimeError:
            result = FinalOutputSyncResult("unavailable")
            try:
                self._call_after(self._finish_request, request, result)
            except Exception:
                with self._lock:
                    self._active = False
                    self._latest_request = None
                    self._closed = True

    def _run_worker(self, request: FinalOutputRequest) -> None:
        bounded = (request.snapshot.transition_evaluation_request is not None
                   and request.snapshot.transition_evaluation_request.policy.policy_id == TRANSITION_POLICY_V2)
        cleanup_candidate = request.snapshot.cleanup_evaluation_request is not None
        cancelled = (
            (lambda: self._bounded_request_cancelled(request))
            if bounded or cleanup_candidate
            else (lambda: self._request_cancelled(request))
        )
        result = _build_request_result(request, cancelled=cancelled)
        try:
            self._call_after(self._finish_request, request, result)
        except Exception:
            with self._lock:
                self._active = False
                self._latest_request = None
                self._closed = True

    def _bounded_request_cancelled(
        self,
        request: FinalOutputRequest,
    ) -> bool:
        with self._lock:
            return (
                self._closed
                or self._latest_request is not None
                or request.snapshot.ticket in self._cancelled_tickets
            )

    def _request_cancelled(self, request: FinalOutputRequest) -> bool:
        with self._lock:
            return self._closed or request.snapshot.ticket in self._cancelled_tickets

    def cancel(self, request: FinalOutputRequest) -> bool:
        """Discard a pending request result and signal cooperative worker stages."""
        if not isinstance(request, FinalOutputRequest):
            return False
        notify_cancelled = False
        with self._lock:
            if self._closed:
                return False
            self._cancelled_tickets.add(request.snapshot.ticket)
            if self._latest_request == request:
                self._latest_request = None
                if self._active_request != request:
                    notify_cancelled = True
        if notify_cancelled:
            result = FinalOutputSyncResult("stale")
            try:
                self._call_after(self._result_callback, request, result)
            except Exception:
                with self._lock:
                    self._cancelled_tickets.discard(request.snapshot.ticket)
                return False
            with self._lock:
                self._cancelled_tickets.discard(request.snapshot.ticket)
        return True

    def _finish_request(
        self,
        request: FinalOutputRequest,
        result: FinalOutputSyncResult,
    ) -> None:
        next_request: FinalOutputRequest | None = None
        with self._lock:
            if self._closed:
                self._active = False
                self._active_request = None
                self._latest_request = None
                return
            self._active_request = None
            self._cancelled_tickets.discard(request.snapshot.ticket)
            latest = self._latest_request
            self._latest_request = None
            if latest is None:
                self._active = False
            else:
                next_request = latest
        try:
            self._result_callback(request, result)
        finally:
            if next_request is not None:
                self._start_worker(next_request)

    def close(self) -> None:
        with self._lock:
            self._closed = True
            self._active = False
            self._active_request = None
            self._latest_request = None
            self._cancelled_tickets.clear()


def request_shared_final_output(
    *,
    lifecycle: FinalOutputState,
    coordinator: FinalOutputSyncCoordinator,
    input_mode: str,
    base_input: BaseTimingPlanInput,
    adjustment_snapshot: AdjustmentLayerSnapshot,
    effective_plan: EffectiveShapePlan | None,
    resolved_profile_id: str | None,
    output_morph_names: tuple[str, ...],
    source_audio_path: str | os.PathLike[str] | None,
    analysis_wav_path: str | os.PathLike[str] | None,
    text_path: str | os.PathLike[str] | None,
    analysis_result_valid: bool,
    analysis_pending_rebuild: bool,
    is_busy: bool,
    closure_contract: ClosureContract | None = None,
    lifecycle_signature: tuple[object, ...] | None = None,
    diagnostics_seed: DiagnosticSnapshotInput | None = None,
    transition_evaluation_request: TransitionEvaluationRequest | None = None,
    transition_acoustic_snapshot: TransitionAcousticSnapshot | None = None,
    default_transition_selection: DefaultTransitionSelection | None = None,
    cleanup_evaluation_request: CleanupEvaluationRequest | None = None,
    default_cleanup_selection: DefaultCleanupSelection | None = None,
    resolve_effective_plan_in_worker: bool = False,
) -> FinalOutputRequest | None:
    """Capture one coherent UI snapshot, then submit only immutable values to the worker."""
    if not isinstance(lifecycle, FinalOutputState):
        return None
    if (
        not isinstance(coordinator, FinalOutputSyncCoordinator)
        or is_busy
        or not analysis_result_valid
        or analysis_pending_rebuild
        or not lifecycle.is_accepted
        or not isinstance(diagnostics_seed, DiagnosticSnapshotInput)
    ):
        lifecycle.invalidate_context()
        return None
    origin = lifecycle.accepted_origin
    adjustment_snapshot_current = lifecycle.manual_snapshot
    if (
        origin is None
        or lifecycle.manual_revision is None
        or adjustment_snapshot_current != adjustment_snapshot
        or origin.base_plan_digest != adjustment_snapshot.base_plan_identity.digest
        or adjustment_snapshot.base_plan_identity.digest != lifecycle.manual_snapshot_base_digest
        or input_mode != origin.input_mode
        or _normalized_path(source_audio_path) != _normalized_path(origin.source_audio_path)
        or _normalized_path(analysis_wav_path) != _normalized_path(origin.analysis_wav_path)
        or _normalized_path(text_path) != _normalized_path(origin.text_path)
    ):
        lifecycle.invalidate_context()
        return None
    if lifecycle_signature is not None and not isinstance(lifecycle_signature, tuple):
        return None
    contract = closure_contract or ClosureContract()
    ticket, epoch = lifecycle.next_request_ticket()
    normalized_text_path = _normalized_path(text_path)
    try:
        snapshot = FinalOutputInputSnapshot(
            origin=origin,
            manual_revision=lifecycle.manual_revision,
            input_mode=input_mode,
            base_input=base_input,
            adjustment_snapshot=adjustment_snapshot,
            effective_plan=effective_plan,
            resolved_profile_id=resolved_profile_id,
            output_morph_names=tuple(output_morph_names),
            source_audio_path=_normalized_path(source_audio_path),
            analysis_wav_path=_normalized_path(analysis_wav_path),
            normalized_text_path=normalized_text_path,
            ticket=ticket,
            lifecycle_epoch=epoch,
            lifecycle_signature=lifecycle_signature,
            closure_contract=contract,
            transition_evaluation_request=transition_evaluation_request,
            transition_acoustic_snapshot=transition_acoustic_snapshot,
            default_transition_selection=default_transition_selection,
            cleanup_evaluation_request=cleanup_evaluation_request,
            default_cleanup_selection=default_cleanup_selection,
            resolve_effective_plan_in_worker=resolve_effective_plan_in_worker,
        )
        request = FinalOutputRequest(
            snapshot=snapshot,
            diagnostics_seed=diagnostics_seed,
        )
    except (AttributeError, TypeError, ValueError, RuntimeError, OverflowError):
        lifecycle.invalidate_context()
        return None
    if not coordinator.request(request):
        return None
    return request


def apply_shared_final_output_result(
    *,
    lifecycle: FinalOutputState,
    request: FinalOutputRequest,
    result: FinalOutputSyncResult,
    current_lifecycle_signature: tuple[object, ...] | None = None,
) -> bool:
    if (
        not isinstance(lifecycle, FinalOutputState)
        or not isinstance(request, FinalOutputRequest)
        or not isinstance(result, FinalOutputSyncResult)
    ):
        return False
    if result.status != "valid" or result.context is None:
        return False
    if not lifecycle.is_current_request(
        request.snapshot.ticket, request.snapshot.lifecycle_epoch
    ):
        return False
    if (
        request.snapshot.lifecycle_signature is not None
        and current_lifecycle_signature != request.snapshot.lifecycle_signature
    ):
        lifecycle.invalidate_context()
        return False
    if (
        result.context.lifecycle_signature != request.snapshot.lifecycle_signature
        or result.context.ticket != request.snapshot.ticket
        or result.context.lifecycle_epoch != request.snapshot.lifecycle_epoch
    ):
        return False
    binding = result.context.transition_binding
    explicit_request = request.snapshot.transition_evaluation_request
    default_selection = request.snapshot.default_transition_selection
    cleanup_request = request.snapshot.cleanup_evaluation_request
    default_cleanup_selection = request.snapshot.default_cleanup_selection
    identity = result.context.input_identity
    cleanup_binding = result.context.cleanup_binding
    if cleanup_request is None and default_cleanup_selection is None:
        if (
            cleanup_binding is not None
            or identity.cleanup_input_digest is not None
            or identity.cleanup_application_binding_digest is not None
            or result.expected_cleanup_input_digest is not None
            or result.expected_cleanup_application_binding_digest is not None
        ):
            return False
    elif cleanup_request is not None and (
        cleanup_binding is None
        or cleanup_binding.request != cleanup_request
        or cleanup_binding.default_selection is not None
        or identity.cleanup_input_digest != cleanup_binding.input_digest
        or identity.cleanup_application_binding_digest is not None
        or result.expected_cleanup_input_digest != cleanup_binding.input_digest
        or result.expected_cleanup_application_binding_digest is not None
    ):
        return False
    elif default_cleanup_selection is not None and (
        cleanup_binding is None
        or cleanup_binding.request is not None
        or cleanup_binding.default_selection != default_cleanup_selection
        or identity.cleanup_input_digest != cleanup_binding.input_digest
        or identity.cleanup_application_binding_digest != default_cleanup_selection.selection_digest
        or result.expected_cleanup_input_digest != cleanup_binding.input_digest
        or result.expected_cleanup_application_binding_digest != default_cleanup_selection.selection_digest
    ):
        return False
    if default_selection is None:
        if (
            result.context.default_selection is not None
            or identity.application_binding_digest is not None
            or result.expected_application_binding_digest is not None
        ):
            return False
        if explicit_request is None:
            if binding is not None or result.expected_transition_input_digest is not None:
                return False
        elif not isinstance(binding, TransitionSharedOutputBinding):
            return False
    else:
        if (
            result.context.default_selection != default_selection
            or identity.application_binding_digest != default_selection.selection_digest
            or result.expected_application_binding_digest != default_selection.selection_digest
        ):
            return False
        if default_selection.selection_kind == "scope_excluded":
            if binding is not None or result.expected_transition_input_digest is not None:
                return False
        elif (
            not isinstance(binding, TransitionSharedOutputBinding)
            or binding.default_selection != default_selection
            or binding.evaluation_request is not None
        ):
            return False
    if explicit_request is not None or (
        default_selection is not None
        and default_selection.selection_kind == "transition"
    ):
        acoustic = request.snapshot.transition_acoustic_snapshot
        if not isinstance(binding, TransitionSharedOutputBinding) or acoustic is None:
            return False
        transition_input = binding.input_snapshot
        origin = request.snapshot.origin
        expected_policy = (
            explicit_request.policy
            if explicit_request is not None
            else default_selection.binding.policy
        )
        if (
            binding.evaluation_request != explicit_request
            or transition_input.run_id != origin.source_run_id
            or transition_input.analysis_generation
            != canonical_transition_generation_token(origin.analysis_generation)
            or transition_input.manual_revision != request.snapshot.manual_revision
            or transition_input.input_mode != request.snapshot.input_mode
            or transition_input.base_plan_digest != origin.base_plan_digest
            or transition_input.policy != expected_policy
            or transition_input.acoustic != acoustic
            or transition_input.input_digest
            != result.expected_transition_input_digest
            or result.context.input_identity.transition_input_digest
            != result.expected_transition_input_digest
        ):
            return False
    return lifecycle.apply_context(
        result.context,
        ticket=request.snapshot.ticket,
        epoch=request.snapshot.lifecycle_epoch,
        expected_transition_input_digest=result.expected_transition_input_digest,
        expected_application_binding_digest=result.expected_application_binding_digest,
        expected_cleanup_input_digest=result.expected_cleanup_input_digest,
        expected_cleanup_application_binding_digest=(
            result.expected_cleanup_application_binding_digest
        ),
    )


__all__ = [
    "FinalOutputInputSnapshot",
    "FinalOutputRequest",
    "FinalOutputSyncCoordinator",
    "apply_shared_final_output_result",
    "build_default_shared_final_output_context",
    "request_shared_final_output",
]
