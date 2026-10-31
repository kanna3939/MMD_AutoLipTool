"""Immutable runtime binding for the MS32-B4B adopted default policy."""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json

from src.core.cross_vowel_transition import (
    B4B_CONTRACT_SHA256,
    TRANSITION_POLICY_V2,
    TransitionPolicySnapshot,
    build_bounded_transition_policy,
)


DEFAULT_APPLICATION_CONTRACT_ID = "ms32-default-application/v1"
ADOPTION_SCHEMA_ID = "ms32-b4b-adoption/v2"
ADOPTED_POLICY_DIGEST = "938ae3d6059619e0af35220e4465fcf93df660cd49d26b45a7a38197fbc9376c"
ADOPTION_RECORD_SHA256 = "3c7323a1487b2babfbd94440ffc07507e90fddd5b62b19d46f2c5e5cd433c515"
COMPARISON_SHA256 = "5bd7959d687746e3c37eb642b148af1ea0bcbad441890d3607c40fa2fdabb6ae"
USER_REPORT_SHA256 = "ca206834e33c1b30ffbaa1a381905df90ed75c395b5e6bffc4589c363ee0fee0"
ADOPTED_INPUT_MODES = ("text_audio", "voice_only")
ADOPTED_LIMITATIONS = (
    ("ms31-b1-00-vo", 39, "overlap_limit_unresolved"),
    ("ms31-b1-00-vo", 1, "protected_overlap_exemption"),
)


def _digest(payload: object) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _require_sha256(value: object, name: str) -> str:
    if (
        type(value) is not str
        or len(value) != 64
        or any(character not in "0123456789abcdef" for character in value)
    ):
        raise ValueError(f"{name} must be lowercase SHA-256")
    return value


@dataclass(frozen=True, slots=True)
class AdoptedTransitionBinding:
    application_contract_id: str
    policy: TransitionPolicySnapshot
    b4b_contract_sha256: str
    adoption_schema_id: str
    adoption_record_sha256: str
    comparison_sha256: str
    user_report_sha256: str
    runtime_scope: tuple[str, ...]
    limitations: tuple[tuple[str, int, str], ...]

    def __post_init__(self) -> None:
        if self.application_contract_id != DEFAULT_APPLICATION_CONTRACT_ID:
            raise ValueError("application contract is not the adopted MS32 default")
        if not isinstance(self.policy, TransitionPolicySnapshot):
            raise ValueError("adopted policy must be a typed transition policy")
        if self.policy.policy_id != TRANSITION_POLICY_V2:
            raise ValueError("adopted policy must use the B4B v2 contract")
        if self.policy.policy_digest != ADOPTED_POLICY_DIGEST:
            raise ValueError("adopted policy differs from the accepted B4B policy")
        if self.b4b_contract_sha256 != B4B_CONTRACT_SHA256:
            raise ValueError("B4B contract digest differs from the adopted policy")
        if self.adoption_schema_id != ADOPTION_SCHEMA_ID:
            raise ValueError("adoption schema is unsupported")
        for name in (
            "b4b_contract_sha256",
            "adoption_record_sha256",
            "comparison_sha256",
            "user_report_sha256",
        ):
            _require_sha256(getattr(self, name), name)
        if self.runtime_scope != ADOPTED_INPUT_MODES:
            raise ValueError("runtime scope differs from the accepted B4B scope")
        if self.limitations != ADOPTED_LIMITATIONS:
            raise ValueError("quality limitations differ from the accepted B4B record")

    def canonical_payload(self) -> dict[str, object]:
        return {
            "application_contract_id": self.application_contract_id,
            "policy_digest": self.policy.policy_digest,
            "b4b_contract_sha256": self.b4b_contract_sha256,
            "adoption_schema_id": self.adoption_schema_id,
            "adoption_record_sha256": self.adoption_record_sha256,
            "comparison_sha256": self.comparison_sha256,
            "user_report_sha256": self.user_report_sha256,
            "runtime_scope": self.runtime_scope,
            "limitations": self.limitations,
        }

    @property
    def semantic_digest(self) -> str:
        return _digest(self.canonical_payload())


@dataclass(frozen=True, slots=True)
class DefaultTransitionSelection:
    binding: AdoptedTransitionBinding
    input_mode: str
    selection_kind: str
    reason: str

    def __post_init__(self) -> None:
        if not isinstance(self.binding, AdoptedTransitionBinding):
            raise ValueError("adopted default binding is invalid")
        if self.input_mode not in {"text_audio", "voice_only"}:
            raise ValueError("input mode is unsupported")
        if self.selection_kind not in {"transition", "scope_excluded"}:
            raise ValueError("default selection kind is unsupported")
        if self.selection_kind == "transition":
            if self.input_mode not in self.binding.runtime_scope or self.reason != "adopted_scope":
                raise ValueError("transition selection is outside the adopted scope")
        elif self.reason != "input_mode_outside_adopted_scope":
            raise ValueError("scope-excluded selection reason is invalid")

    def canonical_payload(self) -> dict[str, object]:
        return {
            "application_binding_digest": self.binding.semantic_digest,
            "input_mode": self.input_mode,
            "selection_kind": self.selection_kind,
            "reason": self.reason,
        }

    @property
    def selection_digest(self) -> str:
        return _digest(self.canonical_payload())


def build_adopted_transition_binding() -> AdoptedTransitionBinding:
    """Build the accepted runtime binding without reading evidence files."""
    return AdoptedTransitionBinding(
        application_contract_id=DEFAULT_APPLICATION_CONTRACT_ID,
        policy=build_bounded_transition_policy(),
        b4b_contract_sha256=B4B_CONTRACT_SHA256,
        adoption_schema_id=ADOPTION_SCHEMA_ID,
        adoption_record_sha256=ADOPTION_RECORD_SHA256,
        comparison_sha256=COMPARISON_SHA256,
        user_report_sha256=USER_REPORT_SHA256,
        runtime_scope=ADOPTED_INPUT_MODES,
        limitations=ADOPTED_LIMITATIONS,
    )


def resolve_default_transition_selection(
    binding: AdoptedTransitionBinding,
    input_mode: str,
) -> DefaultTransitionSelection:
    if not isinstance(binding, AdoptedTransitionBinding):
        raise ValueError("adopted default binding is invalid")
    if input_mode in binding.runtime_scope:
        return DefaultTransitionSelection(binding, input_mode, "transition", "adopted_scope")
    return DefaultTransitionSelection(
        binding,
        input_mode,
        "scope_excluded",
        "input_mode_outside_adopted_scope",
    )


__all__ = [
    "ADOPTED_INPUT_MODES",
    "ADOPTED_POLICY_DIGEST",
    "DEFAULT_APPLICATION_CONTRACT_ID",
    "AdoptedTransitionBinding",
    "DefaultTransitionSelection",
    "build_adopted_transition_binding",
    "resolve_default_transition_selection",
]
