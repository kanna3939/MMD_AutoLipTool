"""Immutable, conservative MS33-B5 cleanup default policy.

The runtime binding is built from literals and accepted digests.  It does not
read B4 research files, comparison manifests, or temporary run directories.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Iterable

from src.core.final_morph_key_reduction_plan import (
    KeyReductionPolicy,
    ReductionPoint,
)


DEFAULT_CLEANUP_APPLICATION_CONTRACT_ID = "ms33-default-cleanup/v1"
ADOPTION_SCHEMA_ID = "ms33-cleanup-adoption/v1"
B4_ADOPTION_EVIDENCE_SCHEMA_ID = "ms33-b4-adoption-evidence/v1"
B3_KEY_POLICY_ID = "ms33-b3-key-contract/v1"
B3_KEY_CONTRACT_DIGEST = "46fa6e737b0db0f16cb02155c71ba97ff4b03b25b915cdb03b799b5023c88b84"
B3_KEY_POLICY_DIGEST = "39340b8671f60a6b0ab07d93116e33d70b86e029aa6253656615984a4ecbfc4d"
B3_AUDIT_SHA256 = "49173b67b4ba7d6f2df1853b03f5c4e6608abd930244fa2c75b9d629cd939521"
B4_HISTORICAL_AUDIT_PATH = (
    r"C:\tmp\MMD_AutoLipTool\ms33-b4\run-20261026T1434-main-call\audit.json"
)
HISTORICAL_B4_AUDIT_SHA256 = "24dfc2f6a58d90c2d2a0c07b647e82b10640d14db6fd86bbf0ba91b1f1a411a1"
CURRENT_G33_04_DISPOSITION_SHA256 = "d39d13c16e1232130e005b44705d7495cc6702c3d97e02f1f2f418fb131ba38c"
B4_COMPARISON_SHA256 = "e7aa17119790f58770ba8ea1861be5cbdc7315203e3b90deee7efda4a4986c20"
B4_TECHNICAL_REPORT_SHA256 = "e11ba7888fd70058a85605e3e93fa0c37800c73c3b2188e854fbcaf41a1f4819"
B4_TEST_SUMMARY_SHA256 = "075a2c4cbbec0829a022045c18a345fd5f4059251ec774a86eafaa7e92b35921"
B4C_REVIEWED_CANDIDATE_VMD_SHA256 = "245c140ac7dae4eef9a3ba1e2a5d151b52e131b75801c9995219160410e0f94e"
B4C_REVIEWED_CANDIDATE_WAV_SHA256 = "16da37e77836d5e2c4e65931ee36cc846894f710190e0e2b2095fe9a55968d72"
ADOPTED_INPUT_MODES = ("text_audio", "voice_only")
ADOPTED_VARIANT = "keys_only"
ADOPTED_EVENT_COMPONENT = "not_applicable"
ADOPTED_KEY_COMPONENT = "adopted"
ADOPTED_LIMITATIONS = (
    "B1 00-VO 39 unresolved shapes remain outside the reduction proof.",
    "B1 00-VO one protected exception remains preserved.",
    "The frame 360 area remains an inherited hold.",
    "The B4C 00-VO candidate is review-only and excluded from normal default.",
    "Exact curve preservation does not claim a visual quality improvement.",
)


_KEY_PROTECTIONS = (
    {
        "kind": "boundary",
        "reason": "Inventory-backed protected exemplar; B3 must preserve this source reason.",
        "record_ids": ["ms33-b1-00-ta:shape:0:point:0"],
        "status": "preserved",
    },
    {
        "kind": "crossfade",
        "reason": "固定8ケースのinventoryに該当する由来付きrecordはありません。保護規則自体は合成fixtureで検証します。",
        "record_ids": [],
        "status": "no_in_scope_examples",
    },
    {
        "kind": "long_vowel",
        "reason": "Inventory-backed protected exemplar; B3 must preserve this source reason.",
        "record_ids": ["ms33-b1-00-ta:event:5"],
        "status": "preserved",
    },
    {
        "kind": "manual",
        "reason": "固定8ケースのinventoryに該当する由来付きrecordはありません。保護規則自体は合成fixtureで検証します。",
        "record_ids": [],
        "status": "no_in_scope_examples",
    },
    {
        "kind": "required_zero",
        "reason": "Inventory-backed protected exemplar; B3 must preserve this source reason.",
        "record_ids": ["ms33-b1-00-ta:event:16"],
        "status": "preserved",
    },
    {
        "kind": "short_vowel",
        "reason": "Inventory-backed protected exemplar; B3 must preserve this source reason.",
        "record_ids": ["ms33-b1-00-ta:event:49"],
        "status": "preserved",
    },
    {
        "kind": "unknown",
        "reason": "Inventory-backed protected exemplar; B3 must preserve this source reason.",
        "record_ids": ["ms33-b1-00-ta:final:23:27:お"],
        "status": "preserved",
    },
    {
        "kind": "valid_low",
        "reason": "固定8ケースのinventoryに該当する由来付きrecordはありません。保護規則自体は合成fixtureで検証します。",
        "record_ids": [],
        "status": "no_in_scope_examples",
    },
)
def _canonical_json(value: object) -> bytes:
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False
    ).encode("utf-8")


def _digest(value: object) -> str:
    return hashlib.sha256(_canonical_json(value)).hexdigest()


def _require_sha256(value: object, name: str) -> str:
    if (
        type(value) is not str
        or len(value) != 64
        or any(character not in "0123456789abcdef" for character in value)
    ):
        raise ValueError(f"{name} must be lowercase SHA-256")
    return value


def build_adopted_key_policy() -> KeyReductionPolicy:
    """Build exactly the B3 adopted policy without reading its research files."""
    return KeyReductionPolicy(
        policy_id=B3_KEY_POLICY_ID,
        key_contract_digest=B3_KEY_CONTRACT_DIGEST,
        protections=tuple(dict(row) for row in _KEY_PROTECTIONS),
        curve_domains=("canonical_binary64", "saved_binary32"),
        algorithm_id="exact-collinear-stack/v1",
        enabled=True,
        policy_digest=B3_KEY_POLICY_DIGEST,
    )


def adoption_record_payload() -> dict[str, object]:
    """Return the frozen adoption record used to derive the runtime digest."""
    b4_evidence = {
        "schema_id": B4_ADOPTION_EVIDENCE_SCHEMA_ID,
        "current_g33_04_disposition": "established",
        "disposition_source": "docs/Implementation_Plan/MS33-B4_Implementation_Plan.md#15.11",
        "historical_b4_audit": {
            "path": B4_HISTORICAL_AUDIT_PATH,
            "sha256": HISTORICAL_B4_AUDIT_SHA256,
            "relation": "historical_pre_disposition_snapshot",
            "recorded_g33_04": "not_established",
            "recorded_exit_code": 2,
        },
        "current_g33_04_disposition_sha256": CURRENT_G33_04_DISPOSITION_SHA256,
        "technical_report_sha256": B4_TECHNICAL_REPORT_SHA256,
        "comparison_sha256": B4_COMPARISON_SHA256,
        "test_summary_sha256": B4_TEST_SUMMARY_SHA256,
        "b3_audit_sha256": B3_AUDIT_SHA256,
        "b4c_candidate_disposition": {
            "state": "review_only",
            "normal_default": "excluded",
            "candidate_vmd_sha256": B4C_REVIEWED_CANDIDATE_VMD_SHA256,
            "paired_wav_sha256": B4C_REVIEWED_CANDIDATE_WAV_SHA256,
        },
        "user_disposition": "GUI01-GUI06 and TA/VO live checks passed; user reported quality sufficient.",
    }
    return {
        "schema_id": ADOPTION_SCHEMA_ID,
        "b4_adoption_evidence_digest": _digest(b4_evidence),
        "historical_b4_audit_sha256": HISTORICAL_B4_AUDIT_SHA256,
        "current_g33_04_disposition_sha256": CURRENT_G33_04_DISPOSITION_SHA256,
        "current_g33_04_disposition": "established",
        "event_component": ADOPTED_EVENT_COMPONENT,
        "key_component": ADOPTED_KEY_COMPONENT,
        "adopted_variant": ADOPTED_VARIANT,
        "key_policy": build_adopted_key_policy().to_dict(),
        "runtime_scope": list(ADOPTED_INPUT_MODES),
        "protections": [dict(row) for row in _KEY_PROTECTIONS],
        "limitations": list(ADOPTED_LIMITATIONS),
        "b4c_candidate_disposition": "review_only_excluded_from_normal_default",
    }


@dataclass(frozen=True, slots=True)
class AdoptedCleanupBinding:
    application_contract_id: str
    event_component: str
    key_component: str
    key_policy: KeyReductionPolicy
    adoption_schema_id: str
    adoption_record_sha256: str
    b4_adoption_evidence_sha256: str
    historical_b4_audit_path: str
    historical_b4_audit_sha256: str
    historical_b4_audit_relation: str
    current_g33_04_disposition_sha256: str
    comparison_sha256: str
    technical_report_sha256: str
    test_summary_sha256: str
    component_evidence_digest: str
    runtime_scope: tuple[str, ...]
    limitations: tuple[str, ...]

    def __post_init__(self) -> None:
        if self.application_contract_id != DEFAULT_CLEANUP_APPLICATION_CONTRACT_ID:
            raise ValueError("application contract differs from the adopted MS33 default")
        if self.event_component != ADOPTED_EVENT_COMPONENT:
            raise ValueError("event component must remain not_applicable")
        if self.key_component != ADOPTED_KEY_COMPONENT:
            raise ValueError("key component differs from the accepted B3 reduction")
        if not isinstance(self.key_policy, KeyReductionPolicy):
            raise ValueError("adopted key policy must be typed")
        self.key_policy.validate_integrity()
        if (
            self.key_policy.policy_id != B3_KEY_POLICY_ID
            or self.key_policy.policy_digest != B3_KEY_POLICY_DIGEST
            or self.key_policy.algorithm_id != "exact-collinear-stack/v1"
            or self.key_policy.curve_domains != ("canonical_binary64", "saved_binary32")
        ):
            raise ValueError("adopted key policy differs from the accepted B3 contract")
        if self.adoption_schema_id != ADOPTION_SCHEMA_ID:
            raise ValueError("adoption schema is unsupported")
        for name in (
            "adoption_record_sha256", "b4_adoption_evidence_sha256",
            "historical_b4_audit_sha256", "current_g33_04_disposition_sha256",
            "comparison_sha256",
            "technical_report_sha256", "test_summary_sha256",
            "component_evidence_digest",
        ):
            _require_sha256(getattr(self, name), name)
        if self.historical_b4_audit_path != B4_HISTORICAL_AUDIT_PATH:
            raise ValueError("historical B4 audit path differs from the recorded snapshot")
        if self.historical_b4_audit_sha256 != HISTORICAL_B4_AUDIT_SHA256:
            raise ValueError("historical B4 audit hash differs from the recorded snapshot")
        if self.historical_b4_audit_relation != "historical_pre_disposition_snapshot":
            raise ValueError("historical B4 audit relation is invalid")
        if self.current_g33_04_disposition_sha256 != CURRENT_G33_04_DISPOSITION_SHA256:
            raise ValueError("current G33-04 disposition hash differs from the accepted document")
        if self.runtime_scope != ADOPTED_INPUT_MODES:
            raise ValueError("runtime scope differs from the accepted input modes")
        if self.limitations != ADOPTED_LIMITATIONS:
            raise ValueError("adopted limitations differ from the evidence record")
        evidence = _digest({
            "b3_audit_sha256": B3_AUDIT_SHA256,
            "historical_b4_audit_sha256": self.historical_b4_audit_sha256,
            "current_g33_04_disposition_sha256": self.current_g33_04_disposition_sha256,
            "comparison_sha256": self.comparison_sha256,
            "technical_report_sha256": self.technical_report_sha256,
            "test_summary_sha256": self.test_summary_sha256,
            "b4_adoption_evidence_sha256": self.b4_adoption_evidence_sha256,
        })
        if evidence != self.component_evidence_digest:
            raise ValueError("component evidence digest differs from its references")
        if self.adoption_record_sha256 != _digest(adoption_record_payload()):
            raise ValueError("adoption record digest differs from the frozen literal")

    @property
    def semantic_digest(self) -> str:
        return _digest({
            "application_contract_id": self.application_contract_id,
            "event_component": self.event_component,
            "key_component": self.key_component,
            "key_policy_digest": self.key_policy.policy_digest,
            "adoption_schema_id": self.adoption_schema_id,
            "adoption_record_sha256": self.adoption_record_sha256,
            "b4_adoption_evidence_sha256": self.b4_adoption_evidence_sha256,
            "historical_b4_audit_path": self.historical_b4_audit_path,
            "historical_b4_audit_sha256": self.historical_b4_audit_sha256,
            "historical_b4_audit_relation": self.historical_b4_audit_relation,
            "current_g33_04_disposition_sha256": self.current_g33_04_disposition_sha256,
            "comparison_sha256": self.comparison_sha256,
            "technical_report_sha256": self.technical_report_sha256,
            "test_summary_sha256": self.test_summary_sha256,
            "component_evidence_digest": self.component_evidence_digest,
            "runtime_scope": list(self.runtime_scope),
            "limitations": list(self.limitations),
        })


def build_adopted_cleanup_binding() -> AdoptedCleanupBinding:
    """Create the default binding using source literals only."""
    adoption = adoption_record_payload()
    b4_digest = adoption["b4_adoption_evidence_digest"]
    evidence = _digest({
        "b3_audit_sha256": B3_AUDIT_SHA256,
        "historical_b4_audit_sha256": HISTORICAL_B4_AUDIT_SHA256,
        "current_g33_04_disposition_sha256": CURRENT_G33_04_DISPOSITION_SHA256,
        "comparison_sha256": B4_COMPARISON_SHA256,
        "technical_report_sha256": B4_TECHNICAL_REPORT_SHA256,
        "test_summary_sha256": B4_TEST_SUMMARY_SHA256,
        "b4_adoption_evidence_sha256": b4_digest,
    })
    # The old audit's file digest is kept separate from current disposition.
    # Its status remains a pre-disposition snapshot and is never promoted.
    return AdoptedCleanupBinding(
        application_contract_id=DEFAULT_CLEANUP_APPLICATION_CONTRACT_ID,
        event_component=ADOPTED_EVENT_COMPONENT,
        key_component=ADOPTED_KEY_COMPONENT,
        key_policy=build_adopted_key_policy(),
        adoption_schema_id=ADOPTION_SCHEMA_ID,
        adoption_record_sha256=_digest(adoption),
        b4_adoption_evidence_sha256=b4_digest,
        historical_b4_audit_path=B4_HISTORICAL_AUDIT_PATH,
        historical_b4_audit_sha256=HISTORICAL_B4_AUDIT_SHA256,
        historical_b4_audit_relation="historical_pre_disposition_snapshot",
        current_g33_04_disposition_sha256=CURRENT_G33_04_DISPOSITION_SHA256,
        comparison_sha256=B4_COMPARISON_SHA256,
        technical_report_sha256=B4_TECHNICAL_REPORT_SHA256,
        test_summary_sha256=B4_TEST_SUMMARY_SHA256,
        component_evidence_digest=evidence,
        runtime_scope=ADOPTED_INPUT_MODES,
        limitations=ADOPTED_LIMITATIONS,
    )


@dataclass(frozen=True, slots=True)
class DefaultCleanupSelection:
    binding: AdoptedCleanupBinding
    input_mode: str
    profile_id: str | None
    output_mapping: tuple[tuple[str, str], ...]
    event_state: str
    key_state: str
    selection_kind: str
    reason: str

    def __post_init__(self) -> None:
        if not isinstance(self.binding, AdoptedCleanupBinding):
            raise ValueError("adopted default cleanup binding is invalid")
        if type(self.input_mode) is not str or not self.input_mode:
            raise ValueError("input mode is invalid")
        if self.profile_id is not None and (type(self.profile_id) is not str or not self.profile_id):
            raise ValueError("profile identity is invalid")
        if (
            type(self.output_mapping) is not tuple
            or any(type(row) is not tuple or len(row) != 2 for row in self.output_mapping)
            or tuple(row[0] for row in self.output_mapping) != ("あ", "い", "う", "え", "お")
            or any(type(row[1]) is not str or not row[1] for row in self.output_mapping)
        ):
            raise ValueError("output mapping is invalid")
        if self.event_state != "not_applicable":
            raise ValueError("event component must remain not_applicable")
        if self.selection_kind not in {"cleanup", "scope_excluded", "no_applicable"}:
            raise ValueError("cleanup selection kind is unsupported")
        if self.selection_kind == "cleanup":
            if self.input_mode not in self.binding.runtime_scope or self.key_state != "adopted":
                raise ValueError("cleanup selection is outside the adopted scope")
            if self.reason != "exact_collinear_key_reduction_adopted":
                raise ValueError("cleanup selection reason is invalid")
        elif self.selection_kind == "scope_excluded":
            if self.reason != "input_mode_outside_adopted_scope" or self.key_state != "not_applied":
                raise ValueError("scope-excluded selection is invalid")
        elif self.reason != "no_applicable_cleanup_component" or self.key_state != "not_applicable":
            raise ValueError("no-applicable selection is invalid")

    def canonical_payload(self) -> dict[str, object]:
        return {
            "application_binding_digest": self.binding.semantic_digest,
            "input_mode": self.input_mode,
            "profile_id": self.profile_id,
            "output_mapping": [[semantic, name] for semantic, name in self.output_mapping],
            "event_state": self.event_state,
            "key_state": self.key_state,
            "selection_kind": self.selection_kind,
            "reason": self.reason,
        }

    @property
    def selection_digest(self) -> str:
        return _digest(self.canonical_payload())


def resolve_default_cleanup_selection(
    binding: AdoptedCleanupBinding,
    *,
    input_mode: str,
    profile_id: str | None,
    output_mapping: Iterable[tuple[str, str]],
) -> DefaultCleanupSelection:
    if not isinstance(binding, AdoptedCleanupBinding):
        raise ValueError("adopted default cleanup binding is invalid")
    mapping = tuple(tuple(row) for row in output_mapping)
    if input_mode in binding.runtime_scope:
        return DefaultCleanupSelection(
            binding=binding,
            input_mode=input_mode,
            profile_id=profile_id,
            output_mapping=mapping,
            event_state="not_applicable",
            key_state="adopted",
            selection_kind="cleanup",
            reason="exact_collinear_key_reduction_adopted",
        )
    return DefaultCleanupSelection(
        binding=binding,
        input_mode=input_mode,
        profile_id=profile_id,
        output_mapping=mapping,
        event_state="not_applicable",
        key_state="not_applied",
        selection_kind="scope_excluded",
        reason="input_mode_outside_adopted_scope",
    )


def _kind_tokens(point: ReductionPoint) -> frozenset[str]:
    return frozenset(
        str(value).casefold().replace("-", "_").replace(" ", "_")
        for value in (*point.point_kinds, *point.intent_origins, *point.source_ids, *point.source_record_ids)
    )


def _has_token(tokens: frozenset[str], *needles: str) -> bool:
    return any(any(needle in token for needle in needles) for token in tokens)


def resolve_current_key_protections(
    points: tuple[ReductionPoint, ...],
    requirements: tuple[dict[str, object], ...],
) -> dict[str, object]:
    """Rebuild accepted protection categories from this live source snapshot.

    The B1 contract's case IDs are evidence exemplars, not runtime selectors.
    Current source records and obligations determine every protected key.
    """
    if type(points) is not tuple or any(not isinstance(point, ReductionPoint) for point in points):
        raise ValueError("current reduction points are invalid")
    if type(requirements) is not tuple or any(type(row) is not dict for row in requirements):
        raise ValueError("current upstream requirements are invalid")
    protected: dict[tuple[int, str], set[str]] = {}
    for point in points:
        tokens = _kind_tokens(point)
        kinds: set[str] = set()
        if point.requirement_ids or _has_token(tokens, "required_zero", "closure", "boundary", "terminal", "start_zero", "end_zero"):
            kinds.add("required_zero" if point.requirement_ids else "boundary")
        if any(origin not in {"automatic", "automatic_event"} for origin in point.intent_origins):
            kinds.add("manual")
        if (
            not point.source_ids
            or not point.source_record_ids
            or _has_token(tokens, "unknown", "unresolved", "mixed")
        ):
            kinds.add("unknown")
        if _has_token(tokens, "valid_low", "valid-low", "valid_low_control", "low_value_control", "valley"):
            kinds.add("valid_low")
        if _has_token(tokens, "long_vowel", "long-vowel", "long_vowel_hold", "long_vowel_decay"):
            kinds.add("long_vowel")
        if _has_token(tokens, "crossfade", "manual_crossfade"):
            kinds.add("crossfade")
        if _has_token(tokens, "short_vowel", "short-vowel", "short_pulse", "ms32_short_vowel_rescue"):
            kinds.add("short_vowel")
        for kind in kinds:
            protected.setdefault(point.key, set()).add(f"b1_contract:{kind}")
    rows = [
        {
            "frame_no": point.frame_no,
            "semantic_morph": point.semantic_morph,
            "source_record_ids": list(point.source_record_ids),
            "reasons": sorted(protected[point.key]),
        }
        for point in points if point.key in protected
    ]
    zero_intervals = []
    for row in requirements:
        if row.get("kind") in {"per_morph_closure", "silence_core", "required_zero"}:
            zero_intervals.append({
                "semantic_morph": row.get("semantic_morph"),
                "start_frame": row.get("start_frame"),
                "end_frame": row.get("end_frame"),
                "reason": f"upstream:{row.get('requirement_id', row.get('kind', 'requirement'))}",
            })
    zero_intervals.sort(key=lambda row: (str(row["semantic_morph"]), row["start_frame"], row["end_frame"], row["reason"]))
    return {
        "schema_id": "ms33-b3-protection-binding/v1",
        "protected_keys": rows,
        "required_zero_intervals": zero_intervals,
    }


__all__ = [
    "ADOPTION_SCHEMA_ID",
    "AdoptedCleanupBinding",
    "DefaultCleanupSelection",
    "adoption_record_payload",
    "build_adopted_cleanup_binding",
    "build_adopted_key_policy",
    "resolve_current_key_protections",
    "resolve_default_cleanup_selection",
]
