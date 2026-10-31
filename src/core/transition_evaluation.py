"""Explicit request contract for MS32 transition candidate evaluation."""

from __future__ import annotations

from dataclasses import dataclass

from src.core.cross_vowel_transition import (
    B1_CONTRACT_SHA256,
    B4B_CONTRACT_SHA256,
    TRANSITION_POLICY_V2,
    TransitionPolicySnapshot,
)


def _require_digest(value: object, name: str) -> str:
    if (
        type(value) is not str
        or len(value) != 64
        or any(character not in "0123456789abcdef" for character in value)
    ):
        raise ValueError(f"{name} must be lowercase SHA-256")
    return value


@dataclass(frozen=True, slots=True)
class TransitionEvaluationRequest:
    """One opt-in evaluation session; no process-wide or saved setting."""

    policy: TransitionPolicySnapshot
    evaluation_session_id: str
    input_manifest_sha256: str
    b1_contract_sha256: str = B1_CONTRACT_SHA256

    def __post_init__(self) -> None:
        if not isinstance(self.policy, TransitionPolicySnapshot):
            raise ValueError("policy must be a typed TransitionPolicySnapshot")
        if type(self.evaluation_session_id) is not str or not self.evaluation_session_id:
            raise ValueError("evaluation_session_id must be non-empty text")
        _require_digest(self.input_manifest_sha256, "input_manifest_sha256")
        _require_digest(self.b1_contract_sha256, "b1_contract_sha256")
        if self.b1_contract_sha256 != (B4B_CONTRACT_SHA256 if self.policy.policy_id == TRANSITION_POLICY_V2 else B1_CONTRACT_SHA256):
            raise ValueError("evaluation request is not bound to the adopted B1 contract")
        if self.policy.b1_contract_sha256 != self.b1_contract_sha256:
            raise ValueError("evaluation policy and request B1 contract differ")
        if self.policy.scope != "adopted_for_core_evaluation":
            raise ValueError("evaluation policy is not adopted for core evaluation")


__all__ = ["TransitionEvaluationRequest"]
