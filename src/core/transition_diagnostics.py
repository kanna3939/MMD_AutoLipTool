"""Immutable pair summaries shared by MS32 diagnostics and reports."""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass
from typing import Any


def _digest(payload: object) -> str:
    encoded = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _finite(value: object, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{name} must be finite")
    result = float(value)
    if not math.isfinite(result):
        raise ValueError(f"{name} must be finite")
    return result


@dataclass(frozen=True, slots=True)
class TransitionPairDiagnostic:
    previous_event_index: int
    next_event_index: int
    previous_morph: str
    next_morph: str
    state: str
    reason: str | None
    baseline_start_frame: int
    candidate_start_frame: int
    start_advance_frames: int
    baseline_overlap_width_frames: float
    candidate_overlap_width_frames: float
    overlap_width_delta_frames: float
    baseline_positive_integer_frame_count: int
    candidate_positive_integer_frame_count: int
    positive_integer_frame_count_delta: int
    local_peak_ratio: float | None

    def __post_init__(self) -> None:
        for name in (
            "previous_event_index",
            "next_event_index",
            "baseline_start_frame",
            "candidate_start_frame",
            "start_advance_frames",
            "baseline_positive_integer_frame_count",
            "candidate_positive_integer_frame_count",
        ):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, int) or value < 0:
                raise ValueError(f"{name} must be a non-negative integer")
        for name in ("previous_morph", "next_morph"):
            value = getattr(self, name)
            if type(value) is not str or not value:
                raise ValueError(f"{name} must be non-empty text")
        if self.state not in {"applied", "not_applicable"}:
            raise ValueError("transition pair state is invalid")
        if self.reason is not None and (type(self.reason) is not str or not self.reason):
            raise ValueError("transition pair reason must be non-empty text or None")
        for name in (
            "baseline_overlap_width_frames",
            "candidate_overlap_width_frames",
            "overlap_width_delta_frames",
        ):
            object.__setattr__(self, name, _finite(getattr(self, name), name))
        if isinstance(self.positive_integer_frame_count_delta, bool) or not isinstance(
            self.positive_integer_frame_count_delta, int
        ):
            raise ValueError("positive_integer_frame_count_delta must be an integer")
        if self.local_peak_ratio is not None:
            object.__setattr__(
                self,
                "local_peak_ratio",
                _finite(self.local_peak_ratio, "local_peak_ratio"),
            )

    def canonical_payload(self) -> dict[str, Any]:
        return {
            "previous_event_index": self.previous_event_index,
            "next_event_index": self.next_event_index,
            "previous_morph": self.previous_morph,
            "next_morph": self.next_morph,
            "state": self.state,
            "reason": self.reason,
            "baseline_start_frame": self.baseline_start_frame,
            "candidate_start_frame": self.candidate_start_frame,
            "start_advance_frames": self.start_advance_frames,
            "baseline_overlap_width_frames": self.baseline_overlap_width_frames.hex(),
            "candidate_overlap_width_frames": self.candidate_overlap_width_frames.hex(),
            "overlap_width_delta_frames": self.overlap_width_delta_frames.hex(),
            "baseline_positive_integer_frame_count": self.baseline_positive_integer_frame_count,
            "candidate_positive_integer_frame_count": self.candidate_positive_integer_frame_count,
            "positive_integer_frame_count_delta": self.positive_integer_frame_count_delta,
            "local_peak_ratio": (
                None if self.local_peak_ratio is None else self.local_peak_ratio.hex()
            ),
        }


@dataclass(frozen=True, slots=True)
class TransitionDiagnosticSummary:
    input_digest: str
    policy_digest: str
    acoustic_digest: str
    outer_plan_schema_id: str
    outer_semantic_digest: str
    outer_wire_digest: str
    pairs: tuple[TransitionPairDiagnostic, ...]
    schema_id: str = "ms32-transition-diagnostic-summary/v1"

    def __post_init__(self) -> None:
        for name in (
            "input_digest",
            "policy_digest",
            "acoustic_digest",
            "outer_semantic_digest",
            "outer_wire_digest",
        ):
            value = getattr(self, name)
            if (
                type(value) is not str
                or len(value) != 64
                or any(character not in "0123456789abcdef" for character in value)
            ):
                raise ValueError(f"{name} must be lowercase SHA-256")
        if type(self.outer_plan_schema_id) is not str or not self.outer_plan_schema_id:
            raise ValueError("outer_plan_schema_id must be non-empty text")
        if self.schema_id != "ms32-transition-diagnostic-summary/v1":
            raise ValueError("transition diagnostic summary schema is unsupported")
        object.__setattr__(self, "pairs", tuple(self.pairs))
        if any(not isinstance(item, TransitionPairDiagnostic) for item in self.pairs):
            raise ValueError("transition diagnostic pairs must be typed immutable records")

    def canonical_payload(self) -> dict[str, Any]:
        return {
            "schema_id": self.schema_id,
            "input_digest": self.input_digest,
            "policy_digest": self.policy_digest,
            "acoustic_digest": self.acoustic_digest,
            "outer_plan_schema_id": self.outer_plan_schema_id,
            "outer_semantic_digest": self.outer_semantic_digest,
            "outer_wire_digest": self.outer_wire_digest,
            "pairs": [item.canonical_payload() for item in self.pairs],
        }

    @property
    def summary_digest(self) -> str:
        return _digest(self.canonical_payload())

    def to_dict(self) -> dict[str, Any]:
        return {**self.canonical_payload(), "summary_digest": self.summary_digest}


def build_transition_diagnostic_summary(
    binding: object,
    final_identity: object,
) -> TransitionDiagnosticSummary:
    """Project the already validated B2 pair records without re-evaluating them."""
    input_snapshot = getattr(binding, "input_snapshot", None)
    resolution = getattr(binding, "resolution", None)
    issuer_context = getattr(binding, "issuer_context", None)
    plan = getattr(binding, "plan", None)
    if any(item is None for item in (input_snapshot, resolution, issuer_context, plan)):
        raise ValueError("validated transition binding is incomplete")
    pairs = tuple(getattr(issuer_context, "pairs", ()))
    decisions = tuple(getattr(resolution, "decisions", ()))
    if len(pairs) != len(decisions):
        raise ValueError("transition pair and decision counts differ")
    records: list[TransitionPairDiagnostic] = []
    for pair, decision in zip(pairs, decisions, strict=True):
        if (
            pair.previous_event_index != decision.previous_event_index
            or pair.next_event_index != decision.next_event_index
            or pair.previous_morph != decision.previous_morph
            or pair.next_morph != decision.next_morph
        ):
            raise ValueError("transition summary differs from the validated pair order")
        records.append(
            TransitionPairDiagnostic(
                previous_event_index=decision.previous_event_index,
                next_event_index=decision.next_event_index,
                previous_morph=decision.previous_morph,
                next_morph=decision.next_morph,
                state=decision.state,
                reason=decision.reason,
                baseline_start_frame=decision.baseline_start_frame,
                candidate_start_frame=decision.candidate_start_frame,
                start_advance_frames=decision.start_advance_frames,
                baseline_overlap_width_frames=decision.baseline_overlap_width_frames,
                candidate_overlap_width_frames=decision.candidate_overlap_width_frames,
                overlap_width_delta_frames=decision.overlap_width_delta_frames,
                baseline_positive_integer_frame_count=len(
                    decision.baseline_positive_integer_frames
                ),
                candidate_positive_integer_frame_count=len(
                    decision.candidate_positive_integer_frames
                ),
                positive_integer_frame_count_delta=(
                    len(decision.candidate_positive_integer_frames)
                    - len(decision.baseline_positive_integer_frames)
                ),
                local_peak_ratio=decision.local_peak_ratio,
            )
        )
    identity_context = getattr(plan, "identity_context", None)
    if identity_context is None:
        raise ValueError("validated transition outer identity is missing")
    result = TransitionDiagnosticSummary(
        input_digest=input_snapshot.input_digest,
        policy_digest=input_snapshot.policy.policy_digest,
        acoustic_digest=input_snapshot.acoustic.content_digest,
        outer_plan_schema_id=plan.schema_id,
        outer_semantic_digest=plan.semantic_digest,
        outer_wire_digest=getattr(final_identity, "wire_digest", ""),
        pairs=tuple(records),
    )
    if (
        getattr(final_identity, "semantic_digest", None) != plan.semantic_digest
        or getattr(final_identity, "plan_schema_id", None) != plan.schema_id
        or getattr(final_identity, "input_identity", None).transition_input_digest
        != input_snapshot.input_digest
    ):
        raise ValueError("transition summary does not match the shared outer identity")
    return result


__all__ = [
    "TransitionDiagnosticSummary",
    "TransitionPairDiagnostic",
    "build_transition_diagnostic_summary",
]
