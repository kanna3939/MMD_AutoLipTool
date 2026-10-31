from __future__ import annotations

import hashlib
import json
import os
import uuid
from dataclasses import dataclass, replace
from typing import Any


def _require_non_empty_text(value: object, name: str) -> str:
    if type(value) is not str or not value:
        raise ValueError(f"{name} must be non-empty text")
    return value


def _require_non_negative_int(value: object, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(f"{name} must be a non-negative integer")
    return value


def _optional_path(value: object, name: str) -> str | None:
    if value is None:
        return None
    if type(value) is not str or not value:
        raise ValueError(f"{name} must be non-empty text or None")
    return value


def _normalize_path(value: str | None) -> str | None:
    if value is None:
        return None
    return os.path.normcase(os.path.abspath(os.path.normpath(value)))


def _snapshot_base_digest(snapshot: object) -> str | None:
    identity = getattr(snapshot, "base_plan_identity", None)
    digest = getattr(identity, "digest", None)
    return digest if type(digest) is str and digest else None


@dataclass(frozen=True, slots=True)
class FinalOutputOrigin:
    """Product-owned identity for one analysis attempt and its accepted result."""

    source_run_id: str
    job_id: int
    analysis_generation: int
    input_mode: str
    input_binding_digest: str
    source_audio_path: str | None
    analysis_wav_path: str | None
    text_path: str | None
    analysis_result_id: str | None = None
    base_plan_digest: str | None = None

    def __post_init__(self) -> None:
        _require_non_empty_text(self.source_run_id, "source_run_id")
        _require_non_negative_int(self.job_id, "job_id")
        _require_non_negative_int(self.analysis_generation, "analysis_generation")
        if self.input_mode not in {"text_audio", "voice_only"}:
            raise ValueError("input_mode is unsupported")
        if (
            type(self.input_binding_digest) is not str
            or len(self.input_binding_digest) != 64
            or any(char not in "0123456789abcdef" for char in self.input_binding_digest)
        ):
            raise ValueError("input_binding_digest must be a lowercase SHA-256 digest")
        _optional_path(self.source_audio_path, "source_audio_path")
        _optional_path(self.analysis_wav_path, "analysis_wav_path")
        _optional_path(self.text_path, "text_path")
        if self.analysis_result_id is not None:
            _require_non_empty_text(self.analysis_result_id, "analysis_result_id")
        if self.base_plan_digest is not None and (
            type(self.base_plan_digest) is not str
            or len(self.base_plan_digest) != 64
            or any(char not in "0123456789abcdef" for char in self.base_plan_digest)
        ):
            raise ValueError("base_plan_digest must be a lowercase SHA-256 digest")


@dataclass(slots=True)
class FinalOutputState:
    """Own analysis origins, monotonic manual revisions, and request epochs.

    This state is deliberately separate from debug traces, editor revisions,
    and history lengths. It does not infer a missing adjustment snapshot.
    """

    accepted_origin: FinalOutputOrigin | None = None
    pending_origin: FinalOutputOrigin | None = None
    manual_revision: int | None = None
    manual_snapshot: object | None = None
    manual_snapshot_known: bool = False
    manual_snapshot_base_digest: str | None = None
    lifecycle_epoch: int = 0
    request_ticket: int = 0
    current_context: object | None = None
    expected_transition_input_digest: str | None = None
    expected_application_binding_digest: str | None = None
    expected_cleanup_input_digest: str | None = None
    expected_cleanup_application_binding_digest: str | None = None
    unavailable_reason: str | None = None
    _generation_counter: int = 0

    def begin_analysis(
        self,
        *,
        job_id: int,
        input_mode: str,
        source_audio_path: str | None,
        analysis_wav_path: str | None,
        text_path: str | None,
        analysis_text: str,
    ) -> FinalOutputOrigin:
        _require_non_negative_int(job_id, "job_id")
        if input_mode not in {"text_audio", "voice_only"}:
            raise ValueError("input_mode is unsupported")
        if type(analysis_text) is not str:
            raise ValueError("analysis_text must be text")
        source_audio_path = _normalize_path(
            _optional_path(source_audio_path, "source_audio_path")
        )
        analysis_wav_path = _normalize_path(
            _optional_path(analysis_wav_path, "analysis_wav_path")
        )
        text_path = _normalize_path(_optional_path(text_path, "text_path"))
        text_digest = hashlib.sha256(analysis_text.encode("utf-8")).hexdigest()
        payload = {
            "input_mode": input_mode,
            "source_audio_path": source_audio_path,
            "analysis_wav_path": analysis_wav_path,
            "text_path": text_path,
            "analysis_text_digest": text_digest,
        }
        binding_digest = hashlib.sha256(
            json.dumps(
                payload,
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
        ).hexdigest()
        self._generation_counter += 1
        origin = FinalOutputOrigin(
            source_run_id=uuid.uuid4().hex,
            job_id=job_id,
            analysis_generation=self._generation_counter,
            input_mode=input_mode,
            input_binding_digest=binding_digest,
            source_audio_path=source_audio_path,
            analysis_wav_path=analysis_wav_path,
            text_path=text_path,
        )
        self.pending_origin = origin
        self.lifecycle_epoch += 1
        self.request_ticket += 1
        self.current_context = None
        self.expected_transition_input_digest = None
        self.expected_application_binding_digest = None
        self.expected_cleanup_input_digest = None
        self.expected_cleanup_application_binding_digest = None
        self.unavailable_reason = None
        return origin

    def accept_analysis(
        self,
        *,
        job_id: int,
        adjustment_snapshot: object,
        analysis_result_id: str,
    ) -> FinalOutputOrigin | None:
        pending = self.pending_origin
        if pending is None or pending.job_id != job_id:
            return None
        if (
            adjustment_snapshot is None
            or getattr(adjustment_snapshot, "adjustments", None) != ()
        ):
            self.unavailable_reason = "initial_empty_snapshot_unavailable"
            self.pending_origin = None
            self.lifecycle_epoch += 1
            self.request_ticket += 1
            return None
        base_digest = _snapshot_base_digest(adjustment_snapshot)
        if base_digest is None:
            self.unavailable_reason = "initial_base_identity_unavailable"
            self.pending_origin = None
            self.lifecycle_epoch += 1
            self.request_ticket += 1
            return None
        try:
            accepted = replace(
                pending,
                analysis_result_id=_require_non_empty_text(
                    analysis_result_id, "analysis_result_id"
                ),
                base_plan_digest=base_digest,
            )
        except (TypeError, ValueError):
            self.unavailable_reason = "analysis_result_identity_invalid"
            self.pending_origin = None
            self.lifecycle_epoch += 1
            self.request_ticket += 1
            return None
        self.accepted_origin = accepted
        self.pending_origin = None
        self.manual_revision = 0
        self.manual_snapshot = adjustment_snapshot
        self.manual_snapshot_known = True
        self.manual_snapshot_base_digest = base_digest
        self.unavailable_reason = None
        self.current_context = None
        self.expected_transition_input_digest = None
        self.expected_application_binding_digest = None
        self.expected_cleanup_input_digest = None
        self.expected_cleanup_application_binding_digest = None
        self.lifecycle_epoch += 1
        self.request_ticket += 1
        return accepted

    def discard_pending_analysis(self, *, job_id: int | None = None) -> bool:
        pending = self.pending_origin
        if pending is None or (job_id is not None and pending.job_id != job_id):
            return False
        self.pending_origin = None
        self.lifecycle_epoch += 1
        self.request_ticket += 1
        self.current_context = None
        self.expected_transition_input_digest = None
        self.expected_application_binding_digest = None
        self.expected_cleanup_input_digest = None
        self.expected_cleanup_application_binding_digest = None
        return True

    def observe_manual_snapshot(self, snapshot: object | None) -> bool:
        """Observe a successfully committed snapshot without guessing gaps."""
        if self.accepted_origin is None:
            return True
        if snapshot is None:
            self.manual_snapshot_known = False
            self.unavailable_reason = "manual_snapshot_missing"
            self.lifecycle_epoch += 1
            self.request_ticket += 1
            self.current_context = None
            self.expected_transition_input_digest = None
            self.expected_application_binding_digest = None
            self.expected_cleanup_input_digest = None
            self.expected_cleanup_application_binding_digest = None
            return False
        base_digest = _snapshot_base_digest(snapshot)
        if base_digest is None or base_digest != self.manual_snapshot_base_digest:
            self.manual_snapshot_known = False
            self.unavailable_reason = "manual_snapshot_base_changed"
            self.lifecycle_epoch += 1
            self.request_ticket += 1
            self.current_context = None
            self.expected_transition_input_digest = None
            self.expected_application_binding_digest = None
            self.expected_cleanup_input_digest = None
            self.expected_cleanup_application_binding_digest = None
            return False
        if not self.manual_snapshot_known or self.manual_snapshot is None:
            if snapshot == self.manual_snapshot and self.manual_revision is not None:
                self.manual_snapshot_known = True
                self.unavailable_reason = None
                self.lifecycle_epoch += 1
                self.request_ticket += 1
                self.current_context = None
                self.expected_transition_input_digest = None
                self.expected_application_binding_digest = None
                self.expected_cleanup_input_digest = None
                self.expected_cleanup_application_binding_digest = None
                return True
            self.unavailable_reason = "manual_snapshot_change_unobserved"
            self.lifecycle_epoch += 1
            self.request_ticket += 1
            self.current_context = None
            self.expected_transition_input_digest = None
            self.expected_application_binding_digest = None
            self.expected_cleanup_input_digest = None
            self.expected_cleanup_application_binding_digest = None
            return False
        if snapshot == self.manual_snapshot:
            return True
        if self.manual_revision is None:
            self.unavailable_reason = "manual_revision_unavailable"
            self.manual_snapshot_known = False
            self.lifecycle_epoch += 1
            self.request_ticket += 1
            self.current_context = None
            self.expected_transition_input_digest = None
            self.expected_application_binding_digest = None
            self.expected_cleanup_input_digest = None
            self.expected_cleanup_application_binding_digest = None
            return False
        self.manual_revision += 1
        self.manual_snapshot = snapshot
        self.lifecycle_epoch += 1
        self.request_ticket += 1
        self.current_context = None
        self.expected_transition_input_digest = None
        self.expected_application_binding_digest = None
        self.expected_cleanup_input_digest = None
        self.expected_cleanup_application_binding_digest = None
        self.unavailable_reason = None
        return True

    def invalidate(self, *, reason: str = "input_invalidated") -> None:
        _require_non_empty_text(reason, "reason")
        self.accepted_origin = None
        self.pending_origin = None
        self.manual_revision = None
        self.manual_snapshot = None
        self.manual_snapshot_known = False
        self.manual_snapshot_base_digest = None
        self.current_context = None
        self.expected_transition_input_digest = None
        self.expected_application_binding_digest = None
        self.expected_cleanup_input_digest = None
        self.expected_cleanup_application_binding_digest = None
        self.unavailable_reason = reason
        self.lifecycle_epoch += 1
        self.request_ticket += 1

    def reset(self) -> None:
        self.invalidate(reason="workspace_reset")

    def next_request_ticket(self) -> tuple[int, int]:
        self.request_ticket += 1
        self.current_context = None
        self.expected_transition_input_digest = None
        self.expected_application_binding_digest = None
        self.expected_cleanup_input_digest = None
        self.expected_cleanup_application_binding_digest = None
        return self.request_ticket, self.lifecycle_epoch

    def invalidate_context(self) -> None:
        self.lifecycle_epoch += 1
        self.request_ticket += 1
        self.current_context = None
        self.expected_transition_input_digest = None
        self.expected_application_binding_digest = None
        self.expected_cleanup_input_digest = None
        self.expected_cleanup_application_binding_digest = None

    def apply_context(
        self,
        context: object,
        *,
        ticket: int,
        epoch: int,
        expected_transition_input_digest: str | None = None,
        expected_application_binding_digest: str | None = None,
        expected_cleanup_input_digest: str | None = None,
        expected_cleanup_application_binding_digest: str | None = None,
    ) -> bool:
        if not self.is_current_request(ticket, epoch) or not self.is_accepted:
            return False
        identity = getattr(context, "input_identity", None)
        actual_transition_digest = getattr(
            identity, "transition_input_digest", None
        )
        actual_application_digest = getattr(
            identity, "application_binding_digest", None
        )
        actual_cleanup_digest = getattr(identity, "cleanup_input_digest", None)
        actual_cleanup_application_digest = getattr(
            identity, "cleanup_application_binding_digest", None
        )
        if actual_transition_digest != expected_transition_input_digest:
            return False
        if actual_application_digest != expected_application_binding_digest:
            return False
        if actual_cleanup_digest != expected_cleanup_input_digest:
            return False
        if actual_cleanup_application_digest != expected_cleanup_application_binding_digest:
            return False
        if (
            getattr(context, "ticket", None) != ticket
            or getattr(context, "lifecycle_epoch", None) != epoch
            or getattr(identity, "source_run_id", None)
            != self.accepted_origin.source_run_id
            or getattr(identity, "job_id", None) != self.accepted_origin.job_id
            or getattr(identity, "analysis_generation", None)
            != self.accepted_origin.analysis_generation
            or getattr(identity, "input_mode", None) != self.accepted_origin.input_mode
            or getattr(identity, "input_binding_digest", None)
            != self.accepted_origin.input_binding_digest
            or getattr(identity, "source_audio_path", None)
            != self.accepted_origin.source_audio_path
            or getattr(identity, "analysis_wav_path", None)
            != self.accepted_origin.analysis_wav_path
            or getattr(identity, "normalized_text_path", None)
            != self.accepted_origin.text_path
            or getattr(identity, "manual_revision", None) != self.manual_revision
            or getattr(identity, "base_plan_digest", None)
            != self.manual_snapshot_base_digest
        ):
            return False
        self.current_context = context
        self.expected_transition_input_digest = expected_transition_input_digest
        self.expected_application_binding_digest = expected_application_binding_digest
        self.expected_cleanup_input_digest = expected_cleanup_input_digest
        self.expected_cleanup_application_binding_digest = (
            expected_cleanup_application_binding_digest
        )
        return True

    def is_current_request(self, ticket: int, epoch: int) -> bool:
        return (
            isinstance(ticket, int)
            and not isinstance(ticket, bool)
            and isinstance(epoch, int)
            and not isinstance(epoch, bool)
            and ticket == self.request_ticket
            and epoch == self.lifecycle_epoch
        )

    @property
    def is_accepted(self) -> bool:
        return (
            self.accepted_origin is not None
            and self.manual_snapshot_known
            and self.manual_revision is not None
            and self.manual_snapshot is not None
            and self.unavailable_reason is None
        )


__all__ = ["FinalOutputOrigin", "FinalOutputState"]
